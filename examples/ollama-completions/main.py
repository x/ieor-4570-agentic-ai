from litellm import completion

# Ollama runs the model as a local server on http://localhost:11434.
# LiteLLM's "ollama/" prefix routes the call there. Same function, same
# arguments as a hosted model; only the model string changes.
MODEL = "ollama/qwen2.5:1.5b"

text = "The scientific method is"

response = completion(
    model=MODEL,
    messages=[{"role": "user", "content": text}],
    temperature=0.7,
    max_tokens=50,
)

print(response.choices[0].message.content)
