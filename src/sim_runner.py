import os
import sys
import pandas as pd
from src.config import IDF_PATH, EPW_PATH, OUTPUT_DIR

try:
    from pyenergyplus.api import EnergyPlusAPI
except ImportError:
    print("❌ Error: pyenergyplus not found.")
    sys.exit(1)

class EcoLoopRunner:
    def __init__(self):
        self.api = EnergyPlusAPI()
        self.state = self.api.state_manager.new_state()
        self.handles_initialized = False
        self.handles = {}
        
        # New: Data storage for our custom CSV
        self.history = []
        self.last_logged_hour = -1

    def init_handles(self, state):
        self.handles["temp_Core_bottom"] = self.api.exchange.get_variable_handle(
            state, "Zone Mean Air Temperature", "Core_bottom"
        )
        self.handles["elec_facility"] = self.api.exchange.get_meter_handle(
            state, "Electricity:Facility"
        )
        self.handles_initialized = True

    def my_callback(self, state):
        if not self.api.exchange.api_data_fully_ready(state) or self.api.exchange.warmup_flag(state):
            return
            
        if not self.handles_initialized:
            self.init_handles(state)
            
        day = self.api.exchange.day_of_year(state)
        hour = self.api.exchange.hour(state)
        
        # Log data exactly once per simulated hour
        if hour != self.last_logged_hour:
            self.last_logged_hour = hour
            
            temp = self.api.exchange.get_variable_value(state, self.handles["temp_Core_bottom"])
            elec = self.api.exchange.get_meter_value(state, self.handles["elec_facility"])
            
            self.history.append({
                "Day": day,
                "Hour": hour,
                "Core_bottom:Zone Mean Air Temperature": temp,
                "Electricity:Facility": elec
            })

    def run(self):
        print("Starting Baseline Simulation...")
        self.api.runtime.callback_end_zone_timestep_after_zone_reporting(self.state, self.my_callback)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.api.runtime.run_energyplus(self.state, ['-w', EPW_PATH, '-d', OUTPUT_DIR, IDF_PATH])
        
        # Save our custom CSV!
        df = pd.DataFrame(self.history)
        csv_path = os.path.join(OUTPUT_DIR, "eplusout.csv")
        df.to_csv(csv_path, index=False)
        print(f"✅ Baseline Data saved to {csv_path}")

if __name__ == "__main__":
    runner = EcoLoopRunner()
    runner.run()