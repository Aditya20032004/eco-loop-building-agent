import os
import sys
import json
import asyncio
import re
import pandas as pd
from src.config import IDF_PATH, EPW_PATH, OUTPUT_DIR
from src.agent import EcoLoopAgent
from src.tools import BuildingTools
from src.mcp_client import send_mcp_command

try:
    from pyenergyplus.api import EnergyPlusAPI
except ImportError:
    print("❌ Error: pyenergyplus not found.")
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
        
        # Target all spatial zones in the building model
        self.zones = [
            "Core_bottom",
            "Core_mid",
            "Core_top",
            "Perimeter_mid_ZN_1",
            "Perimeter_mid_ZN_2",
            "Perimeter_mid_ZN_3",
            "Perimeter_mid_ZN_4"
        ]
        
        # STATE MEMORY: Track previous setpoints to allow 1°C gradual ramps
        self.last_setpoints = {zone: 24.0 for zone in self.zones}
        
        self.history = []
        self.agent_logs = []

    def init_handles(self, state):
        for zone in self.zones:
            self.handles[f"temp_{zone}"] = self.api.exchange.get_variable_handle(state, "Zone Mean Air Temperature", zone)
            self.handles[f"setpoint_{zone}"] = self.api.exchange.get_actuator_handle(state, "Zone Temperature Control", "Cooling Setpoint", zone)
            self.handles[f"occupancy_{zone}"] = self.api.exchange.get_variable_handle(state, "Zone People Occupant Count", zone)
            
        self.handles["elec_facility"] = self.api.exchange.get_meter_handle(state, "Electricity:Facility")
        self.handles["outdoor_temp"] = self.api.exchange.get_variable_handle(state, "Site Outdoor Air Drybulb Temperature", "Environment")
        self.handles["solar_rad"] = self.api.exchange.get_variable_handle(state, "Site Direct Solar Radiation Rate per Area", "Environment")
        
        invalid_handles = [k for k, v in self.handles.items() if v == -1]
        if invalid_handles:
            raise RuntimeError(f"Failed to resolve handles: {invalid_handles}. Check zone names and .idf actuator objects.")
            
        self.handles_initialized = True

    def _get_simulated_carbon_intensity(self, hour: int) -> float:
        if 15 <= hour <= 20:
            return 550.0
        elif 10 <= hour <= 14:
            return 300.0
        else:
            return 400.0

    def _get_predictive_forecast(self, hour: int, current_temp: float, solar: float) -> dict:
        is_heating_up = 9 <= hour <= 15
        expected_temp_trend = "RISING" if is_heating_up else "COOLING"
        
        return {
            "trend": expected_temp_trend,
            "next_hour_estimated_temp": round(current_temp + (0.8 if is_heating_up else -0.5), 2),
            "upcoming_peak_solar": True if solar > 200 and 11 <= hour <= 16 else False,
            "recommendation_hint": "PRE_COOL" if is_heating_up and solar > 150 else "COAST"
        }

    def orchestration_callback(self, state):
        if not self.api.exchange.api_data_fully_ready(state) or self.api.exchange.warmup_flag(state):
            return
            
        if not self.handles_initialized:
            self.init_handles(state)
        
        day = self.api.exchange.day_of_year(state)
        hour = self.api.exchange.hour(state)
        
        if hour != self.last_action_hour:
            self.last_action_hour = hour
            
            # Read meter in Joules and convert to kWh
            elec_joules = self.api.exchange.get_meter_value(state, self.handles["elec_facility"])
            elec = elec_joules / 3600000.0  
            
            out_temp = self.api.exchange.get_variable_value(state, self.handles["outdoor_temp"])
            solar = self.api.exchange.get_variable_value(state, self.handles["solar_rad"])
            carbon_intensity = self._get_simulated_carbon_intensity(hour)
            
            zone_states = {}
            for zone in self.zones:
                t_val = self.api.exchange.get_variable_value(state, self.handles[f"temp_{zone}"])
                occ_val = self.api.exchange.get_variable_value(state, self.handles[f"occupancy_{zone}"])
                
                # UNIT DEBUGGER
                if day == 1 and hour == 1 and zone == "Core_bottom":
                    print(f"\n  [DEBUG] Raw Temp for {zone}: {t_val} (If > 50, it is Fahrenheit!)\n")
                
                # DETERMINISTIC LOOKAHEAD: DOE Medium Office schedule runs 8AM-6PM. 
                # If current hour is 7, next hour is 8, meaning occupancy is approaching.
                next_occ = 1 if 7 <= hour <= 17 else 0

                zone_states[zone] = {
                    "current_temp": round(t_val, 2),
                    "occupancy": round(occ_val, 0),
                    "last_commanded_setpoint": self.last_setpoints[zone],
                    "next_hour_occupancy": next_occ
                }
            
            forecast = self._get_predictive_forecast(hour, out_temp, solar)
            
            history_entry = {
                "Day": day,
                "Hour": hour,
                "Electricity:Facility": elec,
                "Carbon_Intensity": carbon_intensity
            }
            for zone in self.zones:
                history_entry[f"{zone}:Zone Mean Air Temperature"] = zone_states[zone]["current_temp"]
                
            self.history.append(history_entry)
            
            telemetry = {
                "day": day, 
                "time": f"{hour:02d}:00", 
                "zones": zone_states,
                "weather": {
                    "outdoor_temp": round(out_temp, 2),
                    "solar_radiation": round(solar, 2)
                },
                "forecast": forecast,
                "grid_metrics": {
                    "carbon_intensity_g_co2_kwh": carbon_intensity,
                    "grid_status": "PEAK_DIRTY" if carbon_intensity > 500 else "NORMAL"
                }
            }
            
            print(f"\n--- [Day {day}, Hour {hour:02d}:00] Firing Predictive Multi-Zone Agent ---")
            
            prompt = self.tools.generate_agent_prompt(json.dumps(telemetry))
            llm_response, _ = self.agent.prompt_llm(prompt)
            
            parsed_actions = []
            try:
                clean_json = llm_response.replace('```json', '').replace('```', '').strip()
                try:
                    decision = json.loads(clean_json)
                except json.JSONDecodeError:
                    match = re.search(r'\{.*\}', clean_json, re.DOTALL)
                    if match:
                        decision = json.loads(match.group(0))
                    else:
                        raise ValueError("No JSON object detected in LLM response.")
                
                parsed_actions = decision.get("actions", [])
                for action in parsed_actions:
                    zone = action.get("zone")
                    if zone in self.zones:
                        raw_target = action.get("target_temp")
                        safe_target = max(18.0, min(30.0, float(raw_target)))
                        
                        mcp_response_text = asyncio.run(send_mcp_command(zone, safe_target))
                        if mcp_response_text:
                            self.api.exchange.set_actuator_value(state, self.handles[f"setpoint_{zone}"], safe_target)
                            
                            # MEMORY UPDATE: Record the successful command so the next hour can step down from it
                            self.last_setpoints[zone] = safe_target
            except Exception as e:
                print(f"  ⚠️ Action Execution Error: {e}")

            self.agent_logs.append({
                "day": day,
                "hour": hour,
                "telemetry": telemetry,
                "prompt_sent": prompt,
                "raw_llm_response": llm_response,
                "parsed_actions": parsed_actions
            })

    def run(self):
        print("Starting Predictive Multi-Zone AI Orchestrator...")
        self.api.runtime.callback_after_predictor_after_hvac_managers(self.state, self.orchestration_callback)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.api.runtime.run_energyplus(self.state, ['-w', EPW_PATH, '-d', OUTPUT_DIR, IDF_PATH])
        
        df = pd.DataFrame(self.history)
        csv_path = os.path.join(OUTPUT_DIR, "eplusout.csv")
        df.to_csv(csv_path, index=False)
        
        logs_path = os.path.join(OUTPUT_DIR, "agent_logs.json")
        with open(logs_path, "w") as f:
            json.dump(self.agent_logs, f, indent=2)
            
        print(f"✅ AI Data saved to {csv_path} and Agent Logs saved to {logs_path}")

if __name__ == "__main__":
    orchestrator = EcoLoopOrchestrator()
    orchestrator.run()