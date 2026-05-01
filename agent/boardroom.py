import os
import google.generativeai as genai
from typing import Dict, Any

class BoardroomDebate:
    """
    🎭 MULTI-AGENT DEBATE SYSTEM
    Orchestrates a debate between three Gemini personas to decide on retention budgets.
    """
    def __init__(self):
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-pro')

    def run_debate(self, customer_name: str, risk: str, ltv: float) -> Dict[str, Any]:
        # Persona 1: Customer Success (Aggressive Save)
        prompt_success = f"Persona: Customer Success Agent. Goal: Save the customer {customer_name} at all costs. They have a churn risk of {risk} and LTV of ${ltv}. Propose a discount and justify it emotionally."
        success_opinion = self.model.generate_content(prompt_success).text

        # Persona 2: CFO (Frugal/ROI focus)
        prompt_cfo = f"Persona: CFO. Goal: Minimize margin erosion. Review the Success Agent's opinion: '{success_opinion}'. Argue for a lower discount if the ROI isn't clear for {customer_name}."
        cfo_opinion = self.model.generate_content(prompt_cfo).text

        # Persona 3: Orchestrator (The Decider)
        prompt_orchestrator = f"""
        Persona: Executive Orchestrator. 
        Context:
        - Customer: {customer_name}
        - Risk: {risk}
        - LTV: ${ltv}
        - Success Agent Opinion: {success_opinion}
        - CFO Opinion: {cfo_opinion}
        
        Task: Mediate the debate and provide a final approved discount percentage (0-30%) and a concise summary.
        Output Format: JSON with 'discount', 'summary', and 'debate_transcript'.
        """
        
        # Using constrained output for the decider
        final_decision = self.model.generate_content(
            prompt_orchestrator,
            generation_config={"response_mime_type": "application/json"}
        ).text

        import json
        try:
            res = json.loads(final_decision)
            res['debate_transcript'] = f"SUCCESS: {success_opinion[:200]}...\nCFO: {cfo_opinion[:200]}..."
            return res
        except:
            return {"discount": 10, "summary": "Defaulted to 10% due to debate deadlock.", "debate_transcript": "Error parsing debate."}
