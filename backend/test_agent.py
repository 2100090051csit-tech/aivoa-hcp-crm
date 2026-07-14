import os
import sys
from dotenv import load_dotenv

# Add backend to search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from agent.graph import compiled_graph
from langchain_core.messages import HumanMessage

# Redirect stdout to test_log.txt with UTF-8 encoding
log_file = open("test_log.txt", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

print("=== Running Scenario: Partial name + Video Conference ===")
query1 = "i met dr smith in video confrence"
print(f"Triggering query 1: {query1}")

try:
    state1 = compiled_graph.invoke({"messages": [HumanMessage(content=query1)]})
    print("\nSuccess! Messages in state for Query 1:")
    for idx, msg in enumerate(state1["messages"]):
        print(f"\n[{idx}] {type(msg).__name__}:")
        print("Content:", msg.content)
        if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
            print("Additional Kwargs:", msg.additional_kwargs)
except Exception as e:
    print("\nError occurred for Query 1:", e)


print("\n=== Running Scenario: Custom indication (ocd) + Bad Experience + files ===")
query2 = "i met dr priya and discussed about ocd. its was bad experience and i shared the files"
print(f"Triggering query 2: {query2}")

try:
    state2 = compiled_graph.invoke({"messages": [HumanMessage(content=query2)]})
    print("\nSuccess! Messages in state for Query 2:")
    for idx, msg in enumerate(state2["messages"]):
        print(f"\n[{idx}] {type(msg).__name__}:")
        print("Content:", msg.content)
        if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
            print("Additional Kwargs:", msg.additional_kwargs)
except Exception as e:
    print("\nError occurred for Query 2:", e)

log_file.close()
