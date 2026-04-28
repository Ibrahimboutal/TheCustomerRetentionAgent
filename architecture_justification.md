# 🏗️ Architectural Justification & NFR Mapping

To move from a "prototype" to a "production-grade system," every architectural choice must be mapped to a **Non-Functional Requirement (NFR)**.

| Component | Choice | Justification (The "Why") |
| :--- | :--- | :--- |
| **Identity & IAM** | AWS Cognito | **Compliance**: CRM data contains PII. Cognito provides OIDC/SAML integration and SOC2/HIPAA compliance out of the box. |
| **Compute Layer** | AWS Lambda | **Scalability**: Retention campaigns are batch-processed (spiky traffic). Serverless auto-scales to 1,000s of concurrent agents without idle server costs. |
| **Decision Logic** | Python Rules Engine | **Determinism**: Financial risk (discounts) cannot be left to probabilistic LLMs. Python ensures 100% adherence to legal and financial policies. |
| **Intelligence** | Bedrock / Vertex AI | **Stateful Reasoning**: Retention requires multi-step context (complaint -> apology -> offer). Agentic frameworks provide the "memory" needed for empathy. |
| **Persistence** | SQLite (Mock) | **Portability**: Facilitates 1:1 demonstration of schema design without cloud database latency during the live pitch. |

## 🛡️ Trust & Safety
The system implements a **"Sandwiched" Architecture**:
1.  **Bottom Layer**: Deterministic ML (XGBoost) predicts the risk.
2.  **Middle Layer**: LLM (Gemini) generates the personalized empathy.
3.  **Top Layer**: Deterministic Rules Engine (Python) validates and enforces the final financial output.
