# Five Questions

A guessing game against Qwen2.5-1.5B-Instruct, to show that the model never "thinks of" an object.

## Running

```bash
uv run main.py
```

The first run will download the model (~3GB). On Apple silicon it runs on the GPU (MPS); elsewhere it falls back to CPU.

## Playing

Ask up to five yes/no questions. Anything you type is sent to the model, except two commands:

- `rewind` erases the last question and its answer, so you can ask the same thing again.
- `quit` exits. (Ctrl-C and Ctrl-D also work.)

To see what it was thinking of, just ask: type `What was it?`

The demo: ask what the object was, then `rewind`, then ask again. The second answer will
often name a different object that is also consistent with every earlier answer. Nothing was
chosen at the start; each answer is generated to fit the transcript so far.

## Sample run

```
<user>Is it bigger than a shoebox?</s>
<assistant>No. You have 4 questions remaining.</s>
<user>Is it made of metal?</s>
<assistant>Yes. You have 3 questions remaining.</s>
<user>What was it?</s>
<assistant>A flashlight.</s>
<user>rewind
<user>What was it?</s>
<assistant>A smartphone.</s>
```
