# Markov Chains - Temperature

A Markov chain with temperature control to adjust sampling diversity. Lower temperatures favor high-probability tokens (more conservative), while higher temperatures create more diverse outputs.

## Running

Train the model on a book:
```bash
uv run train.py frankenstein.txt
```

This creates `frankenstein-transitions.json` containing the learned transition probabilities.

Generate text with different temperatures:
```bash
# Very low temperature (0.1) - nearly deterministic, highly repetitive
uv run predict.py frankenstein-transitions.json 0.1

# Balanced temperature (0.7) - common default for LLMs
uv run predict.py frankenstein-transitions.json 0.7

# High temperature (2.0) - more diverse, creative
uv run predict.py frankenstein-transitions.json 2.0
```

## Temperature Effects

- **Temperature < 1.0**: Sharpens the probability distribution, making high-probability tokens even more likely. Results in more conservative, predictable text. Temperature 0.7 is a common default in production LLMs.
- **Temperature = 1.0**: Uses the original probability distribution unchanged.
- **Temperature > 1.0**: Flattens the probability distribution, giving lower-probability tokens more chance. Results in more diverse, creative (but potentially incoherent) text.
