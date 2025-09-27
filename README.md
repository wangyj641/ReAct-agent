# ReAct agent for generating source code

### Install uv

https://docs.astral.sh/uv/getting-started/installation/

### Set AI model environment：

```
GITHUB_MODEL_TOKEN=xxx
GITHUB_API_BASE_URL=xxx
GITHUB_MODEL=xxx
```

### Start agent

Input your project path

```bash
uv run agent.py {your project path}
```

Then, input your task. You will get project source code in your specified path.
Fox example:

```bash
uv run agent.py .source/card_gname
请输入任务：使用c++, 编写一个card game游戏

```
