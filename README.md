# 🛡️ ML4MS: NACE Compliance Agent
[![arXiv](https://img.shields.io/badge/arXiv-2512.00977-b31b1b.svg)](https://arxiv.org/abs/2512.00977)

**Provenance-Enforced AI for Sour Service Material Selection**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://huggingface.co/spaces/aaburakhia/ML4MS-Material-Validator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/)

### 🔗 [Launch Live App on Hugging Face](https://huggingface.co/spaces/aaburakhia/ML4MS-Material-Validator)

---

## 1. The Engineering Challenge
In the Oil & Gas industry, specifically in **Sour Service** ($H_2S$) environments, material selection is governed by **NACE MR0175 / ISO 15156**.
*   **The Risk:** Standard AI models (LLMs) often "hallucinate" material properties. If an AI guesses the chemistry of a Liner Hanger, it can lead to **Sulfide Stress Cracking (SSC)** and catastrophic well failure.
*   **The Goal:** Build an AI agent that **refuses to guess**. It must calculate physics deterministically and provide a digital audit trail.

## 2. Solution Architecture
This tool implements the **"Render Gate"** architecture proposed in *"Crystalyse: a multi-tool agent for materials design"* (Nduma et al., 2025).

### The Hybrid RAG Workflow
The agent uses a 3-layer verification process to ensure Asset Integrity:

1.  **Trusted Knowledge Layer:** First, it searches an internal "Approved Vendor List" (CSV Database).
2.  **Physics Engine Layer:** If the material is new, it estimates the formula but calculates **PREN** (Pitting Resistance Equivalent Number) using the `Pymatgen` Quantum Mechanics library.
3.  **The Render Gate:** Every result is cryptographically signed (SHA-256). If the UI cannot verify the hash, the data is blocked.

```mermaid
graph TD
    A["User Input"] --> B{"Search Trusted DB"}
    B -- Found --> C["Load Verified Data"]
    B -- Not Found --> D["AI Estimation (Warning)"]
    C --> E["Human Verification"]
    D --> E
    E --> F["Pymatgen Physics Engine"]
    F --> G{"NACE Rule Check"}
    G --> H["Generate Hash Signature"]
    H --> I["Display Result"]
```

---
## 📚 Scientific References

This project is an implementation of the **"Render Gate"** architecture described in:

> **Crystalyse: a multi-tool agent for materials design**  
> *Ryan Nduma, Hyunsoo Park, and Aron Walsh*  
> Department of Materials, Imperial College London (2025)  
> 📄 [Read the Paper on arXiv](https://arxiv.org/abs/2512.00977)

**Engineering Standards:**
*   **NACE MR0175 / ISO 15156:** *Petroleum and natural gas industries — Materials for use in H2S-containing environments.*
