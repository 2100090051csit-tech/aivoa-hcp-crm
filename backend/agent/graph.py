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

CRITICAL GUIDELINES FOR DYNAMIC FORM CONTROL:
1. ALWAYS TRIGGER A TOOL: If the user describes ANY meeting, interaction, call, or video session, you MUST log it by invoking the tools. Do not just reply with text; you must control the form dynamically.
2. STEP-BY-STEP ORCHESTRATION (NO FAKE/PLACEHOLDER IDs): If you do not have the doctor's integer ID from a previous tool output, you MUST call `get_hcp_profile(name_query=...)` FIRST to find it. Do NOT call `log_interaction` with placeholder/fake IDs (e.g. 12345 or 67890) or null values in the same turn. Run `get_hcp_profile` on its own first. Once the profile tool succeeds and returns the doctor's integer ID to you, call `log_interaction` with that correct ID in the next turn.
3. PARTIAL PHYSICIAN NAMES: If the user refers to a physician by a partial name (e.g., "dr smith", "smith", "priya", "rajesh"), you MUST first call `get_hcp_profile(name_query=<partial_name>)` to look up their ID. Once the tool returns the profile data, call `log_interaction` using the returned `hcp_id`.
4. DATABASE LOOKUP FALLBACK (CUSTOM ERROR MESSAGE): If the get_hcp_profile tool returns no matching doctor, or if the lookup fails (returns an error status), you MUST reply with this exact helpful error message:
   "⚠️ I couldn't find a doctor in our registry matching '<name>'. Please type their name again or choose from the registry list: Dr. Rajesh Kumar, Dr. Ananya Sharma, Dr. Vikram Adiga, Dr. Priya Patel, Dr. Smith, or Dr. John."
   Do NOT output this message on the first turn before you have received the output of the get_hcp_profile tool. If you are calling get_hcp_profile, do not output any warning message text in that turn.
5. EXTRACT PARAMETERS DYNAMICALLY FROM CONVERSATION:
   - `interaction_type`: Determine based on text clues. Use "Video" if they mention "video", "confrence", "zoom", "teams", "meets". Use "Call" for "phone", "call", "mobile". Use "Email" for "email", "mail", "sent files", "shared files". Default to "In-Person" if no channel is specified.
   - `products_discussed`: Set this to whatever drug, disease, topic, or indication they discussed (even if it's "ocd" or a custom text). Write verbatim.
   - `sentiment`: Map "good", "great", "positive", "helpful" -> "Positive". Map "bad", "terrible", "hard pushback", "negative", "worst" -> "Negative". Otherwise, default to "Neutral".
   - `notes`: Populate this field with the user's description.
   - `outcome`: Extract progress/feedback (e.g. "bad experience", "positive response", "requested data").
   - `next_steps`: Extract planned follow-ups (e.g., "will email clinical trials tomorrow", "send brochures").
   - `date_str`: Format as YYYY-MM-DD. Calculate relative date terms (e.g., "today" is 2026-07-15, "yesterday" is 2026-07-14) relative to current local date July 15, 2026.
   - `brochures_shared`: Set to true if they mention "brochure", "pamphlet", "brochures", "slides", "files", or sharing documents. Otherwise, set to false.
6. NO CONVERSATIONAL TEXT DURING TOOL CALLS: When calling any tool, output ONLY the tool call. Do not include conversational text or summary. Only output standard conversational text in the final turn when no further tools are called.
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
            client = Groq(api_key=api_key, max_retries=0)
            
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
            
            # Detect model deprecation/decommissioning errors and fallback automatically
            if "decommissioned" in err_str.lower() or "does not exist" in err_str.lower() or "not found" in err_str.lower() or "unknown model" in err_str.lower() or "400" in err_str:
                current_model = os.getenv("GROQ_MODEL", "gemma2-9b-it")
                fallback_model = "llama-3.1-8b-instant"
                logger.warning(f"Model '{current_model}' is decommissioned or unavailable. Automatically falling back to '{fallback_model}'. Error was: {err_str}")
                os.environ["GROQ_MODEL"] = fallback_model
                if attempt < MAX_RETRIES - 1:
                    time.sleep(0.5)
                    continue
            
            # Detect rate limit (429 / Too Many Requests) errors and retry with backoff
            if "429" in err_str or "rate" in err_str.lower() or "limit" in err_str.lower() or "too many requests" in err_str.lower():
                current_model = os.getenv("GROQ_MODEL", "gemma2-9b-it")
                if "70b" in current_model or "gemma" in current_model.lower():
                    fallback_model = "llama-3.1-8b-instant"
                    logger.warning(f"Model '{current_model}' rate-limited (429). Falling back to '{fallback_model}'...")
                    os.environ["GROQ_MODEL"] = fallback_model
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(0.5)
                        continue
                
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
