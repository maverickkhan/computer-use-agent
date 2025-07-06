from enum import Enum
from typing import Literal


# class ToolVersion(Enum):
#     COMPUTER_USE_20250124 = "computer_use_20250124"
#     COMPUTER_USE_20241022 = "computer_use_20241022"
#     COMPUTER_USE_20250429 = "computer_use_20250429"

ToolVersion = Literal[
    "computer_use_20250124",
    "computer_use_20241022",
    "computer_use_20250429",
]

class ToolGroup:
    def __init__(self):
        self.tools = []  # Put tool classes here later
        self.beta_flag = None

# TOOL_GROUPS_BY_VERSION = {
#     ToolVersion.COMPUTER_USE_20250124: ToolGroup(),
#     ToolVersion.COMPUTER_USE_20241022: ToolGroup(),
#     ToolVersion.COMPUTER_USE_20250429: ToolGroup(),
# }

TOOL_GROUPS_BY_VERSION = {
    "computer_use_20250124": ToolGroup(),
    "computer_use_20241022": ToolGroup(),
    "computer_use_20250429": ToolGroup(),
}

class ToolCollection:
    def __init__(self, *args, **kwargs): pass
    def to_params(self): return []
    async def run(self, name, tool_input): 
        print(f"ToolCollection.run called with name={name} and tool_input={tool_input}")
        return ToolResult()

class ToolResult:
    def __init__(self):
        self.error = None
        self.output = "Hello! Backend is working."
        self.base64_image = None
        self.system = None
