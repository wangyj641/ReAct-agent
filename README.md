# ReAct agent for generating source code

Implement a simple agent to generate source code automatically.

### Set AI model environment

Here, I use github model which it is free

```
GITHUB_MODEL_TOKEN=xxx
GITHUB_API_BASE_URL=xxx
GITHUB_MODEL=xxx
```

### Start App

Start agent and input your project path

```bash
uv run agent.py {your project path}
```

Then, tell agent what you want it to do, Such as developing a card game.
Fox example:

```bash
uv run agent.py .source/card_gname
Input your task：Develop a card game with C++ programing language

```

You will get card game source code in the project directory you input
