import os
import sys
from dotenv import load_dotenv

# Add backend to search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from agent.graph import compiled_graph
from langchain_core.messages import HumanMessage

print("Initialized.")
print("GROQ_API_KEY:", os.getenv("GROQ_API_KEY")[:10] + "..." if os.getenv("GROQ_API_KEY") else "None")
print("GROQ_MODEL:", os.getenv("GROQ_MODEL"))

# First test query
query = "Register an interaction with Dr. Rajesh Kumar about Product X. The sentiment was positive and we shared brochures."
print(f"Triggering query: {query}")

try:
    state = compiled_graph.invoke({"messages": [HumanMessage(content=query)]})
    print("\nSuccess! Messages in state:")
    for idx, msg in enumerate(state["messages"]):
        print(f"\n[{idx}] {type(msg).__name__}:")
        print("Content:", msg.content)
        if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
            print("Additional Kwargs:", msg.additional_kwargs)
except Exception as e:
    print("\nError occurred:", e)
