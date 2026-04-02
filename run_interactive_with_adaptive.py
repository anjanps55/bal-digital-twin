#!/usr/bin/env python3
"""
BAL Digital Twin - Interactive Mode with Real-Time Adaptive Controller

Allows you to input ANY patient parameters, and the adaptive controller
automatically adjusts treatment in real-time to achieve successful clearance.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent))

from simulation.engine import SimulationEngine
from adaptive_realtime_controller import RealtimeAdaptiveController
import config.constants as constants


def print_header():
    """Print welcome header."""
    print("\n" + "="*70)
    print("  BIOARTIFICIAL LIVER DIGITAL TWIN")
    print("  🤖 INTERACTIVE MODE WITH REAL-TIME ADAPTIVE CONTROL 🤖")
    print("="*70)
    print("\n💡 Input ANY parameters - Controller auto-optimizes for success!\n")


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


def show_preset_menu() -> Optional[str]:
    """Show preset patient scenarios and return selection."""
    print("\n" + "-"*70)
    print("  PRESET PATIENT SCENARIOS")
    print("-"*70)
    print("  1. Normal Adult - Standard treatment")
    print("     NH₃: 90 µmol/L, Lidocaine: 21 µmol/L")
    print()
    print("  2. Elevated NH3 - Requires adaptive intervention")
    print("     NH₃: 120 µmol/L, Lidocaine: 25 µmol/L")
    print()
    print("  3. Severe Case - Multiple interventions needed")
    print("     NH₃: 180 µmol/L, Lidocaine: 35 µmol/L")
    print()
    print("  4. Critical Patient - Maximum adaptive support")
    print("     NH₃: 250 µmol/L, Lidocaine: 45 µmol/L")
    print()
    print("  5. Pediatric Patient - Child requiring scaled treatment")
    print("     NH₃: 110 µmol/L, Lidocaine: 25 µmol/L, Reduced flow")
    print()
    print("  6. Mild Case - Early liver failure")
    print("     NH₃: 60 µmol/L, Lidocaine: 15 µmol/L")
    print()
    print("  7. Custom - Enter your own parameters")
    print("-"*70)

    while True:
        choice = input("\nSelect scenario [1-7]: ").strip()
        if choice in ['1', '2', '3', '4', '5', '6', '7']:
            return choice
        print("  ⚠️  Please enter a number between 1 and 7")


def apply_preset(choice: str) -> Dict[str, Any]:
    """Apply preset parameters based on user choice."""

    presets = {
        '1': {  # Normal Adult
            'name': 'Normal Adult',
            'age': 45,
            'weight': 70,
            'Q_blood': 150,
            'Hct': 0.32,
            'NH3': 90,
            'lido': 21,
            'urea': 5.0,
            'duration': 120
        },
        '2': {  # Elevated NH3
            'name': 'Elevated NH3',
            'age': 50,
            'weight': 75,
            'Q_blood': 150,
            'Hct': 0.30,
            'NH3': 120,
            'lido': 25,
            'urea': 4.5,
            'duration': 120
        },
        '3': {  # Severe Case
            'name': 'Severe Case',
            'age': 55,
            'weight': 85,
            'Q_blood': 150,
            'Hct': 0.28,
            'NH3': 180,
            'lido': 35,
            'urea': 3.5,
            'duration': 120
        },
        '4': {  # Critical Patient
            'name': 'Critical Patient',
            'age': 60,
            'weight': 80,
            'Q_blood': 150,
            'Hct': 0.26,
            'NH3': 250,
            'lido': 45,
            'urea': 3.0,
            'duration': 120
        },
        '5': {  # Pediatric
            'name': 'Pediatric Patient',
            'age': 10,
            'weight': 35,
            'Q_blood': 75,
            'Hct': 0.35,
            'NH3': 110,
            'lido': 25,
            'urea': 4.0,
            'duration': 90
        },
        '6': {  # Mild Case
            'name': 'Mild Case',
            'age': 38,
            'weight': 65,
            'Q_blood': 150,
            'Hct': 0.34,
            'NH3': 60,
            'lido': 15,
            'urea': 6.0,
            'duration': 90
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

        if choice != '7':  # Not custom
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
    print("  TOXIN CONCENTRATIONS")
    print("-"*70)
    print("  Normal ranges: NH₃ <35 µmol/L, Lidocaine <10 µmol/L")
    print("  The adaptive controller will auto-adjust treatment for ANY level!")
    params['NH3'] = get_float_input("Ammonia (NH₃) concentration (µmol/L)", params.get('NH3', 90.0), 10, 500)
    params['lido'] = get_float_input("Lidocaine concentration (µmol/L)", params.get('lido', 21.0), 5, 100)
    params['urea'] = get_float_input("Urea concentration (mmol/L)", params.get('urea', 5.0), 0, 30)

    # Treatment duration (initial - will be extended by adaptive controller if needed)
    print("\n" + "-"*70)
    print("  TREATMENT PARAMETERS")
    print("-"*70)
    print("  Note: The adaptive controller may extend duration if needed")
    params['duration'] = get_int_input("Initial treatment duration (minutes)", params.get('duration', 120), 30, 360)

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

    # Assess severity
    if params['NH3'] < 50:
        severity = "✅ NORMAL/MILD"
        adaptive_note = "Standard treatment likely sufficient"
    elif params['NH3'] < 100:
        severity = "⚠️  ELEVATED"
        adaptive_note = "🤖 Adaptive controller will optimize treatment"
    elif params['NH3'] < 200:
        severity = "⚠️  SEVERE"
        adaptive_note = "🤖 Multiple interventions may be needed"
    else:
        severity = "🚨 CRITICAL"
        adaptive_note = "🤖 Maximum adaptive support required"

    print(f"  Ammonia (NH₃):      {params['NH3']} µmol/L    {severity}")
    print(f"  Lidocaine:          {params['lido']} µmol/L")
    print(f"  Urea:               {params['urea']} mmol/L")
    print()
    print(f"Treatment Settings:")
    print(f"  Initial Duration:   {params['duration']} minutes")
    print()
    print(f"🤖 Adaptive Control: {adaptive_note}")
    print("="*70)


def apply_parameters_to_engine(engine: SimulationEngine, params: Dict[str, Any]):
    """Apply user parameters to simulation engine."""

    # Update separator inputs
    engine.separator.Q_blood_in = params['Q_blood']
    engine.separator.Hct_in = params['Hct']
    engine.separator.C_NH3_in = params['NH3']
    engine.separator.C_lido_in = params['lido']
    engine.separator.C_urea_in = params['urea']

    print("\n✅ Parameters applied to simulation engine")


def run_adaptive_simulation(params: Dict[str, Any]):
    """Run the simulation with adaptive controller."""

    print("\n" + "="*70)
    print("  RUNNING ADAPTIVE TREATMENT")
    print("="*70)

    # Create simulation engine
    engine = SimulationEngine(dt=1.0)

    # Apply patient parameters
    apply_parameters_to_engine(engine, params)

    # Create adaptive controller
    controller = RealtimeAdaptiveController(engine)

    # Optional: Customize adaptive controller settings
    print("\n🤖 Adaptive Controller Configuration:")
    print(f"  NH3 target: {controller.NH3_target} µmol/L")
    print(f"  Monitoring interval: {controller.monitoring_interval} minutes")
    print(f"  Flow rate range: {controller.min_flow_rate}-{controller.max_flow_rate} mL/min")
    print(f"  Safety limits: Max {controller.max_treatment_duration:.0f} min, "
          f"{controller.max_interventions} interventions, "
          f"{controller.max_cartridge_replacements} cartridge swaps")

    # Ask if user wants to customize controller
    customize = get_yes_no_input("\nCustomize adaptive controller settings?", default=False)

    if customize:
        print("\n" + "-"*70)
        print("  CUSTOMIZE ADAPTIVE CONTROLLER")
        print("-"*70)
        controller.NH3_target = get_float_input("NH3 target (µmol/L)", controller.NH3_target, 30, 60)
        controller.monitoring_interval = get_float_input("Monitoring interval (minutes)",
                                                         controller.monitoring_interval, 5, 30)
        controller.max_treatment_duration = get_float_input("Maximum treatment duration (minutes)",
                                                            controller.max_treatment_duration, 180, 600)
        controller.max_interventions = get_int_input("Maximum interventions",
                                                     controller.max_interventions, 5, 50)
        controller.max_cartridge_replacements = get_int_input("Maximum cartridge replacements",
                                                              controller.max_cartridge_replacements, 1, 10)
        print("✅ Controller customized")

    # Run adaptive treatment
    summary = controller.run_adaptive_treatment(initial_duration=params['duration'])

    return summary


def show_detailed_results(summary: Dict[str, Any], initial_params: Dict[str, Any]):
    """Show detailed results with comparison to initial state."""

    print("\n" + "="*70)
    print("  DETAILED TREATMENT ANALYSIS")
    print("="*70)

    # Toxin Reduction
    print("\n📊 TOXIN CLEARANCE:")
    initial_nh3 = initial_params['NH3']
    final_nh3 = summary['final_metrics']['NH3_level']
    nh3_reduction = initial_nh3 - final_nh3
    nh3_reduction_pct = (nh3_reduction / initial_nh3 * 100) if initial_nh3 > 0 else 0

    print(f"  NH₃:  {initial_nh3:.1f} → {final_nh3:.1f} µmol/L")
    print(f"        Reduction: {nh3_reduction:.1f} µmol/L ({nh3_reduction_pct:.1f}%)")
    print(f"        Clearance: {summary['final_metrics']['NH3_clearance']:.1%}")

    # Safety Assessment
    print("\n🏥 SAFETY ASSESSMENT:")
    nh3_safe = final_nh3 <= 50
    nh3_optimal = final_nh3 <= 45

    if nh3_optimal:
        status = "✅ OPTIMAL - Safe to return to patient"
    elif nh3_safe:
        status = "✅ SAFE - Return with monitoring"
    else:
        status = "⚠️  ELEVATED - May need additional treatment"

    print(f"  Final NH₃ Status: {status}")
    print(f"  Cell Viability:   {summary['final_metrics']['cell_viability']:.1%}")
    print(f"  Treatment Success: {summary['final_metrics']['treatment_success']}")

    # Adaptive Interventions
    print("\n🤖 ADAPTIVE INTERVENTIONS:")
    intervention_count = summary['interventions']['total_count']
    cartridge_count = summary['interventions']['cartridge_replacements']

    if intervention_count == 0:
        print(f"  No interventions needed - standard treatment successful")
    else:
        print(f"  Total interventions:     {intervention_count}")
        print(f"  Cartridge replacements:  {cartridge_count}")
        print(f"  Duration extensions:     +{summary['treatment_duration']['extended']:.0f} minutes")

        if summary['interventions']['log']:
            print(f"\n  Intervention Timeline:")
            for i, intervention in enumerate(summary['interventions']['log'][:5], 1):  # Show first 5
                print(f"    {i}. t={intervention['time']:.0f}min [{intervention['level']}]: "
                      f"Flow={intervention['new_flow_rate']:.0f}mL/min")
            if len(summary['interventions']['log']) > 5:
                print(f"    ... and {len(summary['interventions']['log']) - 5} more")

    # Treatment Efficiency
    print("\n⏱️  TREATMENT EFFICIENCY:")
    print(f"  Planned duration:  {summary['treatment_duration']['planned']:.0f} minutes")
    print(f"  Extended by:       +{summary['treatment_duration']['extended']:.0f} minutes")
    print(f"  Total duration:    {summary['treatment_duration']['total']:.0f} minutes")

    # Overall Verdict
    print("\n" + "="*70)
    if summary['final_metrics']['treatment_success'] or final_nh3 <= 50:
        print("  🎉 TREATMENT SUCCESSFUL!")
        print("  Patient blood is safe to return to circulation")
    elif any(summary['safety_limits'].values()):
        print("  ⚠️  SAFETY LIMITS REACHED")
        print("  Patient may require:")
        print("    • Alternative therapy")
        print("    • Liver transplant evaluation")
        print("    • Extended ICU support")
    else:
        print("  ⚠️  TREATMENT INCOMPLETE")
        print("  Consider:")
        print("    • Extended treatment session")
        print("    • Alternative therapeutic approach")
    print("="*70)


def main():
    """Main interactive interface with adaptive control."""

    try:
        print_header()

        print("Welcome to the BAL Digital Twin with Real-Time Adaptive Control!")
        print()
        print("This advanced system:")
        print("  • Accepts ANY patient parameters")
        print("  • Automatically monitors NH₃ levels every 10 minutes")
        print("  • Adjusts flow rate, replaces cartridges, and extends duration")
        print("  • Optimizes treatment to achieve successful toxin clearance")
        print()

        # Get parameters from user
        params = get_patient_parameters()

        # Show summary
        show_parameter_summary(params)

        # Confirm before running
        confirm = get_yes_no_input("\nProceed with adaptive treatment?", default=True)

        if not confirm:
            print("\n❌ Simulation cancelled.")
            return

        # Run adaptive simulation
        summary = run_adaptive_simulation(params)

        # Show detailed results
        show_detailed_results(summary, params)

        # Export data
        print("\n📁 Data Export:")
        print(f"  Results saved to: output/demo_results.csv")
        print(f"  Results saved to: output/demo_results.json")

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
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
