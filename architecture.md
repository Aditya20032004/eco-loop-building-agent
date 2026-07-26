# Eco-Loop AI: System Architecture & Design Document

## 1. System Overview
Eco-Loop Building Agents is a live, closed-loop building-energy control system. It replaces rigid, rule-based Building Management Systems (BMS) with an autonomous AI agent capable of dynamic reasoning. The system pairs the EnergyPlus simulation engine (v22.1.0) with a local Qwen2.5:14b LLM, utilizing a primary Model Context Protocol (MCP) tool-calling pipeline with a robust custom Python failsafe.

## 2. Core Components & Closed-Loop Pipeline
The architecture is designed as a continuous feedback loop:
1. **Telemetry Extraction (Feedback):** Using PyEnergyPlus API, the state manager pulls real-time environmental data (outdoor temp, solar radiation), grid carbon intensity, and 7 specific spatial zone states (Core and Perimeter temperatures, occupancy).
2. **Predictive Forecasting:** The orchestrator pre-computes short-term trend heuristics (e.g., upcoming peak solar loads) to ground the LLM's spatial reasoning.
3. **Cognitive Routing (LLM):** The telemetry payload is shipped to `qwen2.5:14b` running locally via Ollama. The LLM evaluates the state against constraints (max 25°C / min 20°C comfort bounds) and external signals (peak dirty grid hours > 500 gCO2/kWh).
4. **Execution Pipeline (Forward Injection):** 
   * **Primary Action:** The LLM issues setpoint overrides via the **MCP Server** integration.
   * **Failsafe Action:** If MCP validation fails or drops, execution seamlessly falls back to custom Python tool bindings.
   * Actions are injected back into the live EnergyPlus memory state via actuator handles before the next HVAC timestep calculation.

## 3. Hardware Constraints & Latency Management
**Challenge:** The host environment runs on a 6GB VRAM GPU. The full Qwen2.5 14-billion parameter model cannot fit entirely in VRAM, requiring partial CPU/GPU layer offloading.
**Architectural Decision:** To prevent catastrophic simulation bottlenecking, the LLM is *not* queried on every single EnergyPlus sub-hourly timestep. 
**Implementation:** The orchestration loop relies on an hourly cognitive interval. The LLM is queried once per simulated hour (using `day_of_year` and `hour` tracking). This deliberate design choice preserves sub-minute physical simulation accuracy within EnergyPlus while ensuring the inference latency (~7s cold-call) remains completely viable for edge-deployed building hardware.

## 4. Prompt Engineering & JSON Guardrails
Due to the non-deterministic nature of LLM outputs (including markdown wrapping, conversational padding, or stray commas), a strict regex-based JSON extraction layer was built into `orchestrator.py`. 
* The prompt structure explicitly forces a precise JSON array of actions per zone.
* If the LLM generates conversational text around the JSON, the regex bounds `\{.*\}` isolate the valid payload.
* The parsed targets are validated against physical limits before being dispatched via MCP.

## 5. Quantitative Validation
Savings are calculated deterministically. The system runs a true comparative workflow against a DOE/PNNL Commercial Prototype Medium Office `.idf` (Climate Zone 2A, Tampa, FL). 
* **Baseline:** A rule-based baseline is generated via `sim_run`.
* **AI Run:** The agentic loop generates a secondary dataset.
* **Dashboard:** The Streamlit UI ingests both datasets to output exact kWh energy reduction and grid carbon emissions avoidance without relying on fabricated scaling factors.