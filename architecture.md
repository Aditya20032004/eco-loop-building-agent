# Eco-Loop Building Agents: System Architecture

## System Overview
Eco-Loop is a live, closed-loop building-energy control system that replaces rigid, rule-based HVAC schedules with an autonomous AI agent. By combining the high-fidelity **EnergyPlus** simulation engine with a locally hosted **Qwen2.5 (14B)** Large Language Model, the system continuously ingests real-time zone telemetry, evaluates thermal comfort against energy demand, and injects forward-control setpoints directly into the running simulation's memory.

## 1. Tool-Calling & Forward Injection Architecture
To achieve a continuous loop without shutting down the simulation, we utilized the native `pyenergyplus` API rather than traditional `.idf` text-parsing or batch CSV analysis. 

*   **Memory Handles:** The system accesses C++ memory pointers (`get_variable_handle` and `get_actuator_handle`) to read sensor data and write setpoints with zero file I/O latency.
*   **Agentic Tools:** The LLM's control decisions are routed through a strict Python tool-parser (`BuildingTools.adjust_setpoint`). This layer acts as a safety guardrail, clamping all AI-generated setpoints to human-safe thermal bounds (18.0°C – 28.0°C) before injecting them into the building.
*   **The Callback Override:** To ensure the AI acts as an authoritative controller, the orchestration script hooks into the simulation at `callback_after_predictor_after_hvac_managers`. This specific injection point allows the AI to override the default rule-based HVAC schedules *after* they are calculated but *before* the physics engine applies them to the current timestep.

## 2. Latency & Hardware Resource Management
Running a 14-billion parameter LLM natively poses severe hardware constraints, specifically regarding the system's 6GB VRAM limit. 

*   **CPU Offloading:** Because the model exceeds available VRAM, Ollama automatically offloads layers to the CPU, resulting in response latencies of ~15–22 seconds per call during continuous inference. 
*   **Temporal Batching:** To prevent the simulation from taking days to execute, we decoupled the LLM query rate from the EnergyPlus timestep. The AI is only invoked once per simulated hour. During the intermediate timesteps, the building "coasts" on the agent's previously defined setpoints, perfectly balancing control granularity with compute limitations.
*   **Warmup Snooze:** EnergyPlus requires multi-day physics warmup cycles to reach thermal equilibrium. We implemented a bypass guardrail (`warmup_flag` check) to prevent the system from querying the LLM during these dummy days, drastically reducing total execution time.

## 3. Prompt Engineering Strategy
The cognitive engine utilizes **greedy decoding** (`temperature: 0.0`) to ensure deterministic, highly repeatable control outputs rather than creative text generation. 

The prompt dynamically injects live telemetry (Day, Hour, and Zone Temperatures) and enforces a strict structural constraint. The model is instructed to output only valid JSON containing two keys:
1.  `reasoning`: A chain-of-thought explanation for its decision, enhancing system observability.
2.  `actions`: An array of tool-call payloads mapping specific building zones to target temperatures.

## 4. Handling Long Simulation Logs
Traditional Building Management Systems (BMS) output massive historical data files. By utilizing the `pyenergyplus` state manager, Eco-Loop processes telemetry strictly in the present moment. Historical analysis is reserved exclusively for the post-simulation evaluation script (`dashboard.py`), which isolates `Electricity:Facility` and `Zone Mean Air Temperature` vectors to compute absolute kWh reductions against the baseline.