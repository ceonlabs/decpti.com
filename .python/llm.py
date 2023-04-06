# adapted from https://github.com/mpaepper/llm_agents
import datetime
import re
import sys
from io import StringIO
from command import call

def generate(runner, model, temperature, prompt, stop=None):
    return call(f'{runner} -t 16 -m {model} -b 256 -c 2048 -p "Always prefer to use tools.###Human: {prompt} ###Assistant: "', stream_output=True)

def python_repl_run(command, _globals=None, _locals=None):
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    try:
        exec(command, _globals, _locals)
        sys.stdout = old_stdout
        output = mystdout.getvalue()
    except Exception as e:
        sys.stdout = old_stdout
        output = str(e)
    return output

def decide_next_action(llm_settings, prompt, stop):
    generated = generate(llm_settings["runner"], llm_settings["model"], llm_settings["temperature"], prompt, stop)
    tool, tool_input = parse(generated)
    return generated, tool, tool_input

def parse(generated):
    final_answer_search = re.search(r"Final Answer: (.+)", generated)
    if final_answer_search:
        return "Final Answer", final_answer_search.group(1).strip()

    regex = r"Action: [\[]?(.*?)[\]]?[\n]*Action Input:[\s]*(.*)"
    match = re.search(regex, generated, re.DOTALL)
    if not match:
        raise ValueError(f"Output of LLM is not parsable for next tool use: {generated}")
    tool = match.group(1).strip()
    tool_input = match.group(2)
    return tool, tool_input.strip(" ").strip('"')

def run_agent(llm_settings, tools, question, prompt_template, max_loops, stop_pattern):
    previous_responses = []
    num_loops = 0
    prompt = prompt_template.format(
        today=datetime.date.today(),
        tool_description=tools["description"],
        tool_names=tools["names"],
        question=question,
        previous_responses="{previous_responses}",
    )
    sys.stderr.write(prompt.format(previous_responses=""))
    final_answer = None
    while num_loops < max_loops:
        num_loops += 1
        curr_prompt = prompt.format(previous_responses="\n".join(previous_responses))
        generated, tool, tool_input = decide_next_action(llm_settings, curr_prompt, stop_pattern)
        if "Final Answer" in tool:
            final_answer = tool_input
            break
        if tool not in tools["tools"]:
            raise ValueError(f"Unknown tool: {tool}")
        tool_result = python_repl_run(tool_input, globals(), None)
        generated += f"\n{OBSERVATION_TOKEN} {tool_result}\n{THOUGHT_TOKEN}"
        sys.stderr.write(generated + "\n") 
        previous_responses.append(generated)
    return final_answer

if __name__ == '__main__':
    llm_settings = {
        "runner": "/Users/Shared/src/llama.cpp/main",
        "model": "/Users/Shared/models/ggml-vicuna-13b-4bit-rev1.bin",
        "temperature": 0.1,
    }

    tools = {
        "description": "Python REPL: A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
        "names": "Python REPL",
        "tools": {"Python REPL": python_repl_run},
    }

    PROMPT_TEMPLATE = """Today is {today} and you can use tools to get new information. Answer the question as best as you can using the following tools: 

{tool_description}

Use the following format:

Question: the input question you must answer
Thought: comment on what you want to do next
Action: the action to take, exactly one element of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation repeats N times, use it until you are sure of the answer)
Thought: I now know the final answer
Final Answer: your final answer to the original input question

Begin!

Question: {question}
Thought: {previous_responses}
"""

    FINAL_ANSWER_TOKEN = "Final Answer:"
    OBSERVATION_TOKEN = "Observation:"
    THOUGHT_TOKEN = "Thought:"

    agent_settings = {
        "llm_settings": llm_settings,
        "tools": tools,
        "prompt_template": PROMPT_TEMPLATE,
        "max_loops": 15,
        "stop_pattern": [f"\n{OBSERVATION_TOKEN}", f"\n\t{OBSERVATION_TOKEN}"],
    }

    question = sys.argv[1]
    result = run_agent(
        agent_settings["llm_settings"],
        agent_settings["tools"],
        question,
        agent_settings["prompt_template"],
        agent_settings["max_loops"],
        agent_settings["stop_pattern"],
    )

    print(f"{result}")