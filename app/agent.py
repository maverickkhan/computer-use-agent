from dotenv import load_dotenv
load_dotenv()
import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../computer-use-demo/computer_use_demo")))

from loop import sampling_loop, APIProvider

from tools import TOOL_GROUPS_BY_VERSION, ToolVersion, ToolCollection, ToolResult
print("Tool groups loaded:", TOOL_GROUPS_BY_VERSION)


ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def to_agent_messages(messages):
    """
    Convert DB message list to Anthropic format.
    messages: list of {"role": ..., "content": ...}
    Returns list of BetaMessageParam
    """
    agent_msgs = []

    for m in messages:
        content_text = m["content"].strip()
        if not content_text:
            continue
        # Accept only user/assistant roles, or map your "agent" role to "assistant"
        if m["role"] == "agent":
            role = "assistant"
        elif m["role"] in ("user", "assistant"):
            role = m["role"]
        else:
            continue  # Skip any others!
        agent_msgs.append({"role": role, "content": [{"type": "text", "text": m["content"]}]})
    return agent_msgs

async def run_agent_task_stream(user_input: str, session_messages: list, model: str = "claude-opus-4-20250514"):
    messages = to_agent_messages(session_messages) + [
        {"role": "user", "content": [{"type": "text", "text": user_input}]}
    ]

    # Define the callback that will yield blocks to the caller
    queue = asyncio.Queue()

    def output_callback(block):
        asyncio.create_task(queue.put(block))

    def tool_output_callback(result, block_id): pass
    def api_response_callback(request, response, exc):
        if exc:
            print(f"API ERROR: {exc}")
        else:
            print(f"API SUCCESS: {response.status_code if response else 'No response'}")

    async def agent_loop():
        await sampling_loop(
            model=model,
            provider=APIProvider.ANTHROPIC,
            system_prompt_suffix="",
            messages=messages,
            output_callback=output_callback,
            tool_output_callback=tool_output_callback,
            api_response_callback=api_response_callback,
            api_key=ANTHROPIC_API_KEY,
            tool_version="computer_use_20250429",
        )
        await queue.put(None)

    asyncio.create_task(agent_loop())

    # Yield events as they come in
    while True:
        block = await queue.get()
        if block is None:
            break
        yield block

async def run_agent_task(user_input: str, session_messages: list, model: str = "claude-opus-4-20250514"):
    result_blocks = []

    async def main():
        messages = to_agent_messages(session_messages) + [
            {"role": "user", "content": [{"type": "text", "text": user_input}]}
        ]

        def output_callback(block):
            print("BLOCK:", block)
            if block["type"] == "text" and block.get("text"):
                result_blocks.append(block["text"])
            elif block["type"] == "tool_use":
                # Optionally, append tool_use info
                result_blocks.append(f"[TOOL USE] {block['name']}: {block['input']}")
            elif block["type"] == "tool_result":
                # If you ever get tool_result blocks directly
                result_blocks.append(str(block))


        tool_version = "computer_use_20250429"


        def tool_output_callback(result, block_id): pass
        def api_response_callback(request, response, exc): 
            if exc:
                print(f"API ERROR: {exc}")
            else:
                print(f"API SUCCESS: {response.status_code if response else 'No response'}")

        await sampling_loop(
            model=model,
            provider=APIProvider.ANTHROPIC,
            system_prompt_suffix="",
            messages=messages,
            output_callback=output_callback,
            tool_output_callback=tool_output_callback,
            api_response_callback=api_response_callback,
            api_key=ANTHROPIC_API_KEY,
            tool_version=tool_version,
        )

    await main()
    return "\n".join(result_blocks)
