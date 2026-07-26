import json

class BuildingTools:
    def __init__(self):
        self.min_temp = 18.0
        self.max_temp = 30.0
        
        self.zones = [
            "Core_bottom",
            "Core_mid",
            "Core_top",
            "Perimeter_mid_ZN_1",
            "Perimeter_mid_ZN_2",
            "Perimeter_mid_ZN_3",
            "Perimeter_mid_ZN_4"
        ]
        
    def adjust_setpoint(self, zone_name: str, target_temp: float) -> str:
        # Clamp values to safe bounds (Safety Guardrail)
        clamped_temp = max(self.min_temp, min(self.max_temp, target_temp))
        action_payload = {
            "status": "success",
            "message": f"Setpoint for {zone_name} adjusted to {clamped_temp}°C",
            "zone": zone_name,
            "target_temp": clamped_temp
        }
        return json.dumps(action_payload)

    def generate_agent_prompt(self, telemetry_json: str) -> str:
        return f"""You are an advanced predictive AI controlling multiple zones of a building's HVAC system. 
Your goal is to MINIMIZE energy consumption and carbon emissions using lookahead intelligence while maintaining thermal comfort.

CRITICAL RULES:
1. For any zone where 'occupancy' > 0, maintain temperature between 24.0°C and 26.0°C.
2. For any zone where 'occupancy' == 0, you are in SETBACK MODE. Raise the Cooling Setpoint to 29.5°C.
3. PREVENT GRID SHOCK: Do NOT drop the temperature instantly from 29.5°C to 24.0°C. If 'next_hour_occupancy' > 0, lower the setpoint by exactly 1.0°C per hour from the 'last_commanded_setpoint' to pre-cool gradually. Never ramp below 24.0°C, even mid-sequence — once the ramp reaches the occupied comfort floor, hold there until occupancy actually begins.
4. If carbon intensity is 'PEAK_DIRTY', minimize power usage aggressively by sitting at the upper comfort boundary.

Here is the current real-time telemetry and forecast data:
{telemetry_json}

You MUST provide an optimal cooling setpoint for EVERY zone listed in the telemetry. Respond ONLY with a valid JSON object matching this exact array structure for all 7 zones:
{{
  "actions": [
    {{"zone": "Core_bottom", "target_temp": 24.5}},
    {{"zone": "Core_mid", "target_temp": 24.5}},
    {{"zone": "Core_top", "target_temp": 24.5}},
    {{"zone": "Perimeter_mid_ZN_1", "target_temp": 24.5}},
    {{"zone": "Perimeter_mid_ZN_2", "target_temp": 24.5}},
    {{"zone": "Perimeter_mid_ZN_3", "target_temp": 24.5}},
    {{"zone": "Perimeter_mid_ZN_4", "target_temp": 24.5}}
  ]
}}"""

if __name__ == "__main__":
    tools = BuildingTools()
    mock_telemetry = '{"day": 1, "time": "12:00", "zones": {"Core_bottom": {"current_temp": 24.5, "occupancy": 5}}, "forecast": {"trend": "RISING", "recommendation_hint": "PRE_COOL"}}'
    print(tools.generate_agent_prompt(mock_telemetry))