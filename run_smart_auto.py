#!/usr/bin/env python3
"""
BAL Digital Twin - SMART AUTO MODE

Just input patient parameters - the system automatically figures out
EVERYTHING needed for successful treatment!

No guessing, no trial-and-error - pure intelligence! 🧠
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from intelligent_treatment_planner import IntelligentTreatmentPlanner
from typing import Dict, Any


def print_header():
    """Print welcome header."""
    print("\n" + "="*70)
    print("  BAL DIGITAL TWIN - SMART AUTO MODE 🧠")
    print("="*70)
    print("\n  Just tell me about your patient...")
    print("  I'll figure out the optimal treatment automatically!")
    print("="*70)


def get_float_input(prompt: str, default: float, min_val: float = None, max_val: float = None) -> float:
    """Get validated float input from user."""
    while True:
        user_input = input(f"{prompt} [{default}]: ").strip()

        if not user_input:
            return default

        try:
            value = float(user_input)

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


def show_preset_menu():
    """Show preset patient scenarios."""
    print("\n" + "-"*70)
    print("  QUICK SCENARIOS")
    print("-"*70)
    print("  1. Normal (NH₃: 90 µmol/L)")
    print("  2. Mild (NH₃: 110 µmol/L)")
    print("  3. Moderate (NH₃: 150 µmol/L)")
    print("  4. Severe (NH₃: 200 µmol/L)")
    print("  5. Critical (NH₃: 280 µmol/L)")
    print("  6. Custom - Enter your own")
    print("-"*70)

    while True:
        choice = input("\nSelect [1-6]: ").strip()
        if choice in ['1', '2', '3', '4', '5', '6']:
            return choice
        print("  ⚠️  Enter 1-6")


def get_preset_values(choice: str) -> tuple:
    """Get NH3 and lidocaine values for preset."""
    presets = {
        '1': (90, 21),    # Normal
        '2': (110, 25),   # Mild
        '3': (150, 30),   # Moderate
        '4': (200, 35),   # Severe
        '5': (280, 45),   # Critical
    }
    return presets.get(choice, (90, 21))


def get_patient_input() -> Dict[str, Any]:
    """Get patient parameters - ONLY what matters, system calculates the rest!"""

    print("\n" + "="*70)
    print("  PATIENT INPUT")
    print("="*70)
    print("\n💡 You only need to tell me about the patient's condition")
    print("   I'll calculate everything else automatically!\n")

    # Use preset or custom
    use_preset = get_yes_no_input("Use a quick scenario?", default=True)

    if use_preset:
        choice = show_preset_menu()
        if choice == '6':  # Custom
            nh3 = get_float_input("\nAmmonia (NH₃) concentration (µmol/L)", 90.0, 10, 500)
            lido = get_float_input("Lidocaine concentration (µmol/L)", 21.0, 5, 100)
        else:
            nh3, lido = get_preset_values(choice)
            print(f"\n✅ Selected: NH₃ = {nh3} µmol/L, Lidocaine = {lido} µmol/L")
    else:
        print("\nEnter patient toxin levels:")
        nh3 = get_float_input("  Ammonia (NH₃) concentration (µmol/L)", 90.0, 10, 500)
        lido = get_float_input("  Lidocaine concentration (µmol/L)", 21.0, 5, 100)

    # Optional: Additional patient parameters (for completeness)
    print("\n" + "-"*70)
    print("Optional: Additional patient details (or press Enter to use defaults)")
    print("-"*70)

    customize = get_yes_no_input("Enter additional patient details?", default=False)

    patient_params = {}
    if customize:
        patient_params['age'] = get_int_input("  Age (years)", 45, 0, 120)
        patient_params['weight'] = get_float_input("  Weight (kg)", 70.0, 20, 200)
        patient_params['Q_blood'] = get_float_input("  Blood flow rate (mL/min)", 150.0, 50, 300)
        patient_params['Hct'] = get_float_input("  Hematocrit", 0.32, 0.15, 0.65)

    return {
        'NH3': nh3,
        'lido': lido,
        'additional_params': patient_params
    }


def show_patient_summary(params: Dict[str, Any]):
    """Show patient summary."""
    print("\n" + "="*70)
    print("  PATIENT SUMMARY")
    print("="*70)

    print(f"\n🔬 TOXIN LEVELS:")
    print(f"  Ammonia (NH₃):  {params['NH3']:.1f} µmol/L", end="")

    # Show status
    if params['NH3'] < 50:
        print("  ✅ Normal")
    elif params['NH3'] < 90:
        print("  ⚠️  Mildly elevated")
    elif params['NH3'] < 150:
        print("  ⚠️  Moderately elevated")
    elif params['NH3'] < 250:
        print("  🚨 Severely elevated")
    else:
        print("  🚨 Critically high")

    print(f"  Lidocaine:      {params['lido']:.1f} µmol/L")

    if params['additional_params']:
        print(f"\n👤 PATIENT DETAILS:")
        if 'age' in params['additional_params']:
            print(f"  Age:            {params['additional_params']['age']} years")
        if 'weight' in params['additional_params']:
            print(f"  Weight:         {params['additional_params']['weight']} kg")
        if 'Q_blood' in params['additional_params']:
            print(f"  Blood flow:     {params['additional_params']['Q_blood']} mL/min")
        if 'Hct' in params['additional_params']:
            print(f"  Hematocrit:     {params['additional_params']['Hct']:.2f}")

    print("="*70)


def show_final_results(summary: Dict[str, Any], initial_nh3: float):
    """Show comprehensive final results."""
    print("\n" + "="*70)
    print("  🎯 FINAL RESULTS")
    print("="*70)

    final_nh3 = summary['final_metrics']['NH3_level']
    clearance = summary['final_metrics']['NH3_clearance']
    viability = summary['final_metrics']['cell_viability']

    print(f"\n📊 TREATMENT OUTCOME:")
    print(f"  Initial NH₃:     {initial_nh3:.1f} µmol/L")
    print(f"  Final NH₃:       {final_nh3:.1f} µmol/L")
    print(f"  Reduction:       {initial_nh3 - final_nh3:.1f} µmol/L ({clearance:.1%})")
    print(f"  Cell Viability:  {viability:.1%}")

    # Success assessment
    print(f"\n🏥 ASSESSMENT:")
    if final_nh3 <= 45:
        print(f"  ✅ EXCELLENT - Optimal clearance achieved")
        print(f"     Blood is safe to return to patient")
    elif final_nh3 <= 50:
        print(f"  ✅ GOOD - Target achieved")
        print(f"     Blood is safe to return to patient")
    elif final_nh3 <= 60:
        print(f"  ⚠️  ACCEPTABLE - Slight elevation remains")
        print(f"     Return with continued monitoring")
    else:
        print(f"  ⚠️  INCOMPLETE - NH₃ still elevated")
        print(f"     Consider: extended treatment or alternative therapy")

    # Interventions summary
    interventions = summary['interventions']['total_count']
    if interventions > 0:
        print(f"\n🤖 ADAPTIVE ADJUSTMENTS:")
        print(f"  {interventions} real-time intervention(s) during treatment")
        print(f"  System auto-corrected to maintain optimal performance")

    # Planning accuracy
    if 'treatment_plan' in summary:
        accuracy = summary['treatment_plan']['planning_accuracy']
        print(f"\n🧠 PLANNING ACCURACY:")
        print(f"  Predicted NH₃:   {accuracy['estimated_NH3']:.1f} µmol/L")
        print(f"  Actual NH₃:      {accuracy['actual_NH3']:.1f} µmol/L")
        print(f"  Error:           {accuracy['error']:.1f} µmol/L ({accuracy['error_percent']:.1f}%)")
        print(f"  Rating:          {accuracy['accuracy_rating']}")

    # Duration info
    print(f"\n⏱️  TREATMENT DURATION:")
    print(f"  Calculated:      {summary['treatment_duration']['planned']:.0f} minutes")
    if summary['treatment_duration']['extended'] > 0:
        print(f"  Extended by:     +{summary['treatment_duration']['extended']:.0f} minutes")
    print(f"  Total:           {summary['treatment_duration']['total']:.0f} minutes ({summary['treatment_duration']['total']/60:.1f} hours)")

    print("="*70)


def main():
    """Main smart auto mode interface."""

    try:
        print_header()

        print("\nWelcome! This is the SMARTEST way to use the BAL simulator.")
        print()
        print("How it works:")
        print("  1. You tell me the patient's NH₃ and lidocaine levels")
        print("  2. I analyze and calculate OPTIMAL treatment parameters")
        print("  3. I run the treatment with those perfect settings")
        print("  4. You get successful clearance - automatically! 🎉")
        print()

        # Get patient input (ONLY toxin levels needed!)
        params = get_patient_input()

        # Show summary
        show_patient_summary(params)

        # Confirm
        confirm = get_yes_no_input("\nCalculate optimal treatment and execute?", default=True)

        if not confirm:
            print("\n❌ Cancelled.")
            return

        # Create intelligent planner
        planner = IntelligentTreatmentPlanner()

        # Plan and execute - THE MAGIC HAPPENS HERE! 🧠
        summary = planner.plan_and_execute(
            NH3_initial=params['NH3'],
            lido_initial=params['lido'],
            patient_params=params['additional_params']
        )

        # Show comprehensive results
        show_final_results(summary, params['NH3'])

        # Comparison
        print("\n" + "="*70)
        print("  💡 WHAT THE SYSTEM CALCULATED FOR YOU:")
        print("="*70)
        optimal = summary['treatment_plan']['optimal_parameters']
        print(f"\n  Instead of guessing, the system determined:")
        print(f"    ✅ Optimal flow rate:     {optimal['initial_flow_rate']:.0f} mL/min")
        print(f"    ✅ Optimal duration:      {optimal['initial_duration']:.0f} minutes")
        print(f"    ✅ Fresh cartridge:       {'Yes' if optimal['use_fresh_cartridge'] else 'No'}")
        print(f"\n  Based on:")
        analysis = summary['treatment_plan']['analysis']
        print(f"    • Severity assessment:    {analysis['severity']}")
        print(f"    • Clearance model:        Exponential decay kinetics")
        print(f"    • Safety margins:         20% time buffer included")
        print("="*70)

        # Ask to run another
        print()
        another = get_yes_no_input("Run another patient?", default=False)

        if another:
            # Reset constants if needed
            from config.constants import HEPATOCYTE_KINETICS
            HEPATOCYTE_KINETICS['k1_NH3_base'] = 1.0
            HEPATOCYTE_KINETICS['k1_lido_base'] = 0.85
            main()
        else:
            print("\n✅ Thank you for using Smart Auto Mode!")
            print("="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
        print("="*70 + "\n")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
