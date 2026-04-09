# EVA Whisper Chat → Agentic AI OS

## Master Build Document

This document captures everything discussed in this chat: the system vision, the local + cloud model setup, Claude Code integration ideas, multi-model routing, agentic workflows, tool/skill expansion, repo integration plan, and the current implementation roadmap. It is written so it can be handed to Qwen / Qwen-Coder to analyze the repository and determine what is already done and what remains.

---

# 1. Project Vision

The project starts as **eva-whisper-chat** and is being evolved into a **personal AI operating system**.

The end goal is not just a chatbot. The system should be able to:

- understand user intent
- plan multi-step tasks
- choose the best model automatically
- use tools and skills
- operate in voice + text mode
- perform coding and non-coding agentic tasks
- manage personal productivity workflows
- support social, communication, media, and documentation actions

In short:

> **User input → Whisper → Memory → Intent → Planner → Agent Loop → Tools / Skills → Model Router → Model(s) → Response / Action**

---

# 2. Core Philosophy

The assistant should behave like an **agentic personal assistant**, not a passive Q&A bot.

That means it should:

- reason before acting
- break goals into steps
- choose tools when appropriate
- ask for confirmation before risky actions
- remember context across turns
- use local models first when possible
- fall back to cloud models when needed
- support coding, writing, scheduling, messaging, media control, and app automation

---

# 3. Important Safety / Key Management Note

During the chat, real API keys were shown. Those should be considered compromised.

Best practice:

- revoke any exposed keys immediately
- generate fresh keys
- never hardcode keys in source files
- use environment variables only
- keep secrets out of prompts, logs, and Git history

The system must be built so credentials are injected securely at runtime.

---

# 4. Desired High-Level Architecture

```text
User (voice/text)
    ↓
Whisper transcription
    ↓
Memory layer
    ↓
Intent detection
    ↓
Planner
    ↓
Agent loop
    ↓
Tool / skill execution
    ↓
Model router
    ↓
Local or cloud model
    ↓
Response and/or action
```

---

# 5. Model Strategy

The model stack discussed in this chat has three layers:

## A. Local / Free Layer
Use Ollama with Qwen models for local, low-cost, everyday tasks.

Examples:

- `qwen3.5:4b`
- `qwen3.5:9b`
- `qwen2.5-coder:7b`

Use this for:

- chat
- local reasoning
- coding assistance
- quick summaries
- offline or low-cost work

## B. OpenRouter Layer
Use OpenRouter as a cloud routing layer.

Use this for:

- stronger coding tasks
- better reasoning when needed
- fallback when local models are not enough
- cloud model access without direct provider lock-in

Examples discussed:

- `qwen/qwen2.5-coder-7b-instruct`
- `qwen/qwen2.5-coder-14b-instruct`
- `deepseek/deepseek-chat`
- OpenRouter free endpoints, though they may be rate-limited

## C. Anthropic Layer
Use Anthropic as premium fallback where necessary.

Use this for:

- strongest quality cases
- advanced reasoning
- difficult tasks

---

# 6. Claude Code Integration Concept

The chat discussed using Claude Code as the interface while pointing it to different backends.

Two main routing styles were discussed:

## A. Local Routing via Ollama
Claude Code can be pointed at a local Ollama server through Anthropic-compatible settings.

Conceptually:

```text
Claude Code → Ollama → Qwen
```

## B. Cloud Routing via OpenRouter
Claude Code can be pointed at OpenRouter by setting Anthropic-compatible environment variables.

Conceptually:

```text
Claude Code → OpenRouter → Qwen / other model
```

The important idea is that Claude Code can be made to talk to an Anthropic-compatible layer, and that layer can be local or cloud-based.

---

# 7. Environment Variable Strategy

The chat emphasized a clean environment variable setup.

Important principles:

- do not set both incompatible auth variables at the same time
- explicitly clear any conflicting Anthropic key if routing through OpenRouter
- use the proper base URL depending on whether the target is local Ollama or OpenRouter

The basic pattern discussed:

## Local / Ollama
- base URL points to local host
- auth token is a dummy value
- API key should be blank

## OpenRouter
- base URL points to OpenRouter’s API
- auth token is the OpenRouter key
- Anthropic API key should be blank

---

# 8. The Best Free Setup

The chat concluded that the best fully free path is:

```text
Claude Code-like interface → Ollama → Qwen
```

Why:

- fully local
- no cloud dependency
- no API cost
- good for development and experimentation

Recommended local model sizes depend on hardware:

- weaker laptop: smaller Qwen model
- mid-range machine: `qwen3.5:9b`
- stronger machine: larger model such as 14B or higher

---

# 9. Dual-Mode Setup

The discussed final setup is dual-mode:

## Mode 1 — Local, Free, Daily Use
- Ollama
- Qwen
- fast and cheap

## Mode 2 — Cloud Fallback
- OpenRouter
- Qwen coder or other cloud models
- used for harder or more expensive tasks

This gives a practical balance between:

- cost
- performance
- reliability
- quality

---

