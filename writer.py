import click
import requests as requests
import torch
from random_word import RandomWords
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

    def __init__(self, path, low_mem=True):
        self.low_mem = low_mem
        self.path = path
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = self._get_model()
        self._model.to(self._device)
        self._tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")

    def _get_model(self):
        return GPTJForCausalLM.from_pretrained(self.path, low_cpu_mem_usage=self.low_mem)

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
            prompt = self.generate(prompt, additional=self.MAX_ADDITIONAL)
            additional -= self.MAX_ADDITIONAL
        prompt = self.generate(prompt, additional=additional)
        return prompt

    def estimate_input_length(self, prompt):
        return len(prompt) // 3

    def get_input_ids(self, prompt, max_length):
        input_length = self.estimate_input_length(prompt)
        if input_length > max_length:
            disparity = max_length / input_length
            max_words = int(total_words(prompt) * disparity) - 1
            prompt = get_last_n_words(prompt, max_words)
            return self.get_input_ids(prompt, max_length)
        return self._tokenizer(prompt, return_tensors="pt").to(self._device).input_ids, prompt, input_length

    def generate_new_story(self):
        rw = RandomWords().get_random_word()
        possible = self.generate(f"title: {rw}".title(), 10)
        if "\n" in possible:
            url = 'http://35.223.44.38/story/'
            index = possible.index('\n') + 1
            title = possible[len("title:"): index].strip().title()
            r = requests.post(url, data={"title": title})
            if str(r.status_code)[0] == '2':
                print("New Title Created:", title)
            else:
                print("New Title Failed:", title, r.status_code, r.reason)


@click.command()
@click.option('--model-name', prompt='Name of the Model', help='Reference to local path at hg_models/')
@click.option('--low-mem/--no-low-mem', default=False,
              help='Whether to run in low memory mode (must be false on TPU vm)')
@click.option('--max-generated', default=10,
              help='Interger stops generation if there are already this many prompts')
def main(model_name, low_mem, max_generated):
    url = f'http://35.223.44.38/prompt/next-prompt/?model_type={model_name}'
    data = requests.get(url).json()
    generated = data["generated"]
    prompt_text = data["text"]
    additional = data["max_length"]
    # Loading the model is expensive so this short circuits if there is nothing to generate
    if generated > max_generated:
        if model_name != 'plot_summary':
            return None

    my_writer = TextWriter(f"hg_models/{model_name}", low_mem)

    for i in range(50):
        story_text = my_writer.generate_story(prompt_text, additional)
        requests.post('http://35.223.44.38/generated-text/', data={"text": story_text, 'prompt': data['id']})
        data = requests.get(url).json()
        generated = data["generated"]
        prompt_text = data["text"]
        additional = data["max_length"]

        if generated > max_generated:
            if model_name == 'plot_summary':
                my_writer.generate_new_story()
            else:
                return None


if __name__ == '__main__':
    main()
