def read_file(file_path):
    """Read the content of a specified file"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def write_to_file(file_path, content):
    """Write content to a specified file"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content.replace("\\n", "\n"))
    return "Write success"

def run_terminal_command(command):
    """Run a terminal command and return its output or error message"""
    import subprocess
    run_result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if run_result.returncode == 0:
        return "Execution success" 
    else:
        return "Execution failed: " + run_result.stderr