# 10. Auto Model Switcher

A key idea in the chat was to build an auto model switcher.

This router should inspect the user prompt and route it based on task type.

Possible signals:

- coding keywords
- long prompts
- architecture/system design requests
- simple chat
- general Q&A
- task execution

Suggested routing rules:

- simple chat → local Qwen
- coding → Qwen coder
- heavy reasoning → OpenRouter
- premium fallback → Anthropic
- if a provider fails → retry or switch

The switcher should also support:

- fallback chains
- logging which model was used
- configurable thresholds
- model selection by task category

---

# 11. Repo Integration Target

The repository mentioned in the chat is:

- `eva-whisper-chat`

The goal is to integrate the routing and agentic layers into that existing project instead of rewriting everything.

The system should be extended, not replaced.

The expected repo evolution is:

```text
existing whisper chat app
    ↓
model router
    ↓
agent system
    ↓
tool / skill layer
    ↓
personal assistant integrations
```

---

# 12. Proposed Directory Structure

A modular AI folder should be introduced.

```text
/src/ai/
  router.js
  memory.js
  intent.js
  agent/
    agent.js
    planner.js
    executor.js
  providers/
    ollama.js
    openrouter.js
    anthropic.js
  tools/
    fileTool.js
    shellTool.js
    webTool.js
    index.js
  integrations/
    social/
    productivity/
    communication/
    media/
```

This is the main structure that the assistant should analyze and populate.

---

# 13. Provider Layer

Each provider should be isolated and have a small, predictable interface.

Expected behavior:

- accept `messages[]`
- return a string response
- hide provider-specific details behind a common interface

Provider examples:

## Ollama Provider
Used for local model calls.

## OpenRouter Provider
Used for cloud model calls via OpenRouter’s unified API.

## Anthropic Provider
Used only as premium fallback where desired.

---

# 14. Router Layer

The router decides which provider to use.

Responsibilities:

- inspect prompt content
- detect task type
- pick local vs cloud vs premium
- handle provider failures
- provide fallback behavior
- log selected route

Suggested output from router:

- provider name
- model name
- reasoning for route selection

---

# 15. Memory Layer

Memory was discussed as a necessary part of the assistant.

It should store:

- recent messages
- conversation context
- user preferences
- task history

It should be:

- bounded in size
- easy to inject into prompts
- usable by both planner and agent loop

Future memory can be expanded into:

- preference memory
- task memory
- long-term profile memory
- embeddings / semantic memory

---

# 16. Intent Detection

The assistant should determine what kind of request the user made.

Possible intents:

- CHAT
- TASK
- ACTION
- SEARCH
- SOCIAL
- MEDIA
- PRODUCTIVITY
- COMMUNICATION

Example behavior:

- “explain this” → CHAT
- “build this feature” → TASK
- “open the file” → ACTION
- “find docs” → SEARCH
- “write a LinkedIn post” → SOCIAL
- “play music” → MEDIA
- “create slides” → PRODUCTIVITY
- “send WhatsApp message” → COMMUNICATION

---

# 17. Planner Layer

The planner should break a complex task into steps.

Example output format:

```json
{
  "steps": ["step1", "step2", "step3"]
}
```

The planner should:

- use the model when needed
- produce structured steps
- handle parsing failures gracefully
- degrade to a single-step plan if necessary

---

# 18. Executor Layer

The executor takes planned steps and runs them.

Responsibilities:

- map step to the right tool
- run the tool
- fallback to the model if no tool is applicable
- return results cleanly

The executor should be able to handle both:

- explicit tool steps
- normal model-generated responses

---

# 19. Agent Loop

The assistant should not be “one-shot only.”

It should run a loop:

```text
think → decide → act → observe → repeat
```

This was one of the strongest ideas in the chat.

The agent loop should:

- decide when to use a tool
- stop after max iterations
- handle failures
- continue until task completion or limit reached

A tool-call response format was discussed, such as:

```json
{
  "action": "tool_name",
  "input": {"...": "..."}
}
```

---

# 20. Tool / Skill System

The system should support modular tools and skills.

Every tool should follow a simple contract:

```js
{
  name: "tool_name",
  description: "what it does",
  execute: async (input) => string
}
```

This is the base pattern for the assistant’s action layer.

---

# 21. Core Tools Discussed

## File Tools
- read file
- write file
- inspect directory contents

## Shell Tools
- run command
- execute scripts
- invoke dev commands

## Web Tools
- fetch URLs
- inspect web content
- pull external knowledge when needed

## Repo Tools
- search codebase
- analyze files
- detect duplicates
- summarize code structure

---

# 22. Skills / “Superpowers” Concept

The chat discussed ideas inspired by repositories that focus on agent skills and power-user workflows.

The useful takeaway is not to copy everything, but to adopt the best patterns:

- modular skill system
- planning before execution
- code review stage
- task breakdown
- subagent style decomposition
- hooks for lifecycle actions
- on-demand knowledge loading
- repository-aware behavior

This turns tools into a reusable skill layer.

---

