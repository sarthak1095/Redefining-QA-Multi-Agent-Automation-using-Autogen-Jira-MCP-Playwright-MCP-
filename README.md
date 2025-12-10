# **Redefining QA Multi-Agent Automation using Autogen (OpenAI + Jira MCP + Playwright MCP)**

This project showcases an advanced **multi-agent AI automation system** that integrates:

* **Autogen multi-agent collaboration**
* **OpenAI (Gemini-2.5-Flash model)**
* **Jira MCP Automation**
* **Playwright MCP Browser Automation**
* **Round-robin agent orchestration**
* **LLM-generated smoke test scripts**
* **Fully automated execution of test steps**

---

## **Project Overview**

This system simulates a full **QA Automation Workflow**:

### **Agent 1 – Bug_Analyst (Jira Agent)**

Analyses latest Jira bugs → identifies patterns → creates detailed smoke test scenarios.

### **Agent 2 – Automation_Expert (Playwright MCP Agent)**

Converts smoke test cases → Playwright steps → executes them automatically → reports results.

### **Workflow**

1. Retrieve bugs from Jira MCP container
2. Generate structured smoke test scripts
3. Convert to automated Playwright MCP browser actions
4. Execute UI tests step-by-step with screenshots
5. Terminate only when `"TESTING COMPLETE"` is reached

---

## **Architecture Diagram**

```
                           ┌─────────────────────────┐
                           │        Developer         │
                           │     (Runs main.py)       │
                           └─────────────┬───────────┘
                                         │
                                         ▼
                    ┌────────────────────────────────────────┐
                    │        Autogen Orchestrator            │
                    │   (Round-Robin Multi-Agent Control)    │
                    └───────────────┬───────────────┬────────┘
                                    │               │
                                    │               │
              ┌─────────────────────▼───┐       ┌───▼─────────────────────┐
              │   Bug_Analyst Agent     │       │  Automation_Expert Agent │
              │      (Jira Agent)       │       │    (Playwright Agent)   │
              └───────────────┬─────────┘       └───────────┬─────────────┘
                              │                               │
                              │                               │
                   ┌──────────▼──────────┐         ┌─────────▼───────────┐
                   │      Jira MCP       │         │    Playwright MCP    │
                   │ (Docker Container)  │         │   (npx runtime)      │
                   └──────────┬──────────┘         └─────────┬───────────┘
                              │                               │
                              ▼                               ▼
        ┌────────────────────────────┐            ┌──────────────────────────┐
        │  Fetch Latest Defects      │            │  Execute Browser Actions  │
        │  Generate Smoke Tests      │            │   Run UI Automation       │
        └───────────────┬────────────┘            └───────────┬─────────────┘
                        │                                      │
                        ▼                                      ▼
          ┌───────────────────────────┐           ┌──────────────────────────┐
          │   Hand Off Test Scripts   │           │ Validate Results         │
          │  → “HANDOFF TO AUTOMATION”│           │ Capture Screenshots      │
          └──────────────┬────────────┘           └───────────┬─────────────┘
                         │                                     │
                         └─────────────────────────────────────┘
                                           ▼
                              ┌─────────────────────────────┐
                              │     Final Execution Log      │
                              │   → “TESTING COMPLETE”      │
                              └─────────────────────────────┘



```

## **Code Walkthrough**

### **1. Imports & Environment Setup**

The script loads Autogen agents, MCP tools, and environment variables:

```python
import asyncio, os
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
...
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
```

### **2. LLM Client**

Defines the AI model with structured output enabled:

```python
model_client = OpenAIChatCompletionClient(
    model="gemini-2.5-flash",
    model_info=ModelInfo(vision=True, function_calling=True, json_output=True)
)
```

### **3. MCP Workbenches**

Connects to:

* **Jira MCP** via Docker
* **Playwright MCP** via npx

```python
JIRA_server_params = StdioServerParams(command="docker", args=[...])
Playwright_server_params = StdioServerParams(command="npx", args=[...])
```

### **4. Agent Role Definitions**

Each agent receives a system prompt describing its responsibility:

```python
JIRA_prompt = """You are a Bug Analyst..."""
Playwright_prompt = """You are a Playwright automation expert..."""
```

### **5. Multi-Agent Orchestration**

Uses round-robin scheduling so both agents collaborate:

```python
JIRA_Automation_Team = RoundRobinGroupChat(
    participants=[JIRA_Agent, PLAYWRIGHT_Agent],
    termination_condition=TextMentionTermination("TESTING COMPLETE")
)
```

### **6. Task Definition**

Sets the conversation’s starting goal:

```python
task = """
JIRA_Agent:
1. Search for recent bugs...
PLAYWRIGHT_Agent:
Automate this flow using Playwright MCP...
"""
```

### **7. Execution**

Runs the agents and streams output:

```python
await Console(JIRA_Automation_Team.run_stream(task=task))
```


## **Advantages of This Multi-Agent QA Automation System**

1. **End-to-End Automation**

   * Eliminates manual QA scripting by automatically generating, converting, and executing test cases.
   * Reduces human error and speeds up test cycles.

2. **AI-Driven Intelligence**

   * Bug analysis and test generation are performed by an LLM (Gemini-2.5-Flash).
   * Can detect patterns in real Jira defects and propose robust smoke tests.

3. **Seamless Multi-Agent Collaboration**

   * Two agents (Bug_Analyst & Automation_Expert) work together asynchronously.
   * Mimics real-world team handoffs with clear responsibilities and structured outputs.

4. **Real-World Tool Integration**

   * Works directly with Jira for defect retrieval and Playwright for browser automation.
   * Uses Docker and npx for isolated, reproducible execution environments.

5. **Structured, Actionable Outputs**

   * Smoke test steps are output in a clear, structured format.
   * Automated execution produces logs, screenshots, and validation results for easy review.

6. **Extensible and Future-Ready**

   * Architecture allows swapping or adding new MCP tools (e.g., API tests, CI/CD notifications).
   * Can scale to more agents or additional workflows without changing core orchestration.

7. **Improves QA Efficiency**

   * Speeds up defect analysis and testing.
   * Frees QA engineers to focus on edge cases and exploratory testing.

8. **Leadership-Level Insight**

   * Demonstrates AI-driven decision making in software quality.
   * Shows practical, end-to-end AI workflow execution that can be showcased in portfolios or demos.


