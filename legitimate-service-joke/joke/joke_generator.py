import uuid

import boto3
import torch
from botocore.exceptions import ClientError
from transformers import BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer, GenerationConfig
from loguru import logger

from joke.speech import VoiceActorService

from env import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET


class JokeGenerator:
    __model_name = 'google/gemma-3-1b-it'
    __device = 'cuda:0' if torch.cuda.is_available() else 'cpu'

    vas = VoiceActorService('/home/ivan/git/not-a-legitimate-stand-up')

    __system_prompt = {
        "role": "system",
        "content": [{"type": "text",
                     "text": "Output ONLY one short joke in Ukrainian. Do NOT add other text."}, ]
    }

    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained(
            self.__model_name,
            torch_dtype=torch.bfloat16,
            quantization_config=BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type='nf4',
                bnb_4bit_compute_dtype=getattr(torch, 'float16'),
                bnb_4bit_use_double_quant=False,
            ),
            attn_implementation='flash_attention_2',
            device_map=self.__device,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.__model_name,
            use_default_system_prompt=False,
            device_map=self.model.device,
        )
        self.generation_params = GenerationConfig(
            max_new_tokens=1024,
            temperature=1.2,
            top_k=25,
            top_p=1,
            repetition_penalty=1.1,
            eos_token_id=[1, 107],
            do_sample=True,
        )

    def tell_generic_joke(self):
        logger.info(f'start generic joke generation')
        return self.__infer([
            self.__system_prompt,
            {'role': "user", 'content': f'Розкажи жарт'}
        ])

    def tell_topic_joke(self, topic: str):
        logger.info(f'start joke generation on topic {topic}')
        return self.__infer([
            self.__system_prompt,
            {'role': "user", 'content': f'Розкажи жарт на тему {topic}'}
        ])

    def __upload_joke(self, file_name, object_name) -> str | None:

        s3_client = boto3.client('s3',
                                 aws_access_key_id=AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        try:
            response = s3_client.upload_file(file_name, AWS_BUCKET, object_name)
            logger.info(response)
            return s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={'Bucket': AWS_BUCKET, 'Key': object_name},
                ExpiresIn=1800
            )
        except ClientError as e:
            logger.error(e)
        return None

    def __infer(self, messages):
        input_ids = self.tokenizer.apply_chat_template(
            messages,
            return_tensors='pt',
            add_generation_prompt=True,
            return_dict=True,
            return_full_text=False,
        ).to(self.model.device)

        outputs = self.model.generate(**input_ids, generation_config=self.generation_params)
        logger.info(f'end joke generation')

        joke = self.tokenizer.decode(outputs[0][input_ids["input_ids"].shape[-1]:])
        logger.info(f'joke: {joke}')

        fname = f'{str(uuid.uuid4())}.wav'
        audio_file = self.vas.say_as_yanik(joke, output_file=f'/tmp/{fname}')

        logger.info(f'joke audio file generated: {audio_file}')

        return self.__upload_joke(audio_file, fname)
