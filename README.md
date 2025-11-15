# CoderLang
An Agent-driven Compiler &amp; Tutor Engine for Developer Productivity

## 🧩 Overview

CoderLang is an enterprise-grade **multi-agent coding assistant** built using Google’s **Agent Development Kit (ADK)** and powered by **Gemini** models. It translates code, debugs programs, generates tests, explains logic, and executes code safely using long-running operations. The system demonstrates production-ready agent patterns, including:

* Multi-Agent Architecture
* Tooling (Search, Code Execution, Test Generation)
* Memory (Short-Term + Long-Term)
* Observability (Logs, Traces, Metrics)
* A2A (Agent-to-Agent) Collaboration
* Optional Deployment via Vertex AI Agent Engine

CoderLang is designed as a coding tutor, auto-debugger, and enterprise workflow assistant.

---

## 🧠 Problem Statement

Developers lose significant time switching between debugging, researching errors, documenting code, writing tests, translating logic, and optimizing performance. These tasks are repetitive, time-consuming, and error-prone.

CoderLang solves this by allowing multiple specialized AI agents to collaborate like a real engineering team.

---

## 🎯 Why Agents?

Single LLM prompts can *write* code, but they cannot manage workflows that require:

* multi-step reasoning
* calling tools at the right time
* iterative debugging
* using memory across tasks
* evaluating intermediate outputs

Agents solve this through orchestration, loops, verification, tool integration, and specialized roles.

CoderLang shows agents working together to:

1. understand the task
2. write code
3. test it
4. debug it
5. generate documentation
6. translate it
7. evaluate correctness

---

## 🧱 Architecture

**Orchestrator**

* Routes requests across agents
* Manages tool flow
* Stores logs, traces, metrics

**Agents**

* Coding Agent
* Debugging Agent
* Translation Agent
* Explanation Agent
* Test Generator Agent
* Documentation Agent
* Safety Agent
* Judge/Evaluator Agent

**Tools**

* Code Execution Tool (LRO)
* Search Tool (Gemini API)
* Test Generator Tool
* File Tool

**Memory**

* short_term.json (session context)
* long_term.json (persistent patterns)

**Observability**

* events.log
* traces.log
* metrics.json

---

## 📦 File Structure

```
coderlang/
├── README.md
├── requirements.txt
├── Dockerfile
├── main.py
│
├── orchestrator/
│   ├── router.py
│   ├── coordinator.py
│   └── evaluator.py
├── agents/
│   ├── coding_agent.py
│   ├── debugging_agent.py
│   ├── translate_agent.py
│   ├── explain_agent.py
│   ├── test_generator_agent.py
│   ├── doc_agent.py
│   └── safety_agent.py
├── tools/
│   ├── run_code.py
│   ├── generate_tests.py
│   ├── search_tool.py
│   └── file_tool.py
├── memory/
│   ├── short_term.json
│   ├── long_term.json
│   └── memory_store.py
├── observability/
│   ├── logs/
│   ├── logger.py
│   ├── tracer.py
│   └── metrics.py
├── deployment/
│   ├── vertex_config.yaml
│   ├── cloudrun.yaml
│   └── README_DEPLOY.md
└── tests/
    ├── test_agents.py
    ├── test_tools.py
    └── test_memory.py
```

---

## 🚀 Local Development

```
pip install -r requirements.txt
python main.py
```

---

## 🐳 Docker

```
docker build -t coderlang .
docker run -it coderlang
```

---

## ☁ Deployment (Vertex Agent Engine)

See `deployment/README_DEPLOY.md`.

---

## 🧪 Tests

```
pytest tests/
```

---

## 🧠 Future Work

* Add domain-specific compilers
* Add a UI dashboard
* Expand supported languages
* Integrate static analysis tools

---

# Kaggle Notebook Template

## 🧩 Title

**CoderLang — Multi-Agent Code Assistant (Enterprise Track)**

---

## 📘 1. Introduction

* Short problem explanation
* Why agents are needed
* Architecture diagram (insert PNG)
* Link to GitHub repository

---

## 📦 2. Install Dependencies

```python
!pip install google-genai google-cloud-aiplatform rich
```

---

## 🔑 3. Load API Key

```python
import os
os.environ["GOOGLE_API_KEY"] = kaggle_secrets.get("GOOGLE_API_KEY")
```

---

## 🛠 4. Define Tools (Simplified)

Include notebook versions of:

* Code execution tool
* Search tool
* Test generator

---

## 🤖 5. Define Notebook Agents

Create simplified ADK agents:

* CodingAgent
* DebugAgent
* TranslateAgent
* ExplainAgent
* JudgeAgent

---

## 🧠 6. Orchestrator (Notebook Version)

```python
response = orchestrator.run(
    "Write Python Fibonacci, translate to C++, generate tests, explain logic"
)
print(response)
```

---

## 📊 7. Observability Demo

```python
print(tracer.show())
print(logger.tail())
```

---

## 🧬 8. Memory Demo

```python
memory.write("preferred_language", "Python")
memory.read("preferred_language")
```

---

## 🖥 9. Demo Results

Show:

* generated code
* translated version
* tests
* explanation
* judge score

---

## 🧭 10. Conclusion

* What you achieved
* What you'd improve with more time

---

This is the complete structure for both your **GitHub repository** and **Kaggle notebook**, ready for the December 1 submission.
