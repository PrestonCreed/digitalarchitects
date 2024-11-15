from ..base_tool import Tool
from ...core.websocketManager import WebSocketClientManager

place_model_tool = Tool(
    name="place_model_tool",
    supported_tasks=["place_model"],
    requires_unity_action=True,
    unity_action_type="place_model",
    requirements={
        'model_name': 'str',
        'position': 'dict',
        'rotation': 'dict'
    }
)