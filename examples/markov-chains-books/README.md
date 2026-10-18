# Markov Chains - Books

A Markov chain trained on classic literature to generate text in a similar style.

## Running

Train the model on a book:
```bash
uv run train.py frankenstein.txt
```

This creates `frankenstein-transitions.json` containing the learned transition probabilities.

Generate text using the trained weights:
```bash
uv run predict.py frankenstein-transitions.json
```

You can train on either book:
```bash
uv run train.py moby-dick.txt
uv run predict.py moby-dick-transitions.json
```
