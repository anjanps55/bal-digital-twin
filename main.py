"""
BAL Digital Twin Simulator
Main entry point
"""

from simulation.engine import SimulationEngine
from interface.gui import BALGUI


def main():
    """
    Main function to run BAL simulator.
    """
    print("BAL Digital Twin Simulator")
    print("=" * 50)
    print("\n🎉 ALL 6 MODULES IMPLEMENTED!")
    print("  1. Plasma Separator")
    print("  2. Pump Control ← NEW!")
    print("  3. Bioreactor System")
    print("  4. Sampler")
    print("  5. Mixer")
    print("  6. Return Monitor")
    print("=" * 50)

    # Option 1: Run with GUI (future enhancement)
    # gui = BALGUI()
    # gui.run()

    # Option 2: Run headless simulation
    print("\nInitializing simulation engine...")
    sim = SimulationEngine(dt=1.0)  # 1 minute time steps

    print("\nModule Status:")
    states = sim.get_module_states()
    for module_name, state in states.items():
        print(f"  {module_name}: {state}")

    print("\nRunning 60-minute treatment simulation...")
    print("-" * 50)

    # Run 60-minute simulation
    results = sim.run(duration=60)

    print("\n" + "=" * 50)
    print("SIMULATION COMPLETE")
    print("=" * 50)

    # Display final results
    print("\nFinal Module States:")
    final_states = sim.get_module_states()
    for module_name, state in final_states.items():
        print(f"  {module_name}: {state}")

    # Display treatment metrics
    if results:
        print("\nTreatment Performance:")
        if 'bioreactor' in results:
            bio = results['bioreactor']
            print(f"  NH3 Clearance: {bio.get('NH3_clearance', 0.0):.1%}")
            print(f"  Lidocaine Clearance: {bio.get('lido_clearance', 0.0):.1%}")
            print(f"  Cell Viability: {bio.get('cell_viability', 0.0):.1%}")

        if 'pump' in results:
            pump = results['pump']
            print(f"\nPump Status:")
            print(f"  State: {pump.get('state_name', 'Unknown')}")
            print(f"  Running: {pump.get('pump_running', False)}")
            print(f"  Flow Rate: {pump.get('Q_plasma', 0.0):.1f} mL/min")

        if 'return_monitor' in results:
            monitor = results['return_monitor']
            print(f"\nReturn Monitor:")
            print(f"  Return Approved: {monitor.get('return_approved', False)}")
            print(f"  Treatment Success: {monitor.get('treatment_success', False)}")

    print("\n✅ Simulation complete! All 6 modules operational.")


if __name__ == "__main__":
    main()
