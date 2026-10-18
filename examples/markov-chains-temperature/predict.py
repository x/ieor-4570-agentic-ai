import math
import json
import random
import sys

if len(sys.argv) != 3:
    print("Usage: uv run predict.py <transitions.json> <temperature>")
    sys.exit(1)

transitions_path = sys.argv[1]
temperature = float(sys.argv[2])

if temperature < 0:
    print("Temperature must be 0 or greater.")
    sys.exit(1)

with open(transitions_path, "r") as f:
    transitions = json.load(f)


def apply_temperature(probs, temperature):
    if temperature == 1.0:
        return probs

    log_probs = [math.log(p) / temperature for p in probs]

    # Compute softmax to get new probabilities
    max_log_prob = max(log_probs)
    exp_probs = [math.exp(lp - max_log_prob) for lp in log_probs]
    sum_exp = sum(exp_probs)

    return [p / sum_exp for p in exp_probs]


def predict_next(current_token, temperature):
    if current_token not in transitions:
        return None
    candidates = list(transitions[current_token].keys())
    probs = list(transitions[current_token].values())

    # Temperature 0 is the limit of the formula below: always the likeliest token.
    if temperature == 0:
        return max(zip(candidates, probs), key=lambda pair: pair[1])[0]

    # Apply temperature
    probs = apply_temperature(probs, temperature)

    return random.choices(candidates, weights=probs)[0]


def generate_sequence(start_token, length, temperature):
    sequence = [start_token]
    current_token = start_token
    for _ in range(length - 1):
        next_word = predict_next(current_token, temperature)
        if next_word is None:
            break
        sequence.append(next_word)
        current_token = next_word
    return sequence


start_token = "The"
sequence = generate_sequence(start_token, 100, temperature)
print(" ".join(sequence))
