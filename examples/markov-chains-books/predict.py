import json
import random
import sys

if len(sys.argv) != 2:
    print("Usage: uv run predict.py <transitions.json>")
    sys.exit(1)

transitions_path = sys.argv[1]

with open(transitions_path, "r") as f:
    transitions = json.load(f)


def predict_next(current_token):
    if current_token not in transitions:
        return None
    candidates = list(transitions[current_token].keys())
    probs = list(transitions[current_token].values())
    return random.choices(candidates, weights=probs)[0]


def generate_sequence(start_token, length):
    sequence = [start_token]
    current_token = start_token
    for _ in range(length - 1):
        next_word = predict_next(current_token)
        if next_word is None:
            break
        sequence.append(next_word)
        current_token = next_word
    return sequence


start_token = "The"
sequence = generate_sequence(start_token, 50)
print(" ".join(sequence))
