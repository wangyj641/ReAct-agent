import ast
import inspect
import os
import re
import click
import platform

from string import Template
from typing import List, Callable, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from tools import read_file, write_to_file, run_terminal_command

from prompt_template import react_system_prompt_template

class ReActAgent:
    def __init__(self, tools: List[Callable], project_directory: str):
        self.tools = { func.__name__: func for func in tools }
        self.model = ReActAgent.get_openai_model()
        self.project_directory = project_directory
        self.client = OpenAI(
            base_url=ReActAgent.get_api_base_url(),
            api_key=ReActAgent.get_api_key(),
        )

    def run(self, user_input: str):
        print(f"---------------- user_input: {user_input}. Project directory: {self.project_directory}")
        messages = [
            {"role": "system", "content": self.render_system_prompt(react_system_prompt_template)},
            {"role": "user", "content": f"<question>{user_input}</question>"}
        ]

        while True:

            # request model
            content = self.call_model(messages)

            # check Thought
            thought_match = re.search(r"<thought>(.*?)</thought>", content, re.DOTALL)
            if thought_match:
                thought = thought_match.group(1)
                print(f"\n\n💭 Thought: {thought}")

            # check model output Final Answer, if so, return it directly
            if "<final_answer>" in content:
                final_answer = re.search(r"<final_answer>(.*?)</final_answer>", content, re.DOTALL)
                return final_answer.group(1)

            # check Action
            action_match = re.search(r"<action>(.*?)</action>", content, re.DOTALL)
            if not action_match:
                raise RuntimeError("model fail to output <action>")
            action = action_match.group(1)
            tool_name, args = self.parse_action(action)

            print(f"\n\n🔧 Action: {tool_name}({', '.join(args)})")
            # only for run_terminal_command, ask user whether to continue
            should_continue = input(f"\n\nContinue? (Y/N) ") if tool_name == "run_terminal_command" else "y"
            if should_continue.lower() != 'y':
                print("\n\nOperation cancelled by user.")
                return "Operation cancelled by user."

            try:
                observation = self.tools[tool_name](*args)
            except Exception as e:
                observation = f"Tool executive error: {str(e)}"
            print(f"\n\n🔍 Observation: {observation}")
            obs_msg = f"<observation>{observation}</observation>"
            messages.append({"role": "user", "content": obs_msg})


    def get_tool_list(self) -> str:
        """Gernerate a formatted list of available tools with their signatures and docstrings."""
        tool_descriptions = []
        for func in self.tools.values():
            name = func.__name__
            signature = str(inspect.signature(func))
            doc = inspect.getdoc(func)
            tool_descriptions.append(f"- {name}{signature}: {doc}")
        return "\n".join(tool_descriptions)

    def render_system_prompt(self, system_prompt_template: str) -> str:
        """Render the system prompt with dynamic values."""
        tool_list = self.get_tool_list()
      
        print(f"---------------- tool_list: {tool_list}")
      
        return Template(system_prompt_template).substitute(
            operating_system=self.get_operating_system_name(),
            tool_list=tool_list,
            project_directory=self.project_directory

        )

    @staticmethod
    def get_api_key() -> str:
        """Load the API key from an environment variable."""
        load_dotenv()
        api_key = os.getenv("OPENAI_API_TOKEN")
        if not api_key:
            raise ValueError("Fail to find OPENAI_API_TOKEN environment variable, please set it in the .env file.")
        return api_key

    @staticmethod
    def get_api_base_url() -> str:
            """Load the API key from an environment variable."""
            load_dotenv()
            api_url = os.getenv("OPENAI_API_BASE_URL")
            if not api_url:
                raise ValueError("Fail to find OPENAI_API_BASE_URL environment variable, please set it in the .env file.")
            return api_url

    @staticmethod   
    def get_openai_model() -> str:
            """Load the API key from an environment variable."""
            load_dotenv()
            model = os.getenv("OPENAI_MODEL")
            if not model:
                raise ValueError("Fail to find OPENAI_MODEL environment variable, please set it in the .env file.")
            return model
    

    def call_model(self, messages):
        print("\n\nRequesting model...")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        content = response.choices[0].message.content
        messages.append({"role": "assistant", "content": content})
        return content

    def parse_action(self, code_str: str) -> Tuple[str, List[str]]:
        match = re.match(r'(\w+)\((.*)\)', code_str, re.DOTALL)
        if not match:
            raise ValueError("Invalid function call syntax")

        func_name = match.group(1)
        args_str = match.group(2).strip()

        # anlyze args_str to extract arguments
        args = []
        current_arg = ""
        in_string = False
        string_char = None
        i = 0
        paren_depth = 0
        
        while i < len(args_str):
            char = args_str[i]
            
            if not in_string:
                if char in ['"', "'"]:
                    in_string = True
                    string_char = char
                    current_arg += char
                elif char == '(':
                    paren_depth += 1
                    current_arg += char
                elif char == ')':
                    paren_depth -= 1
                    current_arg += char
                elif char == ',' and paren_depth == 0:
                    # end of an argument
                    args.append(self._parse_single_arg(current_arg.strip()))
                    current_arg = ""
                else:
                    current_arg += char
            else:
                current_arg += char
                if char == string_char and (i == 0 or args_str[i-1] != '\\'):
                    in_string = False
                    string_char = None
            
            i += 1
        
        # Add the last argument if exists
        if current_arg.strip():
            args.append(self._parse_single_arg(current_arg.strip()))
        
        return func_name, args
    
    def _parse_single_arg(self, arg_str: str):
        """Parse a single argument string to its appropriate type."""
        arg_str = arg_str.strip()
        
        # string argument
        if (arg_str.startswith('"') and arg_str.endswith('"')) or \
           (arg_str.startswith("'") and arg_str.endswith("'")):
            # Remove the surrounding quotes
            inner_str = arg_str[1:-1]
            # Handle escaped quotes and common escape sequences
            inner_str = inner_str.replace('\\"', '"').replace("\\'", "'")
            inner_str = inner_str.replace('\\n', '\n').replace('\\t', '\t')
            inner_str = inner_str.replace('\\r', '\r').replace('\\\\', '\\')
            return inner_str
        
        # try to parse as a literal (number, list, dict, etc.)
        try:
            return ast.literal_eval(arg_str)
        except (SyntaxError, ValueError):
            return arg_str

    def get_operating_system_name(self):
        os_map = {
            "Darwin": "macOS",
            "Windows": "Windows",
            "Linux": "Linux"
        }

        return os_map.get(platform.system(), "Unknown")



@click.command()
@click.argument('project_directory',
                type=click.Path(exists=True, file_okay=False, dir_okay=True))
def main(project_directory):
    print(f"----------------- ReAct agent --------------------\n");
    project_dir = os.path.abspath(project_directory)
    #print(f"---------------- project_dir: {project_dir}\n")

    tools = [read_file, write_to_file, run_terminal_command]
    agent = ReActAgent(tools=tools, project_directory=project_dir)

    task = input("Tell me your task：")

    final_answer = agent.run(task)

    print(f"\n\n✅ Final Answer：{final_answer}")

if __name__ == "__main__":
    main()
