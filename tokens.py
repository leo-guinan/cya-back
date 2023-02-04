from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

with open("sample.txt", "r") as f:
    t = f.read()
    print(len(tokenizer(t)['input_ids']))