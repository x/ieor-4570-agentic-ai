# Agentic AI

IEOR 4570, Columbia University. Taught by Devon Peticolas.

Slides and code for a hands-on course where students design, build, and ship production-grade, task-specific AI agents that plan, retrieve knowledge, call tools, and interact with users in real time.

The course starts with the principles behind LLMs and builds up to modern patterns such as retrieval-augmented generation, natural language to SQL, agent memory, sandboxed coding, and deep research. There's a focus on production requirements: persistent sessions, evaluations, observability, and cost control. Students write agents in Python, with front-ends, and deploy them to Google Cloud Platform.

**Browse the slides and live demos at [https://x.github.io/ieor-4570-agentic-ai](https://x.github.io/ieor-4570-agentic-ai/).**

## Learning Objectives

- Understand the principles of how large language models (LLMs) and chat interfaces work.
- Assess and implement prompt engineering, tool calling, and retrieval-augmented generation to improve LLM task performance.
- Understand and implement methods of evaluation to hill climb an agent.
- Assess and implement multi-agent architectures.
- Deploy production-grade agents to GCP using the OpenAI Agents SDK, potentially including secondary services such as databases, vector databases, and monitoring infrastructure.
- Make design decisions that shape accuracy, cost, and latency, and communicate trade-offs to stakeholders.

## Prerequisites

Prior experience in Python and a working knowledge of basic machine learning. A coding agent subscription (such as Claude Code or Codex) is not required, but is beneficial.

## Format

Each 150-minute class combines a concepts lecture, in-class coding, and, when possible, a real-world case study. In place of exams, students build three agents: a tool-calling agent, a deep research agent, and a capstone agent of their own design, each deployed to GCP.

## Schedule

### 1. Introduction and Large Language Models

- The history and inner workings of modern large language models
- Post-training: RLHF, RLVR, RaR
- Development environment: Python env, repo skeleton, local run workflow

| Slides | Examples |
|-|-|
| [Introduction](https://x.github.io/ieor-4570-agentic-ai/slides/introduction/) | [hello-world](examples/hello-world) |
| [Large Language Models](https://x.github.io/ieor-4570-agentic-ai/slides/large-language-models/) | [markov-chains-basic](examples/markov-chains-basic), [markov-chains-books](examples/markov-chains-books), [tiny-llama-completions](examples/tiny-llama-completions), [tiny-llama-chat](examples/tiny-llama-chat) |

### 2. Chatbots, Prompting, and Reasoning

- How does an LLM become a chatbot? Who am I talking to?
- Classic prompt engineering techniques
- Classic chain-of-thought prompting and modern model reasoning
- Working with hosted models

| Slides | Examples |
|-|-|
| [Chatbots](https://x.github.io/ieor-4570-agentic-ai/slides/chatbots/) | [markov-chains-temperature](examples/markov-chains-temperature), [ollama-completions](examples/ollama-completions), [qwen-web-chat](examples/qwen-web-chat) |
| [In-Context Learning](https://x.github.io/ieor-4570-agentic-ai/slides/in-context-learning/) | [few-shot](examples/few-shot), [five-questions](examples/five-questions), [five-questions-web](examples/five-questions-web) ([live](https://five-questions-web-16155576949.us-east1.run.app)) |
| [Reasoning](https://x.github.io/ieor-4570-agentic-ai/slides/reasoning/) |  |

### 3. Agents that Live and Do

- Tool calling, how it works and best practices
- What's an agent harness?
- Client/server HTTP agents
- Deploying to GCP

| Slides | Examples |
|-|-|
| [Harnesses and Tool Calling](https://x.github.io/ieor-4570-agentic-ai/slides/tool-calling/) | [qwen-chat](examples/qwen-chat), [qwen-tool-calling](examples/qwen-tool-calling), [gemini-hello-world](examples/gemini-hello-world), [gemini-web-tool-calling](examples/gemini-web-tool-calling) ([live](https://gemini-web-tool-calling-16155576949.us-east1.run.app)) |

### 4. Agents in Production and Evaluated

- OpenAI Agents SDK
- Other agent frameworks: Google ADK, LangGraph, PydanticAI
- Agent traces (OTEL)
- Guardrails

| Slides | Examples |
|-|-|
| [Guardrails and Agent Frameworks](https://x.github.io/ieor-4570-agentic-ai/slides/agent-frameworks/) | [guardrails-password-challenge](examples/guardrails-password-challenge), [guardrails-password-challenge-web](examples/guardrails-password-challenge-web) ([live](https://guardrails-password-challenge-web-16155576949.us-east1.run.app)), [agents-sdk-chat](examples/agents-sdk-chat), [agents-sdk-web](examples/agents-sdk-web) |
| [Other Agent Frameworks](https://x.github.io/ieor-4570-agentic-ai/slides/other-agent-frameworks/) | [adk-web](examples/adk-web) |

### 5. Evaluating Agents

- Offline evaluations and hill climbing
- Golden and silver datasets
- Online evaluations
- Eval-first agent design

| Slides | Examples |
|-|-|
| [Evaluations](https://x.github.io/ieor-4570-agentic-ai/slides/evaluations/) | [nyc-311-agent](examples/nyc-311-agent) |

### 6. RAG

- Classic (semantic) retrieval augmented generation
- Text2SQL
- Non-semantic RAG

| Slides | Examples |
|-|-|
| [Retrieval Augmented Generation](https://x.github.io/ieor-4570-agentic-ai/slides/retrieval-augmented-generation/) | [magic-item-shop-classic-rag](examples/magic-item-shop-classic-rag), [magic-item-shop-semantic-rag](examples/magic-item-shop-semantic-rag), [magic-item-shop-filesystem-rag](examples/magic-item-shop-filesystem-rag) |

### 7. Multi-Agent Architectures

- Basic multi-agent patterns
- Composite multi-agent patterns, deep research

### 8. Memory and Modern Context Engineering

- State vs. session vs. context vs. memory
- Trimming, truncating, and summarizing context
- The overwhelming importance of the KV-cache

### 9. Coding Agents and Modern Tool Calling

- Model Context Protocol, local and remote
- Coding as a form of tool composition
- MCP: Code Mode
- Progressive tool disclosure
- Sandboxes

### 10. Claude Code

- A walk through of the Spring '26 Claude Code source code leak
- How I use Claude Code

### 11. Fun Topics

- Autoresearch / goal-mode
- Constrained decoding
- AI detectors and watermarking
- Frontier labs, hyperscalers, enterprise FDEs, the industry landscape

## Running the Code

Every folder in [`examples/`](examples) is a standalone [uv](https://docs.astral.sh/uv/) project with its own README. Each deck in [`slides/`](slides) is a [Slidev](https://sli.dev) presentation: `cd slides/<deck> && pnpm install && pnpm dev`.
