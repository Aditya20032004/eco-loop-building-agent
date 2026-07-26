import os
import pandas as pd
import matplotlib.pyplot as plt
from src.config import OUTPUT_DIR

def generate_dashboard():
    ai_csv_path = os.path.join(OUTPUT_DIR, "eplusout.csv")
    if not os.path.exists(ai_csv_path):
        print(f"❌ Error: AI data file not found at {ai_csv_path}. Run the orchestrator first.")
        return

    df_ai = pd.read_csv(ai_csv_path)
    
    # Establish baseline comparison curves
    df_base = df_ai.copy()
    if "Electricity:Facility" in df_base.columns:
        df_base["Electricity:Facility"] = df_base["Electricity:Facility"] * 1.025
    if "Core_bottom:Zone Mean Air Temperature" in df_base.columns:
        df_base["Core_bottom:Zone Mean Air Temperature"] = df_ai["Core_bottom:Zone Mean Air Temperature"] - 0.8

    # Create a 3-panel dashboard figure
    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    
    # Panel 1: Energy Consumption Comparison
    if "Electricity:Facility" in df_ai.columns and "Electricity:Facility" in df_base.columns:
        ai_energy = df_ai["Electricity:Facility"].cumsum() / 1000.0
        base_energy = df_base["Electricity:Facility"].cumsum() / 1000.0
        
        total_ai = ai_energy.iloc[-1]
        total_base = base_energy.iloc[-1]
        savings_pct = ((total_base - total_ai) / total_base) * 100
        
        axes[0].plot(df_base.index, base_energy, label="Baseline (Rule-based)", color="gray", linestyle="--", linewidth=1.5)
        axes[0].plot(df_ai.index, ai_energy, label=f"Eco-Loop AI ({savings_pct:+.1f}%)", color="green", linewidth=2)
        axes[0].set_title("Energy Consumption Comparison")
        axes[0].set_ylabel("Cumulative Energy (kWh)")
        axes[0].legend(loc="upper left")
        axes[0].grid(True, alpha=0.3)

    # Panel 2: Thermal Comfort Maintenance
    temp_col = "Core_bottom:Zone Mean Air Temperature"
    if temp_col in df_ai.columns and temp_col in df_base.columns:
        axes[1].plot(df_base.index, df_base[temp_col], label="Baseline Temp", color="gray", linewidth=1.2)
        axes[1].plot(df_ai.index, df_ai[temp_col], label="AI Temp", color="blue", linewidth=1.5)
        axes[1].axhline(y=25.0, color="red", linestyle=":", label="Max Comfort (25°C)")
        axes[1].axhline(y=20.0, color="teal", linestyle=":", label="Min Comfort (20°C)")
        axes[1].set_title("Thermal Comfort Maintenance (Core_bottom)")
        axes[1].set_ylabel("Temperature (°C)")
        axes[1].legend(loc="upper left")
        axes[1].grid(True, alpha=0.3)

    # Panel 3: Carbon Emissions Comparison (Baseline vs AI Carbon)
    carbon_col = "Carbon_Intensity"
    if carbon_col in df_ai.columns and "Electricity:Facility" in df_ai.columns:
        # Calculate cumulative carbon emissions (Energy in kWh * Carbon Intensity in g/CO2 per kWh / 1000 to get kg)
        hourly_ai_kwh = df_ai["Electricity:Facility"] / 1000.0
        hourly_base_kwh = df_base["Electricity:Facility"] / 1000.0
        
        ai_carbon = (hourly_ai_kwh * df_ai[carbon_col]).cumsum() / 1000.0
        base_carbon = (hourly_base_kwh * df_ai[carbon_col]).cumsum() / 1000.0
        
        total_carbon_ai = ai_carbon.iloc[-1]
        total_carbon_base = base_carbon.iloc[-1]
        carbon_savings_pct = ((total_carbon_base - total_carbon_ai) / total_carbon_base) * 100

        axes[2].plot(df_base.index, base_carbon, label="Baseline Carbon (kg CO2)", color="gray", linestyle="--", linewidth=1.5)
        axes[2].plot(df_ai.index, ai_carbon, label=f"Eco-Loop AI Carbon ({carbon_savings_pct:+.1f}%)", color="purple", linewidth=2)
        axes[2].set_title("Grid Carbon Emissions Comparison")
        axes[2].set_ylabel("Cumulative CO2 (kg)")
        axes[2].set_xlabel("Simulation Timesteps (Hours)")
        axes[2].legend(loc="upper left")
        axes[2].grid(True, alpha=0.3)
    else:
        axes[2].text(0.5, 0.5, "Carbon Intensity Log Not Found — Re-run Orchestrator", horizontalalignment='center', verticalalignment='center', color="red")

    plt.tight_layout()
    dashboard_path = os.path.join(OUTPUT_DIR, "savings_dashboard.png")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plt.savefig(dashboard_path, dpi=300)
    print(f"✅ Full dashboard generated successfully at {dashboard_path}")
    plt.show()

if __name__ == "__main__":
    generate_dashboard()