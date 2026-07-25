import os
import sys
import json
import pandas as pd
from src.config import IDF_PATH, EPW_PATH, OUTPUT_DIR
from src.agent import EcoLoopAgent
from src.tools import BuildingTools

try:
    from pyenergyplus.api import EnergyPlusAPI
except ImportError:
    sys.exit(1)

class EcoLoopOrchestrator:
    def __init__(self):
        self.api = EnergyPlusAPI()
        self.state = self.api.state_manager.new_state()
        self.agent = EcoLoopAgent()
        self.tools = BuildingTools()
        
        self.handles_initialized = False
        self.handles = {}
        self.last_action_hour = -1  
        
        # New: Data storage for our custom CSV
        self.history = []

    def init_handles(self, state):
        self.handles["temp_Core_bottom"] = self.api.exchange.get_variable_handle(state, "Zone Mean Air Temperature", "Core_bottom")
        self.handles["temp_Core_mid"] = self.api.exchange.get_variable_handle(state, "Zone Mean Air Temperature", "Core_mid")
        self.handles["setpoint_Core_bottom"] = self.api.exchange.get_actuator_handle(state, "Zone Temperature Control", "Cooling Setpoint", "Core_bottom")
        self.handles["elec_facility"] = self.api.exchange.get_meter_handle(state, "Electricity:Facility")
        self.handles_initialized = True

    def orchestration_callback(self, state):
        if not self.api.exchange.api_data_fully_ready(state) or self.api.exchange.warmup_flag(state):
            return
            
        if not self.handles_initialized:
            self.init_handles(state)
        
        day = self.api.exchange.day_of_year(state)
        hour = self.api.exchange.hour(state)
        
        if hour != self.last_action_hour:
            self.last_action_hour = hour
            
            # 1. Read Current State
            t_bot = self.api.exchange.get_variable_value(state, self.handles["temp_Core_bottom"])
            t_mid = self.api.exchange.get_variable_value(state, self.handles["temp_Core_mid"])
            elec = self.api.exchange.get_meter_value(state, self.handles["elec_facility"])
            
            # 2. Log Data for Dashboard
            self.history.append({
                "Day": day,
                "Hour": hour,
                "Core_bottom:Zone Mean Air Temperature": t_bot,
                "Electricity:Facility": elec
            })
            
            # 3. Fire AI Agent
            telemetry = {"day": day, "time": f"{hour:02d}:00", "temperatures": {"temp_Core_bottom": round(t_bot, 2), "temp_Core_mid": round(t_mid, 2)}}
            print(f"\n--- [Day {day}, Hour {hour:02d}:00] Firing Cognitive Agent ---")
            
            prompt = self.tools.generate_agent_prompt(json.dumps(telemetry))
            llm_response, _ = self.agent.prompt_llm(prompt)
            
            try:
                decision = json.loads(llm_response.replace('```json', '').replace('```', '').strip())
                for action in decision.get("actions", []):
                    zone = action.get("zone")
                    if zone == "Core_bottom":
                        safe_temp = json.loads(self.tools.adjust_setpoint(zone, action.get("target_temp")))["target_temp"]
                        self.api.exchange.set_actuator_value(state, self.handles["setpoint_Core_bottom"], safe_temp)
            except:
                pass # Fallback to previous setpoint if JSON fails

    def run(self):
        print("Starting AI Orchestrator...")
        self.api.runtime.callback_after_predictor_after_hvac_managers(self.state, self.orchestration_callback)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.api.runtime.run_energyplus(self.state, ['-w', EPW_PATH, '-d', OUTPUT_DIR, IDF_PATH])
        
        # Save our custom CSV!
        df = pd.DataFrame(self.history)
        csv_path = os.path.join(OUTPUT_DIR, "eplusout.csv")
        df.to_csv(csv_path, index=False)
        print(f"✅ AI Data saved to {csv_path}")

if __name__ == "__main__":
    orchestrator = EcoLoopOrchestrator()
    orchestrator.run()