import os
from typing import TypedDict, Annotated, Sequence, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage, ToolMessage
from langgraph.graph.message import add_messages
from groq import Groq
import json
import logging

from agent.tools import tools_list

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State definition
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# System prompt outlining the role of the LangGraph agent in managing HCP interactions
SYSTEM_PROMPT = """You are an AI-first CRM Orchestrator helper for pharmaceutical and life science sales representatives.
Your task is to manage Healthcare Professional (HCP) interactions.
You have access to 5 tools:
1. `get_hcp_profile(name_query)`: Retrieve contact details, NPI, specialty, sentiment trends, and past interactions. Always use this first if you need an HCP's ID.
2. `log_interaction(hcp_id, interaction_type, notes, sentiment, products_discussed, outcome, next_steps, date_str)`: Log a new interaction.
3. `edit_interaction(interaction_id, interaction_type, notes, sentiment, products_discussed, outcome, next_steps, date_str)`: Edit files of a previously logged interaction.
4. `schedule_followup(hcp_id, task_description, days_from_now, due_date_str, priority, interaction_id)`: Setup an actionable item or reminder.
5. `search_interactions(query, hcp_id, product_name)`: Search past records for feedback or discussion points.

CRITICAL Guidelines:
1. When calling a tool, DO NOT output any conversational text, explanations, or summaries. Your response must contain ONLY the tool call itself.
2. Only output a conversational response/summary when you are NOT calling any tools (i.e. once the tool results are back and you are summarizing the outcome).
3. Do not try to write json strings in your response text. Use the tool calling capability directly.
4. If you need to find an HCP's profile and then log/create something, first call `get_hcp_profile`. Once the tool returns the profile data, you will receive another turn to call `log_interaction` or other tools. Do not attempt to run multiple dependent steps in a single response turn.
"""

# Map tools list by name
tools_by_name = {tool.name: tool for tool in tools_list}

# Convert LangChain tools into Groq API tool specifications
groq_tools = []
for tool in tools_list:
    groq_tools.append({
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.args_schema.schema() if hasattr(tool, "args_schema") and tool.args_schema else {
                "type": "object",
                "properties": {}
            }
        }
    })

