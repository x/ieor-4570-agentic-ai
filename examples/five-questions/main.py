import warnings

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

warnings.filterwarnings("ignore", category=UserWarning)

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
ERASE_LINE = "\033[F\033[K"
SYSTEM_PROMPT = """
We are playing a guessing game. Think of a single everyday object,
but DO NOT SAY WHAT IT IS and DO NOT GIVE CLUES. The user will ask yes-or-no questions.
Reply to each question with exactly one line in this form:
"Yes. You have N questions remaining." or "No. You have N questions remaining."
Never ask questions. Never name the object. Never give clues.
When the user has no questions remaining, wait for them to guess or give up.
Stay consistent with your earlier answers. Only reveal the object
if the user gives up and asks what it was."""

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "Let's play 5 questions."},
    {"role": "assistant", "content": "I have my object in mind. You have 5 questions remaining."},
]

device = "mps" if torch.backends.mps.is_available() else "cpu"
model = AutoModelForCausalLM.from_pretrained(MODEL_ID).to(device)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

# The screen is the context. Print it once, then only append or erase.
print(f"<system>\n{messages[0]['content']}\n</system>")
for m in messages[1:]:
    print(f"<{m['role']}>{m['content']}</s>")

while True:
    try:
        user_text = input("<user>").strip()
    except (EOFError, KeyboardInterrupt):
        break

    if user_text.lower() == "quit":
        break

    if user_text.lower() == "rewind":
        print(ERASE_LINE * 3, end="")
        messages.pop()
        messages.pop()
        continue

    print(f"{ERASE_LINE}<user>{user_text}</s>")
    messages.append({"role": "user", "content": user_text})

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_new_tokens=24, do_sample=True, temperature=0.9)
    reply = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    reply = " ".join(reply.split())

    print(f"<assistant>{reply}</s>")
    messages.append({"role": "assistant", "content": reply})
