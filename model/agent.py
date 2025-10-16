from typing import Callable, Dict

class AgentTool:
    def __init__(self, name: str, description: str, parameters: Dict, function: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.function = function
