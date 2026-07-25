import os
import sys
import json
from src.config import IDF_PATH, EPW_PATH, OUTPUT_DIR

try:
    from pyenergyplus.api import EnergyPlusAPI
except ImportError:
    print("❌ Error: Could not import pyenergyplus. Check EPLUS_DIR in config.py")
    sys.exit(1)

class EcoLoopRunner:
    def __init__(self):
        self.api = EnergyPlusAPI()
        self.state = self.api.state_manager.new_state()
        
        self.handles_initialized = False
        self.handles = {}
        
        self.zones_to_monitor = ["Core_bottom", "Core_mid"]
        self.last_printed_day = -1  

    def init_handles(self, state):
        for zone in self.zones_to_monitor:
            handle = self.api.exchange.get_variable_handle(
                state, 
                "Zone Mean Air Temperature", 
                zone
            )
            
            if handle == -1:
                print(f"⚠️ Warning: Could not get handle for temperature in {zone}")
            else:
                self.handles[f"temp_{zone}"] = handle
                
        self.handles_initialized = True
        print("✅ Telemetry handles initialized successfully.")

    def my_callback(self, state):
        if not self.api.exchange.api_data_fully_ready(state):
            return
            
        if not self.handles_initialized:
            self.init_handles(state)
        
        day = self.api.exchange.day_of_year(state)
        hour = self.api.exchange.hour(state)
        minute = self.api.exchange.minutes(state)
        
        telemetry = {
            "day": day,
            "time": f"{hour:02d}:{minute:02d}",
            "temperatures": {}
        }
        
        for key, handle in self.handles.items():
            val = self.api.exchange.get_variable_value(state, handle)
            telemetry["temperatures"][key] = round(val, 2)
            
        if hour == 12 and day != self.last_printed_day:
            print(f"Live Telemetry -> {json.dumps(telemetry)}")
            self.last_printed_day = day

    def run(self):
        print("Starting EnergyPlus Baseline Simulation with Telemetry...")
        
        self.api.runtime.callback_begin_zone_timestep_after_init_heat_balance(
            self.state, self.my_callback
        )
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        cmd_args = ['-w', EPW_PATH, '-d', OUTPUT_DIR, IDF_PATH]
        
        result = self.api.runtime.run_energyplus(self.state, cmd_args)
        
        print(f"\n✅ Simulation finished with exit code {result}")
        self.api.state_manager.delete_state(self.state)

if __name__ == "__main__":
    runner = EcoLoopRunner()
    runner.run()