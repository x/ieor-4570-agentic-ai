# Gemini Hello World

Simple test to verify your Gemini setup is working correctly.

## Running

Run the test script:

```bash
uv run main.py
```

If you see a 5-word greeting from Gemini and a success message, your setup is working correctly.

No configuration needed - the script uses your gcloud authentication and project settings automatically.

## Troubleshooting

If you get an authentication error, make sure you've run:

```bash
gcloud auth application-default login
```

And that you checked ALL the permission boxes during authentication.

If you get a "project not found" error, make sure you've set your project:

```bash
gcloud config set project YOUR-PROJECT-ID
```
