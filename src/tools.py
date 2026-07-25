import json

class BuildingTools:
    def __init__(self):
        # Define valid ranges to prevent the LLM from freezing or overheating the building!
        self.min_temp = 18.0  #Celsius
        self.max_temp = 28.0  # Celsius
        
    def adjust_setpoint(self, zone_name: str, target_temp: float) -> str:
        """
        Tool function: Adjusts the cooling/heating setpoint for a given zone.
        """
        # Clamp values to safe human-comfort bounds (Safety Guardrail)
        clamped_temp = max(self.min_temp, min(self.max_temp, target_temp))
        
        action_payload = {
            "status": "success",
            "message": f"Setpoint for {zone_name} adjusted to {clamped_temp}°C",
            "zone": zone_name,
            "target_temp": clamped_temp
        }
        return json.dumps(action_payload)

    def generate_agent_prompt(self, telemetry_json: str) -> str:
        """
        Constructs a strict prompt instructing Qwen to act as an energy control agent.
        """
        prompt = f"""You are an autonomous building energy control agent. Your goal is to minimize energy consumption while maintaining indoor thermal comfort between 20°C and 25°C.

Current Building Telemetry:
{telemetry_json}

You must respond ONLY with a valid JSON object containing your control decision. Do not include markdown code blocks (like ```json) or conversational filler. 

Format:
{{
  "reasoning": "Brief explanation of your decision based on temperature",
  "actions": [
    {{
      "zone": "Core_bottom",
      "target_temp": 23.5
    }}
  ]
}}
"""
        return prompt

if __name__ == "__main__":
    # Quick sanity test of our tool parser
    tools = BuildingTools()
    mock_telemetry = '{"day": 1, "time": "12:00", "temperatures": {"temp_Core_bottom": 26.5}}'
    prompt = tools.generate_agent_prompt(mock_telemetry)
    print("Generated Prompt Preview:")
    print(prompt)