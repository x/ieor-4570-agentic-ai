import warnings

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

warnings.filterwarnings("ignore", category=UserWarning)

MADE_UP_WORD = "rindy"

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
SYSTEM_PROMPT = f"""
You are a {MADE_UP_WORD} detector. The user will ask you if something is
"{MADE_UP_WORD}" and you must respond with "That's so {MADE_UP_WORD}" if it
is {MADE_UP_WORD} or with "That's not {MADE_UP_WORD}" if it's not.
<examples>
  <example>
    <user>No-show ankle socks.</user>
    <assistant>That's so {MADE_UP_WORD}.</assistant>
  </example>
  <example>
    <user>Digital point-and-shoots.</user>
    <assistant>That's not {MADE_UP_WORD}.</assistant>
  </example>
  <example>
    <user>Talking about your hogwarts house.</user>
    <assistant>That's so {MADE_UP_WORD}.</assistant>
  </example>
</examples>"""


messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
]

device = "mps" if torch.backends.mps.is_available() else "cpu"
model = AutoModelForCausalLM.from_pretrained(MODEL_ID).to(device)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

# The screen is the context. Print it once, then only append or erase.
print(f"<system>\n{messages[0]['content']}</system>")
for m in messages[1:]:
    print(f"<{m['role']}>{m['content']}</s>")

while True:
    try:
        user_text = input("<user>").strip()
    except (EOFError, KeyboardInterrupt):
        break

    print(f"\033[F\033[K<user>{user_text}</s>")
    messages.append({"role": "user", "content": user_text})

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_new_tokens=24, do_sample=True, temperature=0.9)
    reply = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    reply = " ".join(reply.split())

    print(f"<assistant>{reply}</s>")
    messages.append({"role": "assistant", "content": reply})
