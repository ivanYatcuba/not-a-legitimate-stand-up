import re
import shutil
from unicodedata import normalize

import soundfile as sf
import torch
from ipa_uk import ipa
#from rvc_infer import infer_audio
from styletts2_inference.models import StyleTTS2
from ukrainian_word_stress import Stressifier, StressSymbol


class VoiceActorService:
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'

    def __init__(self):
        self.stressify = Stressifier()
        self.model = StyleTTS2(hf_path='patriotyk/styletts2_ukrainian_multispeaker_hifigan', device=self.device)

    def say_as_yanik(self, text: str, root_dir: str, output_file: str = 'test.wav',
                     model_name: str = 'yanik-selftrained'):
        self.__text_to_speech(text, f"{root_dir}/yanik.pt", output_file)
        self.__convert_speech_to_yanik(output_file, f"{root_dir}/models", model_name)

    def __convert_speech_to_yanik(self, audio_file: str, models_dir: str, model_name: str = "yanik-selftrained"):
        pass
        # result = infer_audio(
        #     f"{models_dir}/{model_name}",
        #     audio_file,
        #     f0_change=0,
        #     f0_method="rmvpe+",
        #     min_pitch="50",
        #     max_pitch="1100",
        #     crepe_hop_length=128,
        #     index_rate=0.75,
        #     filter_radius=3,
        #     rms_mix_rate=0.25,
        #     protect=0,
        #     split_infer=False,
        #     min_silence=500,
        #     silence_threshold=-50,
        #     seek_step=1,
        #     keep_silence=100,
        #     do_formant=False,
        #     quefrency=0,
        #     timbre=1,
        #     f0_autotune=False,
        #     audio_format="wav",
        #     resample_sr=0,
        #     hubert_model_path=f"{models_dir}/hubert_base.pt",
        #     rmvpe_model_path=f"{models_dir}/rmvpe.pt",
        #     fcpe_model_path=f"{models_dir}/fcpe.pt"
        # )

        #shutil.move(result, audio_file)

    def __text_to_speech(self, text: str, style: str, output_file: str = 'test.wav'):
        style = torch.load(style, weights_only=True)
        result_wav = []
        for tokens in self.__tokenize(text):
            wav = self.model(tokens, speed=1, s_prev=style)
            result_wav.append(wav)
        sf.write(output_file, torch.concatenate(result_wav).cpu().numpy(), 24000)

    def __split_to_parts(self, text):
        split_symbols = '.?!:'
        parts = ['']
        index = 0
        for s in text:
            parts[index] += s
            if s in split_symbols and len(parts[index]) > 150:
                index += 1
                parts.append('')
        return parts

    def __tokenize(self, text: str):
        parts = []
        for t in self.__split_to_parts(text):
            print("tokenize text:", t)

            t = t.strip()
            t = t.replace('"', '')
            if not t:
                continue
            t = t.replace('+', StressSymbol.CombiningAcuteAccent)
            t = normalize('NFKC', t)

            t = re.sub(r'[᠆‐‑‒–—―⁻₋−⸺⸻]', '-', t)
            t = re.sub(r' - ', ': ', t)
            ps = ipa(self.stressify(t))
            if not ps:
                raise RuntimeError('No phonetic transcription found for text: ' + t)
            parts.append(self.model.tokenizer.encode(ps))
        return parts
