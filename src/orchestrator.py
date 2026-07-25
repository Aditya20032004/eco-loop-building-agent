import os
import sys
import json
from src.config import IDF_PATH, EPW_PATH, OUTPUT_DIR
from src.agent import EcoLoopAgent
from src.tools import BuildingTools

try:
    from pyenergyplus.api import EnergyPlusAPI
except ImportError:
    print("❌ Error: pyenergyplus not found. Check EPLUS_DIR in config.py")
    sys.exit(1)

class EcoLoopOrchestrator:
    def __init__(self):
        self.api = EnergyPlusAPI()
        self.state = self.api.state_manager.new_state()
        
        self.agent = EcoLoopAgent()
        self.tools = BuildingTools()
        
        self.handles_initialized = False
        self.var_handles = {}  
        self.act_handles = {}  
        
        self.zones_to_monitor = ["Core_bottom", "Core_mid"]
        self.last_action_hour = -1  

    def init_handles(self, state):
        for zone in self.zones_to_monitor:
            v_handle = self.api.exchange.get_variable_handle(
                state, "Zone Mean Air Temperature", zone
            )
            if v_handle != -1:
                self.var_handles[f"temp_{zone}"] = v_handle
            else:
                print(f"⚠️ Warning: Could not get variable handle for {zone}")

            a_handle = self.api.exchange.get_actuator_handle(
                state, "Zone Temperature Control", "Cooling Setpoint", zone
            )
            if a_handle != -1:
                self.act_handles[f"setpoint_{zone}"] = a_handle
            else:
                print(f"⚠️ Warning: Could not get actuator handle for {zone} Cooling Setpoint")
                
        self.handles_initialized = True
        print("✅ Telemetry and Actuator handles initialized.")

    def orchestration_callback(self, state):
        if not self.api.exchange.api_data_fully_ready(state):
            return
            
        # ⚠️ NEW GUARDRAIL: Skip the LLM completely during E+ warmup days
        if self.api.exchange.warmup_flag(state):
            return
            
        if not self.handles_initialized:
            self.init_handles(state)
        
        day = self.api.exchange.day_of_year(state)
        hour = self.api.exchange.hour(state)
        
        if hour != self.last_action_hour:
            self.last_action_hour = hour
            
            telemetry = {
                "day": day,
                "time": f"{hour:02d}:00",
                "temperatures": {}
            }
            
            for key, handle in self.var_handles.items():
                val = self.api.exchange.get_variable_value(state, handle)
                telemetry["temperatures"][key] = round(val, 2)
                
            print(f"\n--- [Day {day}, Hour {hour:02d}:00] Firing Cognitive Agent ---")
            print(f"📡 Telemetry: {json.dumps(telemetry)}")
            
            prompt = self.tools.generate_agent_prompt(json.dumps(telemetry))
            llm_response, latency = self.agent.prompt_llm(prompt)
            print(f"🧠 Agent Reasoning (Latency: {latency:.2f}s):\n{llm_response}")
            
            try:
                clean_response = llm_response.replace('```json', '').replace('```', '').strip()
                decision = json.loads(clean_response)
                actions = decision.get("actions", [])
                
                for action in actions:
                    zone = action.get("zone")
                    target_temp = action.get("target_temp")
                    
                    if zone and target_temp and f"setpoint_{zone}" in self.act_handles:
                        json_result = self.tools.adjust_setpoint(zone, target_temp)
                        safe_temp = json.loads(json_result)["target_temp"]
                        
                        self.api.exchange.set_actuator_value(
                            state, 
                            self.act_handles[f"setpoint_{zone}"], 
                            safe_temp
                        )
                        print(f"✅ Executed: Set {zone} cooling setpoint to {safe_temp}°C")
                    else:
                        print(f"⚠️ Ignored Action: Invalid zone or missing actuator for '{zone}'")
                        
            except json.JSONDecodeError:
                print("❌ Parse Error: Agent did not return valid JSON. Coasting on previous setpoints.")

    def run(self):
        print("Starting Eco-Loop Orchestrator...")
        
        self.api.runtime.callback_after_predictor_after_hvac_managers(
            self.state, self.orchestration_callback
        )
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        cmd_args = ['-w', EPW_PATH, '-d', OUTPUT_DIR, IDF_PATH]
        
        result = self.api.runtime.run_energyplus(self.state, cmd_args)
        
        print(f"\n🏁 Simulation finished with exit code {result}")
        self.api.state_manager.delete_state(self.state)

if __name__ == "__main__":
    orchestrator = EcoLoopOrchestrator()
    orchestrator.run()