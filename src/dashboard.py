import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from src.config import PROJECT_ROOT

BASELINE_DIR = os.path.join(PROJECT_ROOT, 'output', 'baseline')
AI_DIR = os.path.join(PROJECT_ROOT, 'output', 'ai')

BASELINE_CSV = os.path.join(BASELINE_DIR, 'eplusout.csv')
AI_CSV = os.path.join(AI_DIR, 'eplusout.csv')

def load_data(filepath):
    if not os.path.exists(filepath):
        print(f"❌ Error: Cannot find {filepath}")
        return None
    return pd.read_csv(filepath)

def find_column(df, keyword):
    matches = [col for col in df.columns if keyword.lower() in col.lower()]
    return matches[0] if matches else None

def generate_dashboard():
    print("Loading simulation results...")
    df_base = load_data(BASELINE_CSV)
    df_ai = load_data(AI_CSV)

    if df_base is None or df_ai is None:
        print("Please ensure both baseline and ai eplusout.csv files exist.")
        sys.exit(1)

    energy_col_base = find_column(df_base, 'Electricity:Facility')
    energy_col_ai = find_column(df_ai, 'Electricity:Facility')

    if not energy_col_base or not energy_col_ai:
        print("⚠️ Warning: Could not find 'Electricity:Facility' in CSV headers.")
        print("Falling back to generic HVAC energy if available...")
        energy_col_base = find_column(df_base, 'HVAC Electric')
        energy_col_ai = find_column(df_ai, 'HVAC Electric')

    temp_col_base = find_column(df_base, 'Core_bottom:Zone Mean Air Temperature')
    temp_col_ai = find_column(df_ai, 'Core_bottom:Zone Mean Air Temperature')

    if energy_col_base and energy_col_ai:
        base_kwh = df_base[energy_col_base].sum() / 3600000
        ai_kwh = df_ai[energy_col_ai].sum() / 3600000
        savings_pct = ((base_kwh - ai_kwh) / base_kwh) * 100 if base_kwh > 0 else 0
        
        print(f"\n📊 --- SAVINGS REPORT ---")
        print(f"Baseline Energy: {base_kwh:.2f} kWh")
        print(f"AI-Driven Energy: {ai_kwh:.2f} kWh")
        print(f"Total Reduction: {savings_pct:.1f}%")
    else:
        print("❌ Cannot calculate energy savings due to missing meter data in CSV.")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    df_base['Cumulative_kWh'] = df_base[energy_col_base].cumsum() / 3600000
    df_ai['Cumulative_kWh'] = df_ai[energy_col_ai].cumsum() / 3600000
    
    ax1.plot(df_base.index, df_base['Cumulative_kWh'], label='Baseline (Rule-based)', color='gray', linestyle='--')
    ax1.plot(df_ai.index, df_ai['Cumulative_kWh'], label=f'Eco-Loop AI (-{savings_pct:.1f}%)', color='green', linewidth=2)
    ax1.set_ylabel('Cumulative Energy (kWh)')
    ax1.set_title('Energy Consumption Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    if temp_col_base and temp_col_ai:
        ax2.plot(df_base.index, df_base[temp_col_base], label='Baseline Temp', color='gray', alpha=0.5)
        ax2.plot(df_ai.index, df_ai[temp_col_ai], label='AI Temp', color='blue', alpha=0.8)
        
        ax2.axhline(25.0, color='red', linestyle=':', label='Max Comfort (25°C)')
        ax2.axhline(20.0, color='teal', linestyle=':', label='Min Comfort (20°C)')
        ax2.fill_between(df_base.index, 20.0, 25.0, color='green', alpha=0.1, label='Comfort Zone')
        
        ax2.set_ylabel('Zone Temperature (°C)')
        ax2.set_xlabel('Simulation Timesteps')
        ax2.set_title('Thermal Comfort Maintenance (Core_bottom)')
        ax2.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(PROJECT_ROOT, 'output', 'savings_dashboard.png')
    plt.savefig(plot_path)
    print(f"\n✅ Dashboard saved to: {plot_path}")
    plt.show()

if __name__ == "__main__":
    generate_dashboard()