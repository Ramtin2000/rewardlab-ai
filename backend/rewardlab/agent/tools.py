"""Tool schemas shown to the model (OpenAI-style function calling format).

The model only sees these descriptions. Our code executes the call via
SupportEnv.step(). Keep names in sync with rewardlab.env.TOOL_NAMES.
"""


def _tool(name: str, description: str, param: str, param_desc: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {param: {"type": "integer", "description": param_desc}},
                "required": [param],
            },
        },
    }


TOOL_SCHEMAS = [
    _tool("lookup_ticket", "Get a support ticket's details and complaint.", "ticket_id", "Ticket ID"),
    _tool("lookup_order", "Get an order's status and amount.", "order_id", "Order ID"),
    _tool("lookup_payment", "Get the payment status for an order.", "order_id", "Order ID"),
    _tool("issue_refund", "Refund the payment for an order.", "order_id", "Order ID"),
    _tool("close_ticket", "Mark a support ticket as resolved.", "ticket_id", "Ticket ID"),
]
