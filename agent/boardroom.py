import os
import random
from typing import Dict, Any

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

class BoardroomDebate:
    """
    MULTI-AGENT DEBATE SYSTEM
    Orchestrates a debate between three AI personas to decide on retention budgets.
    Falls back to a deterministic simulation when no API key is configured.
    """
    def __init__(self):
        self.use_ai = bool(GOOGLE_API_KEY)
        if self.use_ai:
            try:
                from google import genai
                self.client = genai.Client(api_key=GOOGLE_API_KEY)
            except Exception:
                self.use_ai = False

    def _ai_debate(self, customer_name: str, risk: str, ltv: float) -> Dict[str, Any]:
        from google import genai
        client = self.client

        success_prompt = (
            f"Persona: Customer Success Agent. Goal: Save the customer {customer_name} at all costs. "
            f"They have a churn risk of {risk} and LTV of ${ltv:.0f}. "
            f"Propose a discount percentage (5-30%) and justify it in 2-3 sentences."
        )
        success_opinion = client.models.generate_content(
            model="gemini-2.0-flash", contents=success_prompt
        ).text

        cfo_prompt = (
            f"Persona: CFO. Goal: Minimize margin erosion. "
            f"Review the Customer Success Agent's opinion: '{success_opinion[:300]}'. "
            f"Argue for a lower or no discount if ROI isn't clear for {customer_name}. 2-3 sentences."
        )
        cfo_opinion = client.models.generate_content(
            model="gemini-2.0-flash", contents=cfo_prompt
        ).text

        orchestrator_prompt = f"""
Persona: Executive Orchestrator.
Context:
- Customer: {customer_name}
- Churn Risk: {risk}
- LTV: ${ltv:.0f}
- Success Agent Opinion: {success_opinion[:300]}
- CFO Opinion: {cfo_opinion[:300]}

Task: Mediate the debate and provide a final approved discount percentage (0-30%) and a concise summary.
Output ONLY valid JSON with keys: "discount" (integer), "summary" (string), "debate_transcript" (string).
"""
        import json
        raw = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=orchestrator_prompt,
            config={"response_mime_type": "application/json"}
        ).text

        try:
            res = json.loads(raw)
            res['debate_transcript'] = (
                f"<b>[SUCCESS AGENT]</b> {success_opinion[:300]}...<br><br>"
                f"<b>[CFO]</b> {cfo_opinion[:300]}..."
            )
            res['ai_powered'] = True
            return res
        except Exception:
            return self._mock_debate(customer_name, risk, ltv)

    def _mock_debate(self, customer_name: str, risk: str, ltv: float) -> Dict[str, Any]:
        risk_val = float(str(risk).replace('%', '')) / 100 if '%' in str(risk) else float(risk)

        if risk_val > 0.6:
            success_stance = f"This customer is critically at risk! We MUST offer 25-30% to save them."
            cfo_stance = f"High risk but also high cost. I'll approve 20% — any more destroys margin."
            discount = random.randint(18, 25)
            summary = f"High churn risk justifies an aggressive retention offer of {discount}%."
        elif risk_val > 0.3:
            success_stance = f"Moderate risk detected. A 15% offer should be enough to re-engage {customer_name}."
            cfo_stance = f"Agreed on moderate risk. I'll approve up to 12% — let's not over-discount."
            discount = random.randint(10, 18)
            summary = f"Moderate churn risk. A {discount}% discount is ROI-positive given their LTV."
        else:
            success_stance = f"{customer_name} is relatively stable but proactive engagement prevents future churn."
            cfo_stance = f"Low risk — no more than 5% discount justified. Protect our margins."
            discount = random.randint(3, 10)
            summary = f"Low churn risk. A small {discount}% loyalty reward is approved to maintain satisfaction."

        ltv_k = ltv / 1000
        return {
            "discount": discount,
            "summary": summary,
            "debate_transcript": (
                f"<b>[SUCCESS AGENT]</b> {success_stance}<br><br>"
                f"<b>[CFO]</b> {cfo_stance}<br><br>"
                f"<b>[ORCHESTRATOR]</b> Weighing LTV of ${ltv_k:.1f}K against retention cost... "
                f"Final decision: <b>{discount}% discount approved</b>."
            ),
            "ai_powered": False
        }

    def run_debate(self, customer_name: str, risk: str, ltv: float) -> Dict[str, Any]:
        if self.use_ai:
            try:
                return self._ai_debate(customer_name, risk, ltv)
            except Exception:
                pass
        return self._mock_debate(customer_name, risk, ltv)