# 23. Advanced Agent Behaviors

The following behaviors were discussed as high-value additions:

## A. Brainstorm → Plan → Execute
Do not jump straight into code.

## B. Subagents
Use specialized mini-agents for tasks.

## C. Review Agent
Check results after execution.

## D. Test-Driven Development Flow
Generate tests first, then implement.

## E. Debugging Discipline
Avoid guessing. Diagnose root cause.

## F. Hooks
Add system hooks before and after tool usage.

---

# 24. Personal Assistant Expansion

The chat expanded beyond coding and into general life automation.

The assistant should eventually support:

- voice assistant behavior
- daily productivity tasks
- content creation
- app actions
- communication
- media control

This makes the system more like a **personal AI operating system**.

---

# 25. Social Media / Content Creation Work

The assistant should help with:

- Instagram
- YouTube
- LinkedIn
- X / Twitter

Useful capabilities:

- generate post drafts
- generate captions
- create thread ideas
- summarize content ideas
- help with content planning
- schedule content
- optionally post with confirmation

Important principle:

- do not auto-post blindly
- use human confirmation before publishing

---

# 26. Productivity / Docs / Slides

The assistant should support productivity tools such as:

- Google Docs
- Google Slides
- presentation generation
- document generation
- note creation
- structured write-ups

This is important because the assistant should not just answer questions; it should create deliverables.

---

# 27. Communication Work

The assistant should eventually help with communication tasks such as:

- WhatsApp messaging
- drafting replies
- sending messages with approval
- reminders and follow-ups

The chat noted that some platforms have limited direct API access, so this may require approved APIs, automation, or a human-in-the-loop flow.

---

# 28. Media Work

The assistant should also support media control and recommendations:

- Spotify
- Apple Music
- YouTube media workflows

Capabilities:

- play music
- pause music
- search songs
- generate playlists
- recommend tracks

---

# 29. Open-Ended Agentic Work

The assistant should be able to handle many kinds of action-oriented tasks, not just social or media.

Examples:

- coding work
- directory analysis
- file editing
- report generation
- workflow automation
- answering questions with action
- creating documents and slide decks
- operating tools based on intent

---

# 30. Human-in-the-Loop Rule

For risky or externally visible actions, the assistant should ask for confirmation.

Examples:

- posting on social media
- sending messages
- deleting files
- running shell commands
- modifying code in important places

The assistant should present a draft or plan first.

---

# 31. What Should Be Done First

The chat naturally split the project into phases.

## Phase 1
- model routing
- local + cloud provider layer
- basic memory
- Whisper integration

## Phase 2
- intent detection
- planning
- agent loop
- basic tools

## Phase 3
- social/media/productivity integrations
- stronger memory
- subagents
- review loops

## Phase 4
- polished personal assistant behavior
- broader automation
- advanced workflows

---

# 32. What Is Already Implemented vs What Is Missing

This section is meant to help Qwen / Qwen-Coder analyze the repo.

## Likely Already Done
- Whisper transcription flow
- basic chat interface
- some model routing logic
- basic provider abstraction
- initial memory handling

## Partially Done
- basic tool support
- basic agent scaffolding
- some integration planning

## Still Needed
- complete planner
- full executor
- intent detection layer
- robust fallback strategy
- tool registry and skill system
- integration modules
- subagent architecture
- reflection / review loop
- human approval flow
- polished memory layer

---

# 33. Recommended Folder Map for the Final System

```text
/docs/
  AI_SYSTEM.md
/src/
  ai/
    router.js
    memory.js
    intent.js
    agent/
      agent.js
      planner.js
      executor.js
    providers/
      ollama.js
      openrouter.js
      anthropic.js
    tools/
      fileTool.js
      shellTool.js
      webTool.js
      index.js
    integrations/
      social/
      productivity/
      communication/
      media/
```

This is the kind of layout the repo should move toward.

---

# 34. Desired Output From Qwen / Qwen-Coder

The assistant should be asked to analyze the repo and return:

```json
{
  "implemented": [],
  "missing": [],
  "improvements": [],
  "next_steps": []
}
```

This makes it easier to compare the current codebase with the target architecture.

---

# 35. Good Questions To Ask the Code Analyzer

Use prompts such as:

- What parts of the architecture already exist?
- What folders/files are missing?
- Which modules should be added first?
- Which components are coupled too tightly?
- What can be safely refactored without breaking current behavior?
- Where should the agent layer be inserted?
- What integrations are realistic now versus later?
- What is the best incremental roadmap from the current repo state?

---

# 36. Implementation Principles

The build should follow these rules:

- keep code modular
- do not rewrite the whole app
- do not break Whisper
- use environment variables for secrets
- prefer local models first
- keep cloud as fallback
- keep tools isolated
- keep agent logic readable
- ask for confirmation before risky actions
- prefer correctness over cleverness

---

# 37. Final Project Identity

The final system is best described as:

> **A personal AI operating system with voice input, model routing, planning, tool execution, and multi-domain agentic capabilities.**

This is the direction the