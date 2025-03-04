import yaml
import time
from rich.text import Text
from rich.rule import Rule
from rich.panel import Panel
from rich.console import Group
import os
import traceback



from smolagents.memory import AgentMemory, TaskStep, ActionStep, MemoryStep, ToolCall
from smolagents.agents import populate_template
from smolagents.monitoring import LogLevel, AgentLogger, YELLOW_HEX
from smolagents.utils import AgentError, AgentExecutionError, AgentGenerationError, AgentMaxStepsError, AgentParsingError, parse_code_blobs, truncate_content
from smolagents.local_python_executor import (
   BASE_BUILTIN_MODULES,
   LocalPythonInterpreter,
   fix_final_answer_code,
)


# this is my adaptation of CodeAgent from SmolAgent
# will be inherited by CastleAgent for this project
# "model" param is actually the ModelWrapper that we defined
# usage:
# agent = PyAgent(model)
# agent.run('What is the date today?')
# see the log:
# agent.memory.replay(detailed=True)
# - also, default PyAgent(debug_mode=True) option should have active logging



class PyAgent:
   def __init__(self, model, debug_mode=True, code_state=None):
        self.model = model

        # tools and managed_agents can be added, similar to CodeAgent
        self.tools = {}
        self.managed_agents = {}
        self.all_tools = {**self.tools, **self.managed_agents}
        self.create_system_prompt()

        self.additional_authorized_imports = [] # List[str] if specified
        self.code_state = code_state or dict() # to store variables
        self.python_executor = LocalPythonInterpreter(
            self.additional_authorized_imports,
            self.all_tools,
            max_print_outputs_length=None,
        )


        # replayer from smolagents
        self.memory = AgentMemory(self.system_prompt)
        self.logger = AgentLogger(
            level=LogLevel.DEBUG if debug_mode else LogLevel.INFO)


   def run(self, task: str, task_images=None, step_max=6, final_answer_checks=None):
       # final_answer_checks: validator functions go here (final_answer, memory) => bool


       task_step = TaskStep(task=task, task_images=task_images)
       self.memory.steps.append(task_step)


       final_answer = None
       step_num = 1
       # iterate until we get final answer
       # intermediate actions will be added to memory.steps
       while final_answer is None and step_num < step_max:
           # timing
           ts_start = time.time()
           action = ActionStep(
               step_number=step_num,
               start_time=ts_start,
               observations_images=task_images
           )  # they call this memory_step
           try:
               # planning would go here; we skip
               self.logger.log_rule(f"Step {step_num}", level=LogLevel.INFO)


               # step forward
               final_answer = self.step(action)
               if final_answer is not None and final_answer_checks:
                   for check_function in final_answer_checks:
                       try:
                           assert check_function(final_answer, self.memory)
                       except Exception as e:
                           final_answer = None
                           raise AgentError(
                               f"Check {check_function.__name__} failed with error: {e}", self.logger)
           except AgentError as e:
               action.error = e
           finally:
               action.end_time = time.time()
               action.duration = action.end_time - ts_start
               self.memory.steps.append(action)  # add to our memory
               step_num += 1


       if final_answer is None:
           print(f'No answer after {step_max - 1} steps')
       return final_answer
   
   def create_system_prompt(self):
       # overwrite this to load a different system prompt
       yaml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'code_agent.yaml')
       with open(yaml_path, 'r') as file:
            templates = yaml.safe_load(file)

       # extra params: pass in if needed in future
       self.authorized_imports = 'None'  
       # for executor; use if we want to add imports later
       self.system_prompt = populate_template(
           templates["system_prompt"],
           variables={
               "tools": self.tools,
               "managed_agents": self.managed_agents,
               "authorized_imports": (
                   "You can import from any package you want."
                   if "*" in self.authorized_imports
                   else str(self.authorized_imports)
               ),
           },
       )


   def get_messages(self, summary_mode=False):
       # helper, called once currently; smolagents may call more in future
       messages = self.memory.system_prompt.to_messages(
           summary_mode=summary_mode)
       for memory_step in self.memory.steps:
           messages.extend(memory_step.to_messages(summary_mode=summary_mode))
       return messages


   def step(self, action: MemoryStep):
       # 1. create model input
       messages = self.get_messages()
       action.model_input_messages = messages.copy()


       # 2. get model response
       try:
           ###################################
           # call the actual model! big stuff
           ###################################
           response = self.model(
               messages,
                stop_sequences=["<end_code>", "Observation:"],
           )
           action.model_output_message = response
           action.model_output = response.content
       except Exception as e:
           print('full traceback', traceback.format_exc())
           raise AgentGenerationError(
               f"Error in generating model output:\n{e}", self.logger) from e

       self.logger.log_markdown(
           content=response.content,
           title='LLM Output message:',
           level=LogLevel.DEBUG
       )

       # 3. Expect model to output python code. Parse it here
       try:
           code_action = fix_final_answer_code(
               parse_code_blobs(response.content))
       except Exception as e:
           error_msg = f"Error in code parsing:\n{e}\nMake sure to provide correct code blobs."
           raise AgentParsingError(error_msg, self.logger)
       action.tool_calls = [
           ToolCall(
               name="python_interpreter",
               arguments=code_action,
               id=f"call_{len(self.memory.steps)}",
           )
       ]

       # 4. Execute python code as requested by model
       self.logger.log_code(title="Executing parsed code:",
                            content=code_action, level=LogLevel.INFO)
       is_final_answer = False
       try:
           output, execution_logs, is_final_answer = self.python_executor(
               code_action,
               self.code_state,
           )
           execution_outputs_console = []
           if len(execution_logs) > 0:
               execution_outputs_console += [
                   Text("Execution logs:", style="bold"),
                   Text(execution_logs),
               ]
           observation = "Execution logs:\n" + execution_logs
       except Exception as e:
           if hasattr(self.python_executor, "state") and "_print_outputs" in self.python_executor.state:
               execution_logs = str(
                   self.python_executor.state["_print_outputs"])
               if len(execution_logs) > 0:
                   execution_outputs_console = [
                       Text("Execution logs:", style="bold"),
                       Text(execution_logs),
                   ]
                   action.observations = "Execution logs:\n" + execution_logs
                   self.logger.log(
                       Group(*execution_outputs_console), level=LogLevel.INFO)
           error_msg = str(e)
           if "Import of " in error_msg and " is not allowed" in error_msg:
               self.logger.log(
                   "[bold red]Warning to user: Code execution failed due to an unauthorized import - Consider passing said import under `additional_authorized_imports` when initializing your CodeAgent.",
                   level=LogLevel.INFO,
               )
           raise AgentExecutionError(error_msg, self.logger)
       truncated_output = truncate_content(str(output))
       observation += 'Last output from code snippet:\n' + truncated_output
       action.observations = observation

       # 5. check if final answer exists
       execution_outputs_console += [
           Text(
               f"{('Out - Final answer' if is_final_answer else 'Out')}: {truncated_output}",
               style=(f"bold {YELLOW_HEX}" if is_final_answer else ""),
           ),
       ]
       self.logger.log(Group(*execution_outputs_console), level=LogLevel.INFO)
       action.action_output = output
       return output if is_final_answer else None





