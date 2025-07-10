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

async def run_agent_task(user_input: str, session_messages: list, model: str = "claude-opus-4-20250514", websocket=None):
    print(f"[AGENT] Starting run_agent_task with user_input: {user_input}")
    print(f"[AGENT] Session messages count: {len(session_messages)}")
    print(f"[AGENT] WebSocket provided: {websocket is not None}")
    
    result_blocks = []
    websocket_tasks = []

    async def main():
        messages = to_agent_messages(session_messages) + [
            {"role": "user", "content": [{"type": "text", "text": user_input}]}
        ]
        print(f"[AGENT] Total messages for API call: {len(messages)}")

        def output_callback(block):
            print(f"[AGENT] OUTPUT_CALLBACK - Block received: {block}")
            if block["type"] == "text" and block.get("text"):
                result_blocks.append(block["text"])
                print(f"[AGENT] Added text block to result_blocks. Total blocks: {len(result_blocks)}")
                # Send over WebSocket if available
                if websocket:
                    print(f"[AGENT] Creating WebSocket task for text block")
                    # Create task and store it
                    task = asyncio.create_task(send_websocket_block(websocket, block))
                    websocket_tasks.append(task)
                    print(f"[AGENT] WebSocket task created. Total tasks: {len(websocket_tasks)}")
            elif block["type"] == "tool_use":
                # Optionally, append tool_use info
                result_blocks.append(f"[TOOL USE] {block['name']}: {block['input']}")
                print(f"[AGENT] Added tool_use block to result_blocks. Total blocks: {len(result_blocks)}")
                # Send over WebSocket if available
                if websocket:
                    print(f"[AGENT] Creating WebSocket task for tool_use block")
                    task = asyncio.create_task(send_websocket_block(websocket, block))
                    websocket_tasks.append(task)
                    print(f"[AGENT] WebSocket task created. Total tasks: {len(websocket_tasks)}")
            elif block["type"] == "tool_result":
                # If you ever get tool_result blocks directly
                result_blocks.append(str(block))
                print(f"[AGENT] Added tool_result block to result_blocks. Total blocks: {len(result_blocks)}")
                # Send over WebSocket if available
                if websocket:
                    print(f"[AGENT] Creating WebSocket task for tool_result block")
                    task = asyncio.create_task(send_websocket_block(websocket, block))
                    websocket_tasks.append(task)
                    print(f"[AGENT] WebSocket task created. Total tasks: {len(websocket_tasks)}")


        tool_version = "computer_use_20250429"
        print(f"[AGENT] Using tool version: {tool_version}")


        def tool_output_callback(result, block_id): 
            print(f"[AGENT] TOOL_OUTPUT_CALLBACK - Tool {block_id} completed with result: {result}")
            # Send tool result over WebSocket if available
            if websocket:
                tool_result_block = {
                    "type": "tool_result",
                    "tool_use_id": block_id,
                    "result": result
                }
                print(f"[AGENT] Creating WebSocket task for tool_result block with ID: {block_id}")
                task = asyncio.create_task(send_websocket_block(websocket, tool_result_block))
                websocket_tasks.append(task)
                print(f"[AGENT] WebSocket task created for tool_result. Total tasks: {len(websocket_tasks)}")
        def api_response_callback(request, response, exc): 
            if exc:
                print(f"[AGENT] API_ERROR: {exc}")
            else:
                print(f"[AGENT] API_SUCCESS: {response.status_code if response else 'No response'}")

        print(f"[AGENT] Starting sampling_loop...")
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
        print(f"[AGENT] sampling_loop completed")

    await main()
    
    # Wait for all WebSocket tasks to complete
    if websocket_tasks:
        print(f"[AGENT] Waiting for {len(websocket_tasks)} WebSocket tasks to complete...")
        await asyncio.gather(*websocket_tasks, return_exceptions=True)
        print(f"[AGENT] All WebSocket tasks completed")
    else:
        print(f"[AGENT] No WebSocket tasks to wait for")
    
    final_result = "\n".join(result_blocks)
    print(f"[AGENT] Final result length: {len(final_result)} characters")
    print(f"[AGENT] Final result preview: {final_result[:100]}...")
    
    return final_result

async def send_websocket_block(websocket, block):
    """Helper function to send a block over WebSocket with proper error handling"""
    print(f"[WEBSOCKET] Attempting to send block: {block}")
    try:
        await websocket.send_json(block)
        print(f"[WEBSOCKET] Successfully sent block: {block.get('type', 'unknown')}")
    except Exception as e:
        print(f"[WEBSOCKET] Send error: {e}")
        # Don't raise the exception, just log it
