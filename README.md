code Markdown

# Exzing Reservoir Management Agent (ExReservoirGPT) 🛢️🤖

**Empowering Reservoir Engineers with Agentic Intelligence and Automated QC.**

Exzing Reservoir Management Agent is an enterprise-grade SaaS solution designed to accelerate the Field Development Planning (FDP) lifecycle. By combining deterministic reservoir physics (Arps, ECLIPSE™ syntax) with advanced AI reasoning (Azure OpenAI, Groq), ExReservoirGPT automates simulation deck architecture and technical data auditing.

[![Azure Marketplace](https://img.shields.io/badge/Azure-Marketplace-blue.svg)](https://azuremarketplace.microsoft.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Key Features

*   **Field Architect (Deck Generator):** Convert natural language requirements into valid ECLIPSE/OPM `.DATA` files. Supports professional "Include" workflows for static-model integration.
*   **Asset Intelligence (Data QC):** Automated detection and remediation of production history anomalies using heuristic engineering rules.
*   **Scenario Lab:** Pre-validated against 150+ industrial test cases, including Volve, Norne, and SPE Comparative Solutions.
*   **AI Reservoir Advisor:** Natural language querying of subsurface datasets for rapid executive insights.
*   **Safety Shield:** Integrated with **Azure AI Content Safety** and a proprietary **Physics Scorer** to prevent unrealistic or dangerous engineering designs.

## 🏗️ Architecture

The system is built on a "Federated SaaS" model:
1.  **Billing Layer:** Azure Commercial Marketplace SaaS Accelerator (.NET Core).
2.  **Logic Layer:** Python-based Agentic Engine.
3.  **Security Layer:** Azure Key Vault & Microsoft Entra ID (SSO).
4.  **Inference Layer:** AzureOpenAI (gpt-5-main) and Groq (openai/gpt-oss-120b).

## Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/okpoEkpenyong/reservoir_mgt_agent.git
   cd reservoir_mgt_agent

    Create a Virtual Environment:
    code Bash

python -m venv .venv
.venv\Scripts\activate  # Windows

Install Dependencies:
code Bash

pip install -r requirements.txt

Configure Secrets:
Create .streamlit/secrets.toml:
code Toml

AZURE_OPENAI_KEY = "your_openai_key"
AZURE_OPENAI_ENDPOINT = "your_openai_endpoint"
GROQ_API_KEY = "your_groq_key"
CONTENT_SAFETY_KEY = "your_key"
CONTENT_SAFETY_ENDPOINT = "your_endpoint"
AZURE_OPENAI_DEPLOYMENT="your_openai_deployment"
AZURE_OPENAI_VERSION="your_openai_version"


Run the App:
code Bash

    streamlit run app.py

🛡️ AI Governance & Privacy

    Zero-Data Retention (ZDR): Technical prompts are processed in-memory and are never used for global model training.

    Human-in-the-Loop (HITL): All generated simulation decks require manual engineer verification before export is enabled.

    Provenance Tracking: Every benchmark generation includes direct links to original open-source datasets (e.g., Equinor Volve).

⚖️ Legal Disclaimer

ECLIPSE is a mark of Schlumberger. OPM is an open-source project. Exzing Reservoir Management Agent is an independent technical solution and is not affiliated with, sponsored by, or endorsed by Schlumberger or the Open Porous Media initiative.

© 2026 Exzing Technology Ltd.