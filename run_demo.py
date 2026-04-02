"""
BAL Digital Twin - Simulation Demo

Demonstrates the simulation engine running Module 1 (Separator).
"""

from simulation.engine import SimulationEngine
import matplotlib.pyplot as plt
import pandas as pd


def main():
    """Run the BAL Digital Twin simulation demo."""
    print("BAL Digital Twin - Simulation Demo")
    print("=" * 60)

    # Create simulation
    sim = SimulationEngine(dt=1.0)

    # Run 60-minute simulation
    print("\nRunning 60-minute simulation...")
    sim.run(duration=60)

    # Print summary
    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)

    print(f"\nFinal Module States:")
    for module_name, state in sim.get_module_states().items():
        print(f"  {module_name}: {state}")

    # Export data
    print("\nExporting data...")
    sim.data_logger.export_csv("demo_results.csv")
    sim.data_logger.export_json("demo_results.json")

    # Plot key metrics
    plot_results(sim.history)

    print("\n✅ Demo complete! Check the 'output' folder for results.")


def plot_results(history):
    """
    Create plots of simulation results.

    Args:
        history: List of simulation output dicts
    """
    # Extract data from nested structure
    time = [entry['time'] for entry in history]

    # Separator data
    sep_Q_plasma = [entry['separator']['Q_plasma'] for entry in history]
    sep_Q_cells = [entry['separator']['Q_cells'] for entry in history]
    sep_TMP = [entry['separator']['TMP'] for entry in history]
    sep_eta = [entry['separator']['eta_sep'] for entry in history]
    sep_state = [entry['separator']['state'] for entry in history]

    # Mixer data
    mixer_Q_blood = [entry['mixer']['Q_blood'] for entry in history]
    mixer_Hct = [entry['mixer']['Hct_out'] for entry in history]
    mixer_efficiency = [entry['mixer']['mixing_efficiency'] for entry in history]
    mixer_state = [entry['mixer']['state'] for entry in history]

    # Create figure with subplots (3 rows, 2 columns for both modules)
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    fig.suptitle('BAL Digital Twin - Separator & Mixer Results', fontsize=14, fontweight='bold')

    # Row 1: Separator Plots
    # Plot 1: Flow rates (Separator)
    axes[0, 0].plot(time, sep_Q_plasma, label='Q_plasma', linewidth=2)
    axes[0, 0].plot(time, sep_Q_cells, label='Q_cells', linewidth=2)
    axes[0, 0].set_xlabel('Time (min)')
    axes[0, 0].set_ylabel('Flow Rate (mL/min)')
    axes[0, 0].set_title('Separator Flow Rates')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Plot 2: TMP (Separator)
    axes[0, 1].plot(time, sep_TMP, color='red', linewidth=2)
    axes[0, 1].axhline(y=50, color='orange', linestyle='--', label='Warning', alpha=0.7)
    axes[0, 1].axhline(y=60, color='red', linestyle='--', label='Critical', alpha=0.7)
    axes[0, 1].set_xlabel('Time (min)')
    axes[0, 1].set_ylabel('TMP (mmHg)')
    axes[0, 1].set_title('Transmembrane Pressure')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Row 2: More Separator and Mixer Plots
    # Plot 3: Separation efficiency
    axes[1, 0].plot(time, sep_eta, linewidth=2, color='green')
    axes[1, 0].axhline(y=0.95, color='green', linestyle='--', label='Normal', alpha=0.7)
    axes[1, 0].axhline(y=0.85, color='orange', linestyle='--', label='Degraded', alpha=0.7)
    axes[1, 0].set_xlabel('Time (min)')
    axes[1, 0].set_ylabel('Efficiency')
    axes[1, 0].set_title('Separation Efficiency')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim([0, 1.05])

    # Plot 4: Mixer output flow and hematocrit
    ax4a = axes[1, 1]
    ax4a.plot(time, mixer_Q_blood, label='Q_blood', linewidth=2, color='blue')
    ax4a.set_xlabel('Time (min)')
    ax4a.set_ylabel('Flow Rate (mL/min)', color='blue')
    ax4a.set_title('Mixer Output Flow & Hematocrit')
    ax4a.tick_params(axis='y', labelcolor='blue')
    ax4a.grid(True, alpha=0.3)

    # Secondary y-axis for hematocrit
    ax4b = ax4a.twinx()
    ax4b.plot(time, mixer_Hct, label='Hct_out', linewidth=2, color='red')
    ax4b.set_ylabel('Hematocrit', color='red')
    ax4b.tick_params(axis='y', labelcolor='red')
    ax4b.axhline(y=0.32, color='gray', linestyle='--', alpha=0.5, label='Target')

    # Add legends
    ax4a.legend(loc='upper left')
    ax4b.legend(loc='upper right')

    # Row 3: State plots
    # Plot 5: Separator state
    axes[2, 0].plot(time, sep_state, linewidth=2, color='blue', marker='o', markersize=3)
    axes[2, 0].set_xlabel('Time (min)')
    axes[2, 0].set_ylabel('State Code')
    axes[2, 0].set_title('Separator State')
    axes[2, 0].set_yticks([0, 1, 2, 3, 4, 5])
    axes[2, 0].set_yticklabels(['STARTUP', 'NORMAL', 'DEGRADED', 'FOULED', 'CLOTTED', 'FAILURE'],
                                fontsize=8)
    axes[2, 0].grid(True, alpha=0.3)
    axes[2, 0].set_ylim([-0.5, 5.5])

    # Plot 6: Mixer state and efficiency
    ax6a = axes[2, 1]
    ax6a.plot(time, mixer_state, linewidth=2, color='purple', marker='o', markersize=3)
    ax6a.set_xlabel('Time (min)')
    ax6a.set_ylabel('State Code', color='purple')
    ax6a.set_title('Mixer State & Efficiency')
    ax6a.tick_params(axis='y', labelcolor='purple')
    ax6a.set_yticks([0, 1, 2, 3])
    ax6a.set_yticklabels(['IDLE', 'STARTUP', 'NORMAL', 'IMBAL'], fontsize=8)
    ax6a.grid(True, alpha=0.3)

    # Secondary y-axis for mixing efficiency
    ax6b = ax6a.twinx()
    ax6b.plot(time, mixer_efficiency, label='Efficiency', linewidth=2, color='orange')
    ax6b.set_ylabel('Mixing Efficiency', color='orange')
    ax6b.tick_params(axis='y', labelcolor='orange')
    ax6b.set_ylim([0, 1.05])

    plt.tight_layout()
    plt.savefig('output/demo_plots.png', dpi=150, bbox_inches='tight')
    print("  Saved plots to: output/demo_plots.png")
    plt.close()


if __name__ == "__main__":
    main()
