from pydantic import BaseModel
from typing import List

from command import call


class ChatLLM(BaseModel):
    runner: str = '~/llama.cpp/main'
    model: str = '~/models/ggml-vicuna-13b-4bit-rev1.bin'
    temperature: float = 0.0

    def generate(self, prompt: str, stop: List[str] = None):
        
        call(f'{self.runner} -m {self.model} -p "Q: {prompt}\n A: "', stream_output=True)

if __name__ == '__main__':
    llm = ChatLLM()
    llm.generate(prompt='Who is the president of the USA?')