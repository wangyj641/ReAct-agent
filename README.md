# ReAct agent Code assistant

A ReAct agent to help you coding. It will generate source code automatically according to your request

### Set AI model environment

Here, I use github model which it is free

```
GITHUB_MODEL_TOKEN=xxx
GITHUB_API_BASE_URL=xxx
GITHUB_MODEL=xxx
```

### Start App

Start agent

```bash
uv run agent.py
```

Then, tell agent what you want it to do, Such as developing a card game.
Fox example:

```bash
uv run agent.py
Input your task：Develop a card game with C++ programing language

```

You will get card game source code in directory

```bash
.source
```
