import litellm

MODEL = "ollama_chat/qwen2.5:1.5b"
SYSTEM_PROMPT = "You are a helpful assistant."

# Initialize context with the system prompt
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:
    user_msg = input("USER: ")

    # Append user's message to the context
    messages += [{"role": "user", "content": user_msg}]

    # Generate response passing the full conversation history
    reply = litellm.completion(
        model=MODEL,
        messages=messages,
        max_tokens=50,
    ).choices[0].message.content

    # Append assistant's reply to the context
    messages += [{"role": "assistant", "content": reply}]

    print(f"ASSISTANT: {reply}\n")
