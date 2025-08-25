import torch
from transformers import BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer, GenerationConfig


class JokeGenerator:
    __model_name = 'google/gemma-3-1b-it'
    __device = 'cuda:0' if torch.cuda.is_available() else 'cpu'

    __system_prompt = {
        "role": "system",
        "content": [{"type": "text",
                     "text": "Output only one short joke in Ukrainian. Do not add any explanations or any other text."}, ]
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
            temperature=0.2,
            top_k=25,
            top_p=1,
            repetition_penalty=1.1,
            eos_token_id=[1, 107],
            do_sample=True,
        )

    def tell_generic_joke(self):
        return self.__infer([
            self.__system_prompt,
            {'role': "user", 'content': f'Розкажи жарт'}
        ])

    def tell_topic_joke(self, topic: str):
        return self.__infer([
            self.__system_prompt,
            {'role': "user", 'content': f'Розкажи жарт на тему {topic}'}
        ])

    def __infer(self, messages):
        input_ids = self.tokenizer.apply_chat_template(
            messages,
            return_tensors='pt',
            add_generation_prompt=True,
            return_dict=True,
            return_full_text=False,
        ).to(self.model.device)

        outputs = self.model.generate(**input_ids, do_sample=False, generation_config=self.generation_params)
        return self.tokenizer.decode(outputs[0][input_ids["input_ids"].shape[-1]:])