# Node functions
def call_model(state: AgentState) -> Dict[str, Any]:
    """
    Sends conversational messages to Groq gemma2-9b-it model and handles tool calls.
    If GROQ_API_KEY is not set, it executes a fallback response to demonstrate functionality.
    """
    messages = state["messages"]
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        logger.warning("GROQ_API_KEY not found. Operating in fallback mock AI mode.")
        # Basic heuristic parsing to simulate the agent tools calling when API Key is missing
        last_user_msg = ""
        for m in reversed(messages):
            if isinstance(m, HumanMessage):
                last_user_msg = m.content
                break
        
        # Mock logic based on input query to let the app work without a key
        text = last_user_msg.lower()
        if "smith" in text or "product x" in text:
            mock_message = AIMessage(
                content="I have extracted this information using the **log_interaction** tool to pre-fill the form on the left: \n- **HCP Name**: Dr. Smith [ID: 5]\n- **Date**: Today\n- **Sentiment**: Positive\n- **Products discussed**: Product X\n- **Outcome**: Brochures were shared."
            )
            mock_message.additional_kwargs = {
                "tool_calls": [
                    {
                        "name": "log_interaction",
                        "args": {
                            "hcp_id": 5,
                            "interaction_type": "In-Person",
                            "notes": "Met with Dr. Smith to discuss Product X efficacy. The sentiment was positive and I shared the brochures.",
                            "sentiment": "Positive",
                            "products_discussed": "Product X",
                            "outcome": "Brochures were shared.",
                            "next_steps": "Follow up next visit."
                        }
                    }
                ]
            }
            return {"messages": [mock_message]}
        elif "john" in text or "actually" in text:
            mock_message = AIMessage(
                content="Understood. I have activated the **edit_interaction** tool to update the fields on the left:\n- Changed **HCP Name** to Dr. John [ID: 6]\n- Changed **Sentiment** to Negative\nAll other fields in the form remain unchanged."
            )
            mock_message.additional_kwargs = {
                "tool_calls": [
                    {
                        "name": "edit_interaction",
                        "args": {
                            "hcp_id": 6,
                            "sentiment": "Negative"
                        }
                    }
                ]
            }
            return {"messages": [mock_message]}
        elif "jenkins" in text or "sarah" in text:
            mock_message = AIMessage(
                content="I have resolved Dr. Sarah Jenkins profile and launched the **log_interaction** tool to pre-fill the form on the left:\n- **HCP Name**: Dr. Sarah Jenkins [ID: 1]\n- **Date**: Today\n- **Sentiment**: Positive"
            )
            mock_message.additional_kwargs = {
                "tool_calls": [
                    {
                        "name": "log_interaction",
                        "args": {
                            "hcp_id": 1,
                            "interaction_type": "In-Person",
                            "notes": "Discussed clinical outcomes with Dr. Sarah Jenkins.",
                            "sentiment": "Positive"
                        }
                    }
                ]
            }
            return {"messages": [mock_message]}
        else:
            mock_message = AIMessage(
                content="Hello! I am your AI CRM Assistant. It looks like you're trying to log or retrieve an HCP interaction. To unlock the full power of LangGraph agents and Groq tool calling, please add your `GROQ_API_KEY` in the `.env` file. \n\nFor testing, you can mention **Dr. Smith** or **Dr. John** to trigger a simulated interaction flow."
            )
            return {"messages": [mock_message]}

    import time
    import re

    MAX_RETRIES = 4
    retry_delay = 1.0  # seconds

    for attempt in range(MAX_RETRIES):
        try:
            client = Groq(api_key=api_key)
            
            # Prepare messages in the shape Groq expects
            groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    groq_messages.append({"role": "system", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    groq_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    m_dict = {"role": "assistant", "content": msg.content or ""}
                    if msg.additional_kwargs.get("tool_calls"):
                        m_dict["tool_calls"] = msg.additional_kwargs["tool_calls"]
                    groq_messages.append(m_dict)
                elif isinstance(msg, ToolMessage):
                    groq_messages.append({
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "name": msg.name,
                        "content": msg.content
                    })

            model_name = os.getenv("GROQ_MODEL", "gemma2-9b-it")

            response = client.chat.completions.create(
                model=model_name,
                messages=groq_messages,
                tools=groq_tools,
                tool_choice="auto",
                temperature=0.1
            )

            response_message = response.choices[0].message
            content = response_message.content

            additional_kwargs = {}
            if response_message.tool_calls:
                additional_kwargs["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in response_message.tool_calls
                ]

            ai_msg = AIMessage(content=content or "", additional_kwargs=additional_kwargs)
            return {"messages": [ai_msg]}

        except Exception as e:
            err_str = str(e)
            # Detect rate limit (429) errors and retry with backoff
            if "429" in err_str or "rate_limit_exceeded" in err_str:
                # Try to parse the suggested wait time from the error message
                wait_match = re.search(r'try again in (\d+(?:\.\d+)?)([ms]+)', err_str)
                if wait_match:
                    wait_val = float(wait_match.group(1))
                    wait_unit = wait_match.group(2)
                    wait_seconds = wait_val / 1000.0 if wait_unit.startswith('m') else wait_val
                    wait_seconds = min(wait_seconds + 0.5, 10.0)  # cap at 10s, add 0.5s buffer
                else:
                    wait_seconds = retry_delay * (2 ** attempt)  # exponential backoff

                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Groq rate limit hit (attempt {attempt + 1}/{MAX_RETRIES}). Retrying in {wait_seconds:.1f}s...")
                    time.sleep(wait_seconds)
                    continue
                else:
                    logger.error(f"Groq rate limit exceeded after {MAX_RETRIES} retries.")
                    error_msg = AIMessage(content="⚠️ The AI is temporarily rate-limited by Groq. Please wait a few seconds and try again.")
                    return {"messages": [error_msg]}
            else:
                logger.error(f"Error calling Groq model: {e}")
                error_msg = AIMessage(content=f"An error occurred while calling the Groq LLM: {err_str}. Please check your connectivity and api key.")
                return {"messages": [error_msg]}

def call_tool(state: AgentState) -> Dict[str, Any]:
    """
    Executes the requested tool calls from the AI message and records outcomes.
    """
    messages = state["messages"]
    last_msg = messages[-1]
    
    tool_messages = []
    if "tool_calls" in last_msg.additional_kwargs:
        for tool_call in last_msg.additional_kwargs["tool_calls"]:
            tool_name = tool_call.get("function", {}).get("name") or tool_call.get("name")
            raw_args = tool_call.get("function", {}).get("arguments") or tool_call.get("args") or tool_call.get("arguments")
            if isinstance(raw_args, str):
                tool_args = json.loads(raw_args) if raw_args.strip().startswith('{') or raw_args.strip().startswith('[') else {}
            else:
                tool_args = raw_args or {}
            if not tool_name:
                raise KeyError(f"Tool call missing name: {tool_call}")
            
            logger.info(f"Agent executing tool: {tool_name} with arguments: {tool_args}")
            
            tool_to_call = tools_by_name.get(tool_name)
            if tool_to_call:
                # Call tool
                try:
                    tool_result = tool_to_call.invoke(tool_args)
                except Exception as e:
                    tool_result = json.dumps({"status": "error", "message": str(e)})
            else:
                tool_result = json.dumps({"status": "error", "message": f"Tool {tool_name} not found."})
                
            tool_call_id = tool_call.get("id") or tool_call.get("tool_call_id") or ""
            tool_messages.append(
                ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_call_id,
                    name=tool_name
                )
            )
            
    return {"messages": tool_messages}

def should_continue(state: AgentState) -> str:
    """
    Router determining whether we should call tools or finish the graph run.
    """
    messages = state["messages"]
    last_msg = messages[-1]
    if "tool_calls" in last_msg.additional_kwargs and last_msg.additional_kwargs["tool_calls"]:
        return "tools"
    return END

# Build and compile LangGraph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tool)

workflow.set_entry_point("agent")

# Add conditional edges
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

# Connect tools back to agent for the next turn
workflow.add_edge("tools", "agent")

compiled_graph = workflow.compile()
