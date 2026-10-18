import json

corpus = [
    "I like to eat apples",
    "I like to eat bananas",
    "I like to play",
    "I love to play",
    "apples are good",
    "bananas are good"
]

transitions = {}

# 1. Populate the transitions dictionary with counts
for document in corpus:
    tokens = document.split(" ")
    for i in range(len(tokens) - 1):
        current_token = tokens[i]
        next_token = tokens[i + 1]

        if current_token not in transitions:
            transitions[current_token] = {}

        if next_token not in transitions[current_token]:
            transitions[current_token][next_token] = 0

        transitions[current_token][next_token] += 1

# 2. Convert counts to probabilities
for current_token, next_tokens in transitions.items():
    total = sum(next_tokens.values())
    for next_token in next_tokens:
        transitions[current_token][next_token] /= total

# 3. Save the transitions to a file
with open("transitions.json", "w") as f:
    json.dump(transitions, f, indent=2)

print("Training complete! Transitions saved to transitions.json")
