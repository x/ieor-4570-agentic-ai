# IEOR 4570 Agentic AI - Resources

Slides, code examples, and live demos from Columbia DSi IEOR 4570, a hands-on course on building and shipping AI Agents. Materials focus on the basics of LLMs, modern agent development, and deploying to GCP with OpenAI Agents SDK, LiteLLM, and Gemini.

## Lectures

### Introduction

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/introduction/)

Course introduction and an overview of building production-grade AI agents.

- [hello-world](examples/hello-world)

### Large Language Models

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/large-language-models/)

The architecture and evolution of modern LLMs, from Markov chains to Transformers.

- [markov-chains-basic](examples/markov-chains-basic)
- [markov-chains-books](examples/markov-chains-books)
- [tiny-llama-completions](examples/tiny-llama-completions)
- [tiny-llama-chat](examples/tiny-llama-chat)

### Chatbots

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/chatbots/)

From terminal to web: the client-server architecture behind an LLM chatbot.

- [markov-chains-temperature](examples/markov-chains-temperature)
- [ollama-completions](examples/ollama-completions)
- [qwen-web-chat](examples/qwen-web-chat)

### In-Context Learning

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/in-context-learning/)

Role-play, InstructGPT, and the principles of a good one-shot prompt.

- [few-shot](examples/few-shot)
- [five-questions](examples/five-questions)
- [five-questions-web](examples/five-questions-web)

### Sampling, Constrained Decoding, and Watermarking

### Reasoning

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/reasoning/)

From chain-of-thought prompting to reasoning models. How In-Context Learning becomes Reasoning.

### Harnesses and Tool Calling

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/tool-calling/)

Agent harnesses and tool calling for LLM-based agents.

- [qwen-chat](examples/qwen-chat)
- [qwen-tool-calling](examples/qwen-tool-calling)
- [gemini-hello-world](examples/gemini-hello-world)
- [gemini-web-tool-calling](examples/gemini-web-tool-calling)

### Guardrails and Agent Frameworks

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/agent-frameworks/)

Guardrails on the agent loop and the OpenAI Agents SDK.

- [guardrails-password-challenge](examples/guardrails-password-challenge)
- [guardrails-password-challenge-web](examples/guardrails-password-challenge-web)
- [agents-sdk-chat](examples/agents-sdk-chat)
- [agents-sdk-web](examples/agents-sdk-web)

### Other Agent Frameworks

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/other-agent-frameworks/)

Google ADK, Claude Agent SDK, LangGraph, and Pydantic AI.

- [adk-web](examples/adk-web)

### Evaluations

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/evaluations/)

Deterministic checks, golden references, rubrics, gold and silver datasets, pass@k, and offline vs. online evals.

- [nyc-311-agent](examples/nyc-311-agent)

### Retrieval Augmented Generation

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/retrieval-augmented-generation/)

Classic (semantic) RAG, retrieval as a tool call, reranking, hybrid search, and filesystem RAG.

- [magic-item-shop-classic-rag](examples/magic-item-shop-classic-rag)
- [magic-item-shop-semantic-rag](examples/magic-item-shop-semantic-rag)
- [magic-item-shop-filesystem-rag](examples/magic-item-shop-filesystem-rag)

### Text2SQL Agents

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/text2sql/)

Agents that perform retrieval from SQL databases.

- [subway-survey-text2sql](examples/subway-survey-text2sql)
- [subway-survey-text2sql-improved](examples/subway-survey-text2sql-improved)
- [nyc-311-agent](examples/nyc-311-agent)
- [nyc-311-agent-improved](examples/nyc-311-agent-improved)

### Tracing and Monitoring

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/tracing-and-monitoring/)

Tracing agents with OpenTelemetry and Langfuse.

- [nyc-311-agent-langfuse](examples/nyc-311-agent-langfuse)

### Multi-Agent Architectures

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/multi-agent-architectures/)

Orchestration patterns, handoffs, human-in-the-loop, and deep research.

- [wikipedia-deck-critic](examples/wikipedia-deck-critic)
- [nyc-data-desk](examples/nyc-data-desk)
- [wikipedia-deck-researchers](examples/wikipedia-deck-researchers)
- [wikipedia-deep-research](examples/wikipedia-deep-research)

### Sessions, State, and Memory

### KV-Cache

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/kv-cache/)

How the KV-cache speeds up generation, and how prompt caching across requests cuts agent latency and cost.

- [kv-cache-web](examples/kv-cache-web)

### What Can We Learn From Claude Code

[slides](https://peticol.as/ieor-4570-agentic-ai/slides/claude-code/)

The agent loop, prompt caching, tool pipeline, and memory system inside Claude Code's leaked source.

### Coding Agents

## Live Demos

### five-questions-web

[demo](https://five-questions-web-16155576949.us-east1.run.app) · [src](examples/five-questions-web)

Play five questions against Gemini while watching its context, then rewind and ask again to see that no object was ever chosen.

![five-questions-web](readme-images/five-questions-web.png)

### gemini-web-tool-calling

[demo](https://gemini-web-tool-calling-16155576949.us-east1.run.app) · [src](examples/gemini-web-tool-calling)

A web chatbot with a weather tool that shows every tool call the harness runs before the answer.

![gemini-web-tool-calling](readme-images/gemini-web-tool-calling.png)

### guardrails-password-challenge-web

[demo](https://guardrails-password-challenge-web-16155576949.us-east1.run.app) · [src](examples/guardrails-password-challenge-web)

Get the model to reveal a password across seven levels, each stacking a new guardrail on the last.

![guardrails-password-challenge-web](readme-images/guardrails-password-challenge-web.png)

### wikipedia-deep-research

[demo](https://wikipedia-deep-research-16155576949.us-east1.run.app) · [src](examples/wikipedia-deep-research)

Ask a question from a starting Wikipedia article and watch a Lead fan out parallel Researchers, then a Writer turn their findings into a cited report.

![wikipedia-deep-research](readme-images/wikipedia-deep-research.png)

### kv-cache-web

[demo](https://kv-cache-web-16155576949.us-east1.run.app) · [src](examples/kv-cache-web)

Two agents read The Hound of the Baskervilles chapter by chapter; one prompt starts with the current time, the other with today's date. Watch time to first token and cached tokens diverge.

![kv-cache-web](readme-images/kv-cache-web.png)
