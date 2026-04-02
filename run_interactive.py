#!/usr/bin/env python3
"""
BAL Digital Twin - Interactive Terminal Interface

Allows users to input custom patient parameters directly in the terminal.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from simulation.engine import SimulationEngine
import config.constants as constants


def print_header():
    """Print welcome header."""
    print("\n" + "="*70)
    print("  BIOARTIFICIAL LIVER DIGITAL TWIN - INTERACTIVE SIMULATION")
    print("="*70)
    print()


def get_float_input(prompt: str, default: float, min_val: float = None, max_val: float = None) -> float:
    """
    Get validated float input from user.
    
    Args:
        prompt: Input prompt text
        default: Default value if user presses Enter
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        User input or default value
    """
    while True:
        user_input = input(f"{prompt} [{default}]: ").strip()
        
        # Use default if empty
        if not user_input:
            return default
        
        # Try to convert to float
        try:
            value = float(user_input)
            
            # Validate range
            if min_val is not None and value < min_val:
                print(f"  ⚠️  Value must be >= {min_val}")
                continue
            if max_val is not None and value > max_val:
                print(f"  ⚠️  Value must be <= {max_val}")
                continue
            
            return value
            
        except ValueError:
            print(f"  ⚠️  Invalid input. Please enter a number.")


def get_int_input(prompt: str, default: int, min_val: int = None, max_val: int = None) -> int:
    """Get validated integer input from user."""
    return int(get_float_input(prompt, float(default), 
                               float(min_val) if min_val else None,
                               float(max_val) if max_val else None))


def get_yes_no_input(prompt: str, default: bool = True) -> bool:
    """Get yes/no input from user."""
    default_str = "Y/n" if default else "y/N"
    while True:
        user_input = input(f"{prompt} [{default_str}]: ").strip().lower()
        
        if not user_input:
            return default
        
        if user_input in ['y', 'yes']:
            return True
        elif user_input in ['n', 'no']:
            return False
        else:
            print("  ⚠️  Please enter 'y' or 'n'")


def show_preset_menu() -> Optional[str]:
    """Show preset patient scenarios and return selection."""
    print("\n" + "-"*70)
    print("  PRESET PATIENT SCENARIOS")
    print("-"*70)
    print("  1. Standard Adult (Default) - Moderate liver failure")
    print("     NH₃: 90 µmol/L, Lidocaine: 21 µmol/L")
    print()
    print("  2. Severe Case - Very high toxin levels")
    print("     NH₃: 200 µmol/L, Lidocaine: 35 µmol/L")
    print()
    print("  3. Pediatric Patient - Child requiring scaled treatment")
    print("     NH₃: 110 µmol/L, Lidocaine: 25 µmol/L, Reduced flow")
    print()
    print("  4. Mild Case - Early liver failure")
    print("     NH₃: 60 µmol/L, Lidocaine: 15 µmol/L")
    print()
    print("  5. Custom - Enter your own parameters")
    print("-"*70)
    
    while True:
        choice = input("\nSelect scenario [1-5]: ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return choice
        print("  ⚠️  Please enter a number between 1 and 5")


def apply_preset(choice: str) -> Dict[str, Any]:
    """Apply preset parameters based on user choice."""
    
    presets = {
        '1': {  # Standard Adult
            'name': 'Standard Adult',
            'age': 45,
            'weight': 70,
            'Q_blood': 150,
            'Hct': 0.32,
            'NH3': 90,
            'lido': 21,
            'urea': 5.0,
            'Q_target': 30,
            'duration': 60
        },
        '2': {  # Severe Case
            'name': 'Severe Case',
            'age': 55,
            'weight': 85,
            'Q_blood': 150,
            'Hct': 0.30,
            'NH3': 200,
            'lido': 35,
            'urea': 3.0,
            'Q_target': 40,
            'duration': 120
        },
        '3': {  # Pediatric
            'name': 'Pediatric Patient',
            'age': 10,
            'weight': 35,
            'Q_blood': 75,
            'Hct': 0.35,
            'NH3': 110,
            'lido': 25,
            'urea': 4.0,
            'Q_target': 20,
            'duration': 90
        },
        '4': {  # Mild Case
            'name': 'Mild Case',
            'age': 38,
            'weight': 65,
            'Q_blood': 150,
            'Hct': 0.34,
            'NH3': 60,
            'lido': 15,
            'urea': 6.0,
            'Q_target': 25,
            'duration': 45
        }
    }
    
    return presets.get(choice, presets['1'])


def get_patient_parameters() -> Dict[str, Any]:
    """
    Interactively collect patient parameters from user.
    
    Returns:
        Dictionary of patient parameters
    """
    print("\n" + "="*70)
    print("  PATIENT PARAMETERS")
    print("="*70)
    print("\nPress Enter to use default values shown in [brackets]")
    print()
    
    # Show preset menu
    use_preset = get_yes_no_input("Would you like to use a preset scenario?", default=True)
    
    if use_preset:
        choice = show_preset_menu()
        
        if choice != '5':  # Not custom
            params = apply_preset(choice)
            print(f"\n✅ Using preset: {params['name']}")
            
            # Ask if they want to modify any parameters
            modify = get_yes_no_input("\nWould you like to modify any parameters?", default=False)
            if not modify:
                return params
            
            print("\nEnter new values or press Enter to keep preset values:")
    else:
        params = apply_preset('1')  # Start with defaults
    
    # Patient demographics
    print("\n" + "-"*70)
    print("  PATIENT DEMOGRAPHICS")
    print("-"*70)
    params['age'] = get_int_input("Patient age (years)", params.get('age', 45), 0, 120)
    params['weight'] = get_float_input("Patient weight (kg)", params.get('weight', 70.0), 20, 200)
    
    # Blood parameters
    print("\n" + "-"*70)
    print("  BLOOD PARAMETERS")
    print("-"*70)
    params['Q_blood'] = get_float_input("Blood flow rate (mL/min)", params.get('Q_blood', 150.0), 50, 300)
    params['Hct'] = get_float_input("Hematocrit (fraction, e.g., 0.32)", params.get('Hct', 0.32), 0.15, 0.65)
    
    # Toxin concentrations
    print("\n" + "-"*70)
    print("  TOXIN CONCENTRATIONS (High values = need treatment)")
    print("-"*70)
    print("  Normal ranges: NH₃ <35 µmol/L, Lidocaine <10 µmol/L")
    params['NH3'] = get_float_input("Ammonia (NH₃) concentration (µmol/L)", params.get('NH3', 90.0), 0, 500)
    params['lido'] = get_float_input("Lidocaine concentration (µmol/L)", params.get('lido', 21.0), 0, 100)
    params['urea'] = get_float_input("Urea concentration (mmol/L)", params.get('urea', 5.0), 0, 30)
    
    # Treatment parameters
    print("\n" + "-"*70)
    print("  TREATMENT PARAMETERS")
    print("-"*70)
    params['Q_target'] = get_float_input("Target plasma flow through bioreactor (mL/min)", 
                                         params.get('Q_target', 30.0), 10, 100)
    params['duration'] = get_int_input("Treatment duration (minutes)", params.get('duration', 60), 10, 360)
    
    return params


def show_parameter_summary(params: Dict[str, Any]):
    """Display summary of entered parameters."""
    print("\n" + "="*70)
    print("  SIMULATION PARAMETERS SUMMARY")
    print("="*70)
    print(f"\nPatient Demographics:")
    print(f"  Age:                {params['age']} years")
    print(f"  Weight:             {params['weight']} kg")
    print()
    print(f"Blood Parameters:")
    print(f"  Flow Rate:          {params['Q_blood']} mL/min")
    print(f"  Hematocrit:         {params['Hct']:.2f} ({params['Hct']*100:.0f}%)")
    print()
    print(f"Toxin Concentrations:")
    
    # Show status for each toxin
    nh3_status = "⚠️  HIGH" if params['NH3'] > 50 else "✅ NORMAL"
    lido_status = "⚠️  HIGH" if params['lido'] > 10 else "✅ NORMAL"
    
    print(f"  Ammonia (NH₃):      {params['NH3']} µmol/L    {nh3_status}")
    print(f"  Lidocaine:          {params['lido']} µmol/L    {lido_status}")
    print(f"  Urea:               {params['urea']} mmol/L")
    print()
    print(f"Treatment Settings:")
    print(f"  Target Flow:        {params['Q_target']} mL/min")
    print(f"  Duration:           {params['duration']} minutes")
    print("="*70)


def apply_parameters_to_constants(params: Dict[str, Any]):
    """Apply user parameters to system constants."""
    
    # Update separator inputs
    constants.SEPARATOR_INPUTS['Q_blood_nominal'] = params['Q_blood']
    constants.SEPARATOR_INPUTS['Hct_in_nominal'] = params['Hct']
    constants.SEPARATOR_INPUTS['C_NH3_in_nominal'] = params['NH3']
    constants.SEPARATOR_INPUTS['C_lido_in_nominal'] = params['lido']
    constants.SEPARATOR_INPUTS['C_urea_in_nominal'] = params['urea']
    
    # Update pump target
    constants.PUMP_THRESHOLDS['Q_target'] = params['Q_target']
    
    print("\n✅ Parameters applied to simulation")


def run_simulation(params: Dict[str, Any]):
    """Run the simulation with user parameters."""
    
    print("\n" + "="*70)
    print("  RUNNING SIMULATION")
    print("="*70)
    print(f"\nSimulating {params['duration']}-minute treatment...")
    print("Please wait...\n")
    
    # Create and run simulation
    sim = SimulationEngine(dt=1.0)
    sim.run(duration=params['duration'])
    
    # Show results
    print("\n" + "="*70)
    print("  SIMULATION COMPLETE")
    print("="*70)
    
    # Get final data
    if sim.history:
        final = sim.history[-1]
        
        # Extract key results
        final_nh3 = final['bioreactor']['C_NH3']
        final_lido = final['bioreactor']['C_lido']
        nh3_clearance = final['bioreactor']['NH3_clearance'] * 100
        lido_clearance = final['bioreactor']['lido_clearance'] * 100
        cell_viability = final['bioreactor']['cell_viability'] * 100
        
        print(f"\nTREATMENT RESULTS:")
        print(f"  Ammonia:     {params['NH3']:.1f} → {final_nh3:.1f} µmol/L ({nh3_clearance:.1f}% clearance)")
        print(f"  Lidocaine:   {params['lido']:.1f} → {final_lido:.1f} µmol/L ({lido_clearance:.1f}% clearance)")
        print(f"  Cell Viability: {cell_viability:.1f}%")
        print()
        
        # Evaluate treatment success
        nh3_safe = final_nh3 < 50
        lido_safe = final_lido < 10
        
        print(f"TREATMENT EVALUATION:")
        print(f"  Ammonia Status:   {'✅ SAFE' if nh3_safe else '⚠️  STILL HIGH'}")
        print(f"  Lidocaine Status: {'✅ SAFE' if lido_safe else '⚠️  STILL HIGH'}")
        
        if nh3_safe and lido_safe:
            print(f"\n  🎉 TREATMENT SUCCESSFUL - Blood is safe to return to patient!")
        else:
            print(f"\n  ⚠️  Treatment incomplete - May need longer duration or adjusted parameters")
    
    # Show module states
    print(f"\nFINAL MODULE STATES:")
    for module_name, state in sim.get_module_states().items():
        print(f"  {module_name}: {state}")
    
    # Export data
    print(f"\nExporting data...")
    sim.data_logger.export_csv("interactive_results.csv")
    sim.data_logger.export_json("interactive_results.json")
    print(f"  ✅ Results saved to output/interactive_results.*")


def main():
    """Main interactive interface."""
    
    try:
        print_header()
        
        print("Welcome to the BAL Digital Twin Interactive Simulator!")
        print("This tool allows you to simulate blood treatment for custom patient parameters.")
        print()
        
        # Get parameters from user
        params = get_patient_parameters()
        
        # Show summary
        show_parameter_summary(params)
        
        # Confirm before running
        confirm = get_yes_no_input("\nProceed with simulation?", default=True)
        
        if not confirm:
            print("\n❌ Simulation cancelled.")
            return
        
        # Apply parameters and run
        apply_parameters_to_constants(params)
        run_simulation(params)
        
        # Ask to run another
        print("\n" + "="*70)
        another = get_yes_no_input("\nWould you like to run another simulation?", default=False)
        
        if another:
            main()  # Recursive call for another simulation
        else:
            print("\n✅ Thank you for using the BAL Digital Twin!")
            print("="*70 + "\n")
    
    except KeyboardInterrupt:
        print("\n\n❌ Simulation cancelled by user.")
        print("="*70 + "\n")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("="*70 + "\n")
        raise


if __name__ == "__main__":
    main()
