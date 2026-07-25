import os
import sys
from config import IDF_PATH, EPLUS_DIR, DATA_DIR

try:
    from eppy.modeleditor import IDF
except ImportError:
    print("❌ Error: eppy not installed. Run: pip install eppy")
    sys.exit(1)

# Tell eppy where the EnergyPlus schema dictionary (.idd) lives
IDF.setiddname(os.path.join(EPLUS_DIR, 'Energy+.idd'))

def prepare_idf():
    print(f"Loading original IDF: {IDF_PATH}")
    idf = IDF(IDF_PATH)
    
    # --- 1. Shorten the Run Period to 3 Days ---
    run_periods = idf.idfobjects['RunPeriod']
    if not run_periods:
        print("❌ Error: No RunPeriod found in IDF.")
        return
        
    rp = run_periods[0]
    rp.Begin_Month = 7
    rp.Begin_Day_of_Month = 1
    rp.End_Month = 7
    rp.End_Day_of_Month = 3
    
    # --- 2. Force CSV Output Logging ---
    print("Injecting Output:Variable and Output:Meter objects...")
    
    # Request Total Facility Electricity (for the savings calculation)
    idf.newidfobject('Output:Meter', 
        Key_Name='Electricity:Facility', 
        Reporting_Frequency='Hourly'
    )
    
    # Request Zone Temperatures (for the comfort bounds graph)
    idf.newidfobject('Output:Variable', 
        Key_Value='Core_bottom', 
        Variable_Name='Zone Mean Air Temperature', 
        Reporting_Frequency='Hourly'
    )
    
    idf.newidfobject('Output:Variable', 
        Key_Value='Core_mid', 
        Variable_Name='Zone Mean Air Temperature', 
        Reporting_Frequency='Hourly'
    )
    
    # Save as a new file so we don't destroy the original
    new_idf_path = os.path.join(DATA_DIR, 'medium_office_tampa_2a_SHORT.idf')
    idf.saveas(new_idf_path)
    
    print(f"✅ Success! Created 3-day simulation file with CSV logging enabled at:\n{new_idf_path}")

if __name__ == "__main__":
    prepare_idf()   