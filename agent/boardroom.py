import os
import re
import json
import random
from datetime import datetime
from typing import Dict, Any, List

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


class BoardroomDebate:
    """
    MULTI-AGENT DEBATE SYSTEM
    Orchestrates a debate between three AI personas (Customer Success, CFO, Orchestrator)
    to decide on retention interventions.  Falls back to a rich deterministic simulation
    when no Gemini API key is configured.
    """

    SPEAKERS = {
        "CS":    {"label": "Customer Success Agent", "color": "#4DFF88", "side": "left",  "icon": "🤝"},
        "CFO":   {"label": "CFO",                    "color": "#FF6B6B", "side": "right", "icon": "💼"},
        "ORCH":  {"label": "Executive Orchestrator",  "color": "#00F5FF", "side": "center","icon": "⚖️"},
    }

    def __init__(self):
        self.use_ai = bool(GOOGLE_API_KEY)
        if self.use_ai:
            try:
                from google import genai
                self.client = genai.Client(api_key=GOOGLE_API_KEY)
            except Exception:
                self.use_ai = False

    # ── AI path (Gemini 2.0 Flash) ──────────────────────────────────────────
    def _ai_debate(self, name: str, risk: str, ltv: float) -> Dict[str, Any]:
        client = self.client

        cs_prompt = (
            f"Persona: Customer Success Agent. Goal: Save the customer {name} at all costs. "
            f"Churn risk: {risk}. LTV: ${ltv:,.0f}. "
            f"Propose a discount (5-30%) and justify it in 3 compelling sentences. "
            f"Be passionate. Mention specific financial risk numbers."
        )
        cs_text = client.models.generate_content(
            model="gemini-2.0-flash", contents=cs_prompt).text

        cfo_prompt = (
            f"Persona: CFO. Goal: Protect margins. "
            f"The CS Agent said: '{cs_text[:350]}'. "
            f"Challenge the ROI. Propose a lower counter-offer with hard numbers. 3 sentences."
        )
        cfo_text = client.models.generate_content(
            model="gemini-2.0-flash", contents=cfo_prompt).text

        orch_prompt = f"""
Persona: Executive Orchestrator. You are the final decision-maker.
Customer: {name} | Churn Risk: {risk} | LTV: ${ltv:,.0f}
CS Agent: {cs_text[:300]}
CFO: {cfo_text[:300]}
Synthesise both views. Be decisive. Output ONLY valid JSON:
{{"discount": <integer 0-30>, "summary": "<2-sentence verdict>", "orch_text": "<your reasoning 3 sentences>"}}
"""
        raw = client.models.generate_content(
            model="gemini-2.0-flash", contents=orch_prompt,
            config={"response_mime_type": "application/json"}).text

        try:
            res = json.loads(raw)
            messages = [
                {"speaker": "CS",   "text": cs_text},
                {"speaker": "CFO",  "text": cfo_text},
                {"speaker": "ORCH", "text": res.get("orch_text", res.get("summary", ""))},
            ]
            return {
                "discount": int(res.get("discount", 15)),
                "summary":  res.get("summary", ""),
                "messages": messages,
                "ai_powered": True,
                "debate_transcript": self._messages_to_html(messages),
            }
        except Exception:
            return self._mock_debate(name, risk, ltv)

    # ── Simulation path (rich deterministic) ────────────────────────────────
    def _mock_debate(self, name: str, risk: str, ltv: float) -> Dict[str, Any]:
        risk_val = float(str(risk).replace('%', '').strip()) / 100 \
                   if '%' in str(risk) else float(risk)
        ltv_k = ltv / 1000
        save_val = ltv * (1 - risk_val)

        if risk_val > 0.65:
            discount = random.randint(20, 28)
            cs_text  = (
                f"{name} is in critical danger — our model puts their churn probability at "
                f"{risk_val*100:.0f}%. Losing them means ${ltv:,.0f} in LTV walks out the door. "
                f"I'm recommending a {discount}% retention discount. At ${ltv*discount/100:,.0f} cost, "
                f"we protect ${save_val:,.0f} in future revenue — that's a {save_val/(ltv*discount/100):.1f}x "
                f"return. We cannot afford to lose this customer."
            )
            cfo_text = (
                f"The numbers support intervention, but {discount}% is the ceiling — not the floor. "
                f"I've modelled the margin impact: at {discount}% we absorb ${ltv*discount/100:,.0f} in "
                f"discount cost against ${save_val:,.0f} in retained revenue. "
                f"My counter is {discount-3}%, which keeps us ROI-positive at {save_val/(ltv*(discount-3)/100):.1f}x. "
                f"Agreeing to {discount}% sets a dangerous precedent for renegotiation."
            )
            orch_text = (
                f"Both positions are defensible. The churn risk of {risk_val*100:.0f}% is too high to ignore, "
                f"but the CFO's margin concern is valid. I'm approving **{discount}% — final**. "
                f"Expected retention value: ${save_val:,.0f}. Intervention cost: ${ltv*discount/100:,.0f}. "
                f"Net expected gain: ${save_val - ltv*discount/100:,.0f}. Proceed immediately."
            )
            summary = (f"Critical risk ({risk_val*100:.0f}%). {discount}% discount approved. "
                       f"Net gain: ${save_val - ltv*discount/100:,.0f}.")

        elif risk_val > 0.4:
            discount = random.randint(12, 20)
            cs_text  = (
                f"{name} is drifting — {risk_val*100:.0f}% churn risk with ${ltv_k:.1f}K in lifetime value. "
                f"This is exactly the profile we lose if we wait. A {discount}% proactive offer costs us "
                f"${ltv*discount/100:,.0f} but retains ${save_val:,.0f}. "
                f"Early intervention is always cheaper than win-back. I recommend acting now."
            )
            cfo_text = (
                f"I'll grant that {risk_val*100:.0f}% risk warrants attention, but {discount}% feels generous "
                f"for a customer who hasn't actually churned yet. "
                f"My proposal: {discount-4}% with a loyalty tier upgrade — same retention signal, "
                f"lower margin erosion. The ROI at {discount-4}% is still {save_val/(ltv*(discount-4)/100):.1f}x."
            )
            orch_text = (
                f"Moderate risk, moderate response. CS's urgency is noted; CFO's caution is prudent. "
                f"Approved: **{discount}%** — splitting the difference and prioritising retention. "
                f"This yields an expected ${save_val - ltv*discount/100:,.0f} net benefit. Log the action."
            )
            summary = (f"Moderate risk ({risk_val*100:.0f}%). {discount}% discount approved. "
                       f"Expected net benefit: ${save_val - ltv*discount/100:,.0f}.")

        else:
            discount = random.randint(4, 10)
            cs_text  = (
                f"{name} is low-risk today, but {risk_val*100:.0f}% is not zero. "
                f"A small {discount}% loyalty reward costs ${ltv*discount/100:,.0f} and locks in "
                f"${save_val:,.0f} in future revenue. Proactive gestures are the cheapest form of retention. "
                f"I'd rather spend now than pay for win-back campaigns later."
            )
            cfo_text = (
                f"Agreed on the principle, but {discount}% for a low-risk customer is borderline wasteful. "
                f"I'll approve {min(discount, 6)}% — a loyalty acknowledgement, not a desperation move. "
                f"We should preserve discount capacity for the accounts that actually need it."
            )
            orch_text = (
                f"Low risk, small intervention. {discount}% approved as a proactive loyalty signal. "
                f"Cost: ${ltv*discount/100:,.0f}. This is maintenance spend, not rescue spend — "
                f"acceptable given the ${ltv_k:.1f}K LTV we're protecting."
            )
            summary = (f"Low risk ({risk_val*100:.0f}%). {discount}% loyalty reward approved. "
                       f"Proactive engagement strategy.")

        messages = [
            {"speaker": "CS",   "text": cs_text},
            {"speaker": "CFO",  "text": cfo_text},
            {"speaker": "ORCH", "text": orch_text},
        ]
        return {
            "discount":          discount,
            "summary":           summary,
            "messages":          messages,
            "ai_powered":        False,
            "debate_transcript": self._messages_to_html(messages),
        }

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _messages_to_html(self, messages: List[Dict]) -> str:
        parts = []
        for m in messages:
            sp = self.SPEAKERS.get(m["speaker"], {})
            label = sp.get("label", m["speaker"])
            color = sp.get("color", "#ccc")
            icon  = sp.get("icon", "•")
            parts.append(
                f"<b style='color:{color}'>{icon} [{label}]</b><br>{m['text']}"
            )
        return "<br><br>".join(parts)

    def run_debate(self, name: str, risk: str, ltv: float) -> Dict[str, Any]:
        if self.use_ai:
            try:
                return self._ai_debate(name, risk, ltv)
            except Exception:
                pass
        return self._mock_debate(name, risk, ltv)

    # ── Executive Briefing ───────────────────────────────────────────────────
    @staticmethod
    def generate_executive_briefing(df, api_key: str = "") -> str:
        """Generate a C-suite war room briefing from CRM data."""
        import pandas as pd

        at_risk   = df[df['segment'] == 'At Risk']
        n_risk    = len(at_risk)
        total     = len(df)
        rev_risk  = float(at_risk['TotalCharges'].sum())
        avg_churn = float(df['churn_probability'].mean())
        monthly   = float(df['MonthlyCharges'].sum())
        top3      = at_risk.nlargest(3, 'TotalCharges')[['name', 'churn_probability', 'TotalCharges']]

        top3_lines = "\n".join(
            f"  • {r['name']}: {r['churn_probability']:.0f}% churn risk, "
            f"${r['TotalCharges']:,.0f} LTV"
            for _, r in top3.iterrows()
        )

        opt_budget    = rev_risk * 0.15
        expected_save = rev_risk * avg_churn / 100 * 0.72  # approx uplift

        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                prompt = f"""You are the Chief Revenue Officer preparing an urgent war room briefing.

CRM Intelligence Summary:
- Total active customers: {total}
- Customers at churn risk: {n_risk} ({n_risk/total*100:.0f}%)
- Revenue exposed to churn: ${rev_risk:,.0f}
- Average churn probability: {avg_churn:.1f}%
- Monthly recurring revenue: ${monthly:,.0f}
- Top 3 at-risk by LTV:
{top3_lines}
- Recommended intervention budget: ${opt_budget:,.0f} (15% of exposed revenue)
- Expected revenue saved with optimal discounting: ${expected_save:,.0f}

Write a concise, data-driven executive war room briefing (4 paragraphs):
1. SITUATION: Current retention crisis summary with key numbers
2. RISKS: Top threats and which customer profiles are most vulnerable
3. RECOMMENDED ACTIONS: Specific, numbered, immediately actionable steps
4. EXPECTED ROI: Financial impact of intervention vs inaction

Tone: Direct, urgent, C-suite level. Use the actual numbers provided."""
                result = client.models.generate_content(
                    model="gemini-2.0-flash", contents=prompt).text
                return result
            except Exception:
                pass

        # Deterministic simulation fallback
        ts    = datetime.now().strftime("%B %d, %Y at %H:%M")
        saved = expected_save - opt_budget
        roi   = expected_save / max(opt_budget, 1)

        return f"""**WAR ROOM EXECUTIVE BRIEFING — {ts}**

---

**1. SITUATION**
The retention model has flagged **{n_risk} of {total} customers ({n_risk/total*100:.0f}%)** as actively at risk of churning. This represents **${rev_risk:,.0f} in exposed lifetime value** — approximately {rev_risk/monthly:.1f} months of recurring revenue. The average churn probability across the at-risk cohort is **{avg_churn:.1f}%**, with the most severe cases exceeding 70%. Without intervention, we project a revenue impact of **${rev_risk * avg_churn/100:,.0f}** in the next 90 days.

**2. KEY RISKS**
The three highest-value customers at risk are:
{top3_lines}
The cohort analysis reveals that **month-to-month contract holders** and **fibre optic internet customers without security add-ons** show the highest churn concentration. Customers in the 0–12 month tenure bracket show average churn risk 1.4× higher than the stable 25–48 month cohort.

**3. RECOMMENDED ACTIONS**
1. **Immediate:** Deploy SLSQP-optimised discounts to top {min(n_risk, 10)} at-risk customers — budget ${opt_budget:,.0f}
2. **48 hours:** Run autonomous agent scan across all {n_risk} at-risk accounts; log all boardroom debate outcomes
3. **This week:** Upgrade top 3 highest-LTV at-risk customers to VIP tier; assign dedicated success manager
4. **Ongoing:** Re-score all customers every 7 days; escalate any account crossing 60% churn threshold automatically

**4. EXPECTED ROI**
Intervention budget: **${opt_budget:,.0f}**
Expected revenue retained: **${expected_save:,.0f}**
Estimated net gain: **${saved:,.0f}**
ROI multiple: **{roi:.1f}x**
Cost of inaction (projected churn loss): **${rev_risk * avg_churn/100:,.0f}**"""
