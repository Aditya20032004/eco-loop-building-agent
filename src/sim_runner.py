import os
import sys
import pandas as pd
from src.config import IDF_PATH, EPW_PATH, OUTPUT_DIR

try:
    from pyenergyplus.api import EnergyPlusAPI
except ImportError:
    print("❌ Error: pyenergyplus not found.")
    sys.exit(1)

class EcoLoopBaselineRunner:
    def __init__(self):
        self.api = EnergyPlusAPI()
        self.state = self.api.state_manager.new_state()
        self.handles_initialized = False
        self.handles = {}
        
        # Track all 7 spatial zones to match the AI orchestrator
        self.zones = [
            "Core_bottom",
            "Core_mid",
            "Core_top",
            "Perimeter_mid_ZN_1",
            "Perimeter_mid_ZN_2",
            "Perimeter_mid_ZN_3",
            "Perimeter_mid_ZN_4"
        ]
        
        self.history = []
        self.last_logged_hour = -1

    def init_handles(self, state):
        for zone in self.zones:
            self.handles[f"temp_{zone}"] = self.api.exchange.get_variable_handle(
                state, "Zone Mean Air Temperature", zone
            )
        self.handles["elec_facility"] = self.api.exchange.get_meter_handle(
            state, "Electricity:Facility"
        )
        self.handles_initialized = True

    def _get_simulated_carbon_intensity(self, hour: int) -> float:
        """Matches the exact carbon profile from the AI orchestrator for an apples-to-apples comparison."""
        if 15 <= hour <= 20:
            return 550.0  # Peak dirty grid hours
        elif 10 <= hour <= 14:
            return 300.0  # Solar midday dip
        else:
            return 400.0  # Baseline grid

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
            
            elec = self.api.exchange.get_meter_value(state, self.handles["elec_facility"])
            carbon_intensity = self._get_simulated_carbon_intensity(hour)
            
            history_entry = {
                "Day": day,
                "Hour": hour,
                "Electricity:Facility": elec,
                "Carbon_Intensity": carbon_intensity
            }
            
            # Dynamically pull temps for all 7 zones
            for zone in self.zones:
                temp = self.api.exchange.get_variable_value(state, self.handles[f"temp_{zone}"])
                history_entry[f"{zone}:Zone Mean Air Temperature"] = temp
            
            self.history.append(history_entry)

    def run(self):
        print("Starting 7-Zone Baseline Simulation...")
        self.api.runtime.callback_end_zone_timestep_after_zone_reporting(self.state, self.my_callback)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.api.runtime.run_energyplus(self.state, ['-w', EPW_PATH, '-d', OUTPUT_DIR, IDF_PATH])
        
        # Save explicitly as baseline_eplusout.csv for app.py
        df = pd.DataFrame(self.history)
        csv_path = os.path.join(OUTPUT_DIR, "eplusout.csv")
        df.to_csv(csv_path, index=False)
        print(f"✅ Baseline Data saved to {csv_path}")

if __name__ == "__main__":
    runner = EcoLoopBaselineRunner()
    runner.run()