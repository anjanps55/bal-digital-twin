#!/usr/bin/env python3
"""
BAL Digital Twin - Interactive Mode with FIXED Adaptive Controller

This version copies the WORKING code from adaptive_controller.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from simulation.engine import SimulationEngine
import config.constants as const
import pandas as pd


def print_header():
    print("\n" + "="*70)
    print("  BIOARTIFICIAL LIVER DIGITAL TWIN")
    print("  🤖 ADAPTIVE CONTROLLER - WORKING VERSION")
    print("="*70)
    print("\n💡 Auto-optimizes treatment for any severity!\n")


def get_yes_no_input(prompt: str, default: bool = True) -> bool:
    default_str = "Y/n" if default else "y/N"
    while True:
        user_input = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not user_input:
            return default
        if user_input in ['y', 'yes']:
            return True
        if user_input in ['n', 'no']:
            return False
        print("  Please enter 'y' or 'n'")


def show_preset_menu():
    print("\n" + "-"*70)
    print("  PRESET SCENARIOS")
    print("-"*70)
    print()
    print("  1. Standard Adult (90 µmol/L NH3)")
    print("  2. Severe Case (200 µmol/L NH3) 🤖")
    print("  3. Pediatric (110 µmol/L NH3)")
    print("  4. Mild Case (60 µmol/L NH3)")
    print("-"*70)
    
    while True:
        choice = input("\nSelect [1-4]: ").strip()
        if choice in ['1', '2', '3', '4']:
            return choice
        print("  ⚠️  Enter 1-4")


def get_params(choice):
    """Get parameters for chosen scenario"""
    params = {
        '1': ('Standard Adult', 90, 21),
        '2': ('Severe Case', 200, 35),
        '3': ('Pediatric', 110, 25),
        '4': ('Mild Case', 60, 15)
    }
    name, nh3, lido = params[choice]
    return name, nh3, lido


def assess_severity(nh3, lido):
    """Determine severity"""
    if nh3 < 35:
        return 'normal'
    elif nh3 < 80:
        return 'mild'
    elif nh3 < 150:
        return 'severe'
    else:
        return 'critical'


def calculate_adjustments(severity, nh3):
    """Calculate treatment parameters based on severity"""
    
    adjustments = {
        'Q_plasma': 30,
        'duration': 60,
        'fresh_cartridge': False,
        'k1_multiplier': 1.0,
        'temperature_boost': 0.0
    }
    
    if severity == 'mild':
        adjustments['Q_plasma'] = 35
        adjustments['duration'] = 90
        
    elif severity == 'severe':
        adjustments['Q_plasma'] = 40
        adjustments['duration'] = 120
        adjustments['fresh_cartridge'] = True
        adjustments['k1_multiplier'] = 1.5
        
    elif severity == 'critical':
        adjustments['Q_plasma'] = 50
        adjustments['duration'] = 180
        adjustments['fresh_cartridge'] = True
        adjustments['k1_multiplier'] = 2.0
        adjustments['temperature_boost'] = 0.5
        
        # Extra for very high NH3
        if nh3 > 200:
            adjustments['duration'] = 240
            adjustments['k1_multiplier'] = 3.0
    
    return adjustments


def apply_adjustments(adjustments):
    """Apply adjustments to constants - EXACT copy from adaptive_controller.py"""
    
    const.PUMP_THRESHOLDS['Q_target'] = adjustments['Q_plasma']
    
    if adjustments['fresh_cartridge']:
        const.HEPATOCYTE_KINETICS['k1_NH3_base'] = 1.0 * adjustments['k1_multiplier']
        const.HEPATOCYTE_KINETICS['k1_lido_base'] = 0.85 * adjustments['k1_multiplier']
    
    if adjustments['temperature_boost'] > 0:
        temp_factor = 1.0 + (adjustments['temperature_boost'] * 0.01)
        const.HEPATOCYTE_KINETICS['k1_NH3_base'] *= temp_factor
        const.HEPATOCYTE_KINETICS['k1_lido_base'] *= temp_factor


def show_adjustments(severity, adj):
    print("\n" + "="*70)
    print("  🤖 ADAPTIVE CONTROLLER")
    print("="*70)
    print(f"\nSeverity: {severity.upper()}")
    print(f"\nAdjustments:")
    print(f"  Flow: {adj['Q_plasma']} mL/min")
    print(f"  Duration: {adj['duration']} min")
    if adj['fresh_cartridge']:
        print(f"  Fresh cartridge ({adj['k1_multiplier']:.1f}× capacity)")
    if adj['temperature_boost'] > 0:
        print(f"  Temperature optimized")
    print("\n" + "="*70)


def run_treatment(nh3_initial, lido_initial, duration):
    """Run treatment - EXACT copy from adaptive_controller.py"""
    
    # Set initial conditions
    const.SEPARATOR_INPUTS['C_NH3_in_nominal'] = nh3_initial
    const.SEPARATOR_INPUTS['C_lido_in_nominal'] = lido_initial
    
    print(f"\n🔬 Running {duration}-minute treatment...\n")
    
    sim = SimulationEngine(dt=1.0)
    sim.run(duration=duration)
    
    # Get results
    df = pd.read_csv('output/demo_results.csv')
    
    final_nh3 = df['bio_C_NH3'].iloc[-1]
    final_lido = df['bio_C_lido'].iloc[-1]
    
    clearance_nh3 = (nh3_initial - final_nh3) / nh3_initial * 100 if nh3_initial > 0 else 0
    clearance_lido = (lido_initial - final_lido) / lido_initial * 100 if lido_initial > 0 else 0
    
    print("="*70)
    print("  RESULTS")
    print("="*70)
    print(f"\nNH3:  {nh3_initial} → {final_nh3:.1f} µmol/L ({clearance_nh3:.1f}% clearance)")
    print(f"Lido: {lido_initial} → {final_lido:.1f} µmol/L ({clearance_lido:.1f}% clearance)")
    
    nh3_safe = final_nh3 < 50
    lido_safe = final_lido < 15
    
    print(f"\nStatus:")
    print(f"  NH3:  {'✅ SAFE' if nh3_safe else '⚠️  HIGH'} (target <50)")
    print(f"  Lido: {'✅ SAFE' if lido_safe else '⚠️  HIGH'} (target <15)")
    
    if nh3_safe and lido_safe:
        print(f"\n🎉 TREATMENT SUCCESSFUL!")
    else:
        print(f"\n⚠️  May need extended treatment")
    
    print()


def main():
    try:
        print_header()
        
        use_preset = get_yes_no_input("Use preset scenario?", True)
        
        if use_preset:
            choice = show_preset_menu()
            name, nh3, lido = get_params(choice)
            print(f"\n✅ Selected: {name}")
        else:
            name, nh3, lido = get_params('1')
        
        severity = assess_severity(nh3, lido)
        adj = calculate_adjustments(severity, nh3)
        
        show_adjustments(severity, adj)
        
        confirm = get_yes_no_input("\nProceed?", True)
        if not confirm:
            print("\n❌ Cancelled\n")
            return
        
        apply_adjustments(adj)
        run_treatment(nh3, lido, adj['duration'])
        
        another = get_yes_no_input("Run another?", False)
        if another:
            # Reset constants
            const.HEPATOCYTE_KINETICS['k1_NH3_base'] = 1.0
            const.HEPATOCYTE_KINETICS['k1_lido_base'] = 0.85
            main()
        else:
            print("="*70 + "\n")
            
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled\n")


if __name__ == "__main__":
    main()
