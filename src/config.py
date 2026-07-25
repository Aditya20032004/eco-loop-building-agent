import os
import sys

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output','ai')

IDF_PATH = os.path.join(DATA_DIR, 'medium_office_tampa_2a_SHORT.idf')
EPW_PATH = os.path.join(DATA_DIR, 'USA_FL_Tampa-MacDill.AFB.747880_TMY3.epw')

# EnergyPlus Install Path (Arch Linux)
EPLUS_DIR = '/usr/local/EnergyPlus-22-1-0/'
if EPLUS_DIR not in sys.path:
    sys.path.insert(0, EPLUS_DIR)