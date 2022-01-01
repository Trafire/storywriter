import torch
from transformers import GPTJForCausalLM, AutoTokenizer


def total_words(prompt):
    return prompt.count(" ")


def find_nth(s, x, n):
    i = -1
    for _ in range(n):
        i = s.find(x, i + len(x))
        if i == -1:
            break
    return i


def get_last_n_words(prompt, n):
    total_words = prompt.count(" ")
    target_index = total_words - n
    if target_index < 1:
        return prompt
    index = find_nth(prompt, ' ', target_index)
    return prompt[index:]


class TextWriter:
    MAX_SIZE = 1100
    MAX_ADDITIONAL = int(MAX_SIZE * .4)
    MAX_PROMPT = int(MAX_SIZE * .6)

    def __init__(self, path):
        self.path = path
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = self._get_model()
        self._model.to(self._device)
        self._tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")


    def _get_model(self):
        return GPTJForCausalLM.from_pretrained(self.path, low_cpu_mem_usage=True)

    def generate(self, prompt, additional):
        # prompt can only be 60% of the total length of the
        input_ids, new_prompt, input_length = self.get_input_ids(prompt, self.MAX_PROMPT)
        generated_ids = self._model.generate(input_ids, do_sample=True, temperature=0.9,
                                             max_length=input_length + additional)
        text = self._tokenizer.decode(generated_ids[0])
        return prompt + text[len(new_prompt):]

    # def generate_text(self, prompt, max_length=200, temperture=0.9):
    #     input_ids = self._tokenizer(prompt, return_tensors="pt").input_ids.to(self._device)
    #     generated_ids = self._model.generate(input_ids, do_sample=True, temperature=temperture, max_length=max_length)
    #     generated_text = self._tokenizer.decode(generated_ids[0])
    #     return generated_text

    def generate_story(self, prompt, additional):
        while additional > self.MAX_ADDITIONAL + 10:
            prompt = self.generate(self._model, additional=self.MAX_ADDITIONAL)
            additional -= self.MAX_ADDITIONAL
        prompt = self.generate(prompt, additional=additional)
        return prompt

    def estimate_input_length(self, prompt):
        return len(prompt) // 4

    def get_input_ids(self, prompt, max_length):
        input_length = self.estimate_input_length(prompt)
        if input_length > max_length:
            disparity = max_length / input_length
            max_words = int(total_words(prompt) * disparity) - 1
            prompt = get_last_n_words(prompt, max_words)
            return self.get_input_ids(prompt, max_length)
        return self._tokenizer(prompt, return_tensors="pt").to(self._device).input_ids, prompt, input_length

if __name__ == '__main__':
    writer = TextWriter('hg')
    print(writer.generate('<cheat> When Rachel', 200))
    print(writer.generate_story('<cheat> When Ellen', 200))

