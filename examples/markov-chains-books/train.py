import json
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print("Usage: uv run train.py <book.txt>")
    sys.exit(1)

book_file = sys.argv[1]
book_path = Path(book_file)
output_path = book_path.stem + "-transitions.json"

transitions = {}

with open(book_file, "r", encoding="utf-8") as f:
    text = f.read()

tokens = text.split()

for i in range(len(tokens) - 1):
    current_token = tokens[i]
    next_token = tokens[i + 1]

    if current_token not in transitions:
        transitions[current_token] = {}

    if next_token not in transitions[current_token]:
        transitions[current_token][next_token] = 0

    transitions[current_token][next_token] += 1

for current_token, next_tokens in transitions.items():
    total = sum(next_tokens.values())
    for next_token in next_tokens:
        transitions[current_token][next_token] /= total

with open(output_path, "w") as f:
    json.dump(transitions, f)

print(f"Trained on: {book_path.name}")
print(f"Total unique tokens: {len(transitions)}")
print(f"Saved to: {output_path}")
