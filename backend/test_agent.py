import os
import sys
from dotenv import load_dotenv

# Add backend to search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from agent.graph import compiled_graph
from langchain_core.messages import HumanMessage

# Output file with UTF-8 encoding
out = open("test_output_final.txt", "w", encoding="utf-8")

# Test 1: Dr. Smith (Partial case-insensitive lookup)
out.write("=== Scenario 1: Partial Search for Dr. Smith (Case-Insensitive) ===\n")
query1 = "i met dr smith in video confrence"
out.write(f"Triggering: {query1}\n")
try:
    state1 = compiled_graph.invoke({"messages": [HumanMessage(content=query1)]})
    out.write("Message output:\n")
    for msg in state1["messages"]:
         out.write(f"[{type(msg).__name__}]: {msg.content}\n")
         if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
             out.write(f"  Args: {msg.additional_kwargs}\n")
except Exception as e:
    out.write(f"Error: {e}\n")

out.write("\n" + "="*50 + "\n\n")

# Test 2: Dr. Priya Patel (Negative sentiment, indication "ocd", shared files)
out.write("=== Scenario 2: Indication ocd + files + bad experience ===\n")
query2 = "i met dr priya and discussed about ocd. its was bad experience and i shared the files"
out.write(f"Triggering: {query2}\n")
try:
    state2 = compiled_graph.invoke({"messages": [HumanMessage(content=query2)]})
    out.write("Message output:\n")
    for msg in state2["messages"]:
         out.write(f"[{type(msg).__name__}]: {msg.content}\n")
         if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
             out.write(f"  Args: {msg.additional_kwargs}\n")
except Exception as e:
    out.write(f"Error: {e}\n")

out.write("\n" + "="*50 + "\n\n")

# Test 3: Dr. John (Direct registry matched success confirmation)
out.write("=== Scenario 3: Direct matching for Dr. John ===\n")
query3 = "today i met Dr. John and discussed product Z"
out.write(f"Triggering: {query3}\n")
try:
    state3 = compiled_graph.invoke({"messages": [HumanMessage(content=query3)]})
    out.write("Message output:\n")
    for msg in state3["messages"]:
         out.write(f"[{type(msg).__name__}]: {msg.content}\n")
         if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
             out.write(f"  Args: {msg.additional_kwargs}\n")
except Exception as e:
    out.write(f"Error: {e}\n")

out.close()
print("All 3 test scenarios completed and output written to test_output_final.txt")
