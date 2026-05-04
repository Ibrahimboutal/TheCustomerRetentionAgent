import os
import sys
import json
import re
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from api import server

def predict_churn_and_segment() -> str:
    res = server.segment_customers()
    return f"Segmentation completed. Summary: {res['summary']}"

def optimize_budget(budget: float) -> str:
    res = server.trigger_macro_optimization(budget=float(budget))
    return f"Optimization completed. Budget used: ${res['budget_used']}, Customers optimized: {res['customers_optimized']}, Avg Discount: {res['avg_discount_pct']}%."

def generate_customer_discount(customer_id: int) -> str:
    res = server.generate_discount(customer_id=int(customer_id))
    return res['msg']

class RetentionAgent:
    """
    Autonomous LLM-driven agent orchestrator.
    Uses a robust JSON-based ReAct loop to reason about a goal and invoke external backend tools.
    """
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not set. Cannot run Autonomous Agent.")
            
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.tool_mapping = {
            "predict_churn_and_segment": predict_churn_and_segment,
            "optimize_budget": optimize_budget,
            "generate_customer_discount": generate_customer_discount
        }

    def execute_goal(self, goal: str) -> Dict[str, Any]:
        """
        Takes a natural language goal, executes the ReAct loop using tools, and returns the result and trace.
        """
        trace = []
        trace.append({"role": "user", "content": goal})
        
        system_prompt = f"""You are an autonomous Customer Retention Agent. Your mission is to plan and execute retention strategies.
You have the following tools available:
1. predict_churn_and_segment() -> Runs the Machine Learning model to score all customers. No arguments.
2. optimize_budget(budget: float) -> Runs the SciPy SLSQP constrained optimization engine. Argument: 'budget'.
3. generate_customer_discount(customer_id: int) -> Generates a discount code. Argument: 'customer_id'.

You must follow this loop:
1. Plan.
2. Score customers using predict_churn_and_segment.
3. Optimize budget using optimize_budget.
4. Summarize results.

To call a tool, you MUST output a JSON block exactly like this:
```json
{{"tool": "predict_churn_and_segment", "args": {{}}}}
```

When you have finished all steps, output your final answer wrapped exactly like this:
<FINAL_ANSWER>
Your detailed summary here.
</FINAL_ANSWER>

Do not output multiple tool calls at once. Output one tool call, wait for the result, then proceed.

User Goal: {goal}
"""
        
        chat = self.model.start_chat(history=[])
        
        current_prompt = system_prompt
        
        try:
            for step in range(8): # Max 8 steps in the loop
                response = chat.send_message(current_prompt)
                response_text = response.text
                
                # Check for final answer
                final_match = re.search(r'<FINAL_ANSWER>(.*?)</FINAL_ANSWER>', response_text, re.DOTALL)
                if final_match:
                    trace.append({"role": "agent_thought", "content": "Mission Complete."})
                    return {
                        "status": "success",
                        "final_answer": final_match.group(1).strip(),
                        "trace": trace
                    }
                
                # Extract JSON tool call
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if not json_match:
                    trace.append({"role": "agent_thought", "content": response_text})
                    current_prompt = "Please continue and output a tool call in JSON format or provide the <FINAL_ANSWER>."
                    continue
                    
                tool_req = json.loads(json_match.group(1))
                tool_name = tool_req.get("tool")
                args = tool_req.get("args", {})
                
                trace.append({
                    "role": "agent_thought",
                    "content": response_text.split("```json")[0].strip()
                })
                
                trace.append({
                    "role": "agent_tool_call",
                    "tool": tool_name,
                    "args": args
                })
                
                if tool_name in self.tool_mapping:
                    try:
                        tool_result = self.tool_mapping[tool_name](**args)
                    except Exception as e:
                        tool_result = f"Error executing {tool_name}: {str(e)}"
                else:
                    tool_result = f"Error: Tool {tool_name} not found."
                    
                trace.append({
                    "role": "tool_result",
                    "tool": tool_name,
                    "content": str(tool_result)
                })
                
                # Feed the result back into the prompt for the next loop iteration
                current_prompt = f"Tool '{tool_name}' returned:\n{tool_result}\n\nWhat is your next step?"
                
            return {
                "status": "success",
                "final_answer": "Max steps reached without concluding the mission.",
                "trace": trace
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "trace": trace
            }

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    agent = RetentionAgent()
    print("Agent Initialized. Testing autonomous execution loop...")
    res = agent.execute_goal("We have a $3000 budget. Please score the latest cohort and optimize the discount allocations.")
    print("\n--- FINAL ANSWER ---")
    print(res.get("final_answer"))
    print("\n--- TRACE ---")
    for t in res.get("trace", []):
        print(f"[{t['role'].upper()}] {t.get('tool', '')}: {t.get('content', t.get('args', ''))}")
