import json
import os
import yaml
from typing import List

from custom_agent.model_wrapper import ModelWrapper
from custom_agent.py_agent import PyAgent
from smolagents.agents import populate_template
from castle.game_objects import game_functions, GameObject


class CastleAgent(PyAgent):
    def __init__(self, model, debug_mode=True, code_state=None):
        super().__init__(model, debug_mode, code_state)
        # we will overwrite code_state in run_battle_command
    
    def create_system_prompt(self):
       # overwrite
       yaml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'castle_agent.yaml')
       with open(yaml_path, 'r') as file:
            templates = yaml.safe_load(file)
       self.system_prompt = populate_template(
           templates["system_prompt"],
           variables={
               'in_game_commands': game_functions
           },
       )
    
    def run_battle_command(self, game_objects: List[GameObject], user_request: str):
        # this is a wrapper of self.run()
        # user_request = 'All units attack enemy castle'
        code_state = {
            'battle_state': [i.__dict__ for i in game_objects]
        }
        prompt_frame = '''This is the current battleground state:
        battle_state = {battle-state}

        As a reminder, these are the in-game commands that you have access to:
        <commands>
        {tool-text}
        </commands>

        Please provide the command(s) for my request:
        {user-request}
        '''
        user_prompt = prompt_frame\
            .replace('{battle-state}', json.dumps(code_state["battle_state"], indent=2))\
            .replace('{user-request}', user_request)\
            .replace('{tool-text}', json.dumps(game_functions, indent=2))
        
        # set code state and run
        self.code_state = code_state
        return self.run(user_prompt)

def get_model():
    max_seq_length = 8192
    model_names = [
        'unsloth/Qwen2.5-3B-Instruct-unsloth-bnb-4bit',
        'unsloth/Qwen2.5-7B-Instruct-bnb-4bit',
        # 'unsloth/Llama-3.2-1B-Instruct-unsloth-bnb-4bit'  # definitely worse than qwen2.5 - 3b
        'unsloth/Qwen2.5-Coder-1.5B-Instruct-bnb-4bit',
        'unsloth/Qwen2.5-Coder-3B-Instruct-bnb-4bit',
        'unsloth/Qwen2.5-Coder-3B-Instruct-bnb-4bit',
        # 'unsloth/Qwen2.5-3B-Instruct-bnb-4bit',
    ]
    model_name = model_names[0]
    model = ModelWrapper(
        model_id=model_name,
        max_seq_length=max_seq_length
    )
    return model