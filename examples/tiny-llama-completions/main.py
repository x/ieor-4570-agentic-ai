import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 1. Load Model
model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    dtype=torch.float32,
)

# 2. Input (Hardcoded for this website demo)
# In your script, you would use: text = input("Start a sentence: ")
text = "The scientific method is"

inputs = tokenizer(text, return_tensors="pt")

# 3. Generate
output_tokens = model.generate(
    **inputs,
    max_new_tokens=50,
    do_sample=True,
    temperature=0.7,
    pad_token_id=tokenizer.eos_token_id,
)

# 4. Decode
completion = tokenizer.decode(output_tokens[0], skip_special_tokens=True)

# Print cleanly for Quarto
print(completion)
