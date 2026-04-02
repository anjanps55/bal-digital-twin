"""
Adaptive Real-Time Controller for BAL System

Implements intelligent, real-time control that monitors toxin levels and automatically
adjusts treatment parameters to optimize patient outcomes.

Key Features:
- Real-time NH3 monitoring every 10 minutes
- Adaptive flow rate control (20-60 mL/min)
- Automatic hepatocyte cartridge replacement
- Dynamic treatment duration extension
- Multi-tier intervention strategy
"""

from typing import Dict, Any, List
from simulation.engine import SimulationEngine
from config.constants import BIOREACTOR_THRESHOLDS


class RealtimeAdaptiveController:
    """
    Real-time adaptive controller for BAL system.

    Monitors toxin levels during treatment and automatically adjusts:
    - Flow rate (20-60 mL/min)
    - Hepatocyte cartridge replacement
    - Treatment duration

    Intervention Levels (NH3 target: 45 µmol/L):
    - CRITICAL (>135 µmol/L): Max flow + fresh cartridge + extend 60 min
    - HIGH (>90 µmol/L): +10 mL/min + fresh cartridge + extend 30 min
    - MEDIUM (>67.5 µmol/L): +5 mL/min + extend 15 min
    """

    def __init__(self, simulation_engine: SimulationEngine):
        """
        Initialize adaptive controller.

        Args:
            simulation_engine: The BAL simulation engine to control
        """
        self.engine = simulation_engine

        # Control parameters
        self.NH3_target = 45.0  # µmol/L - target ammonia level
        self.monitoring_interval = 10.0  # minutes - check every 10 min
        self.min_flow_rate = 20.0  # mL/min
        self.max_flow_rate = 60.0  # mL/min

        # Intervention thresholds (multiples of target)
        self.CRITICAL_THRESHOLD = 3.0  # >135 µmol/L
        self.HIGH_THRESHOLD = 2.0      # >90 µmol/L
        self.MEDIUM_THRESHOLD = 1.5    # >67.5 µmol/L

        # Safety limits to prevent infinite loops
        self.max_treatment_duration = 360.0  # minutes (6 hours max)
        self.max_interventions = 20  # Maximum number of interventions
        self.max_cartridge_replacements = 5  # Maximum cartridge swaps

        # Treatment tracking
        self.planned_duration = 0.0  # Original planned duration
        self.extended_duration = 0.0  # Total extensions applied
        self.cartridge_replacements = 0

        # Monitoring history
        self.intervention_log: List[Dict[str, Any]] = []
        self.nh3_history: List[Dict[str, float]] = []

    def run_adaptive_treatment(self, initial_duration: float) -> Dict[str, Any]:
        """
        Run treatment with real-time adaptive control.

        Args:
            initial_duration: Initial planned treatment duration (minutes)

        Returns:
            Dict with treatment summary and intervention history
        """
        self.planned_duration = initial_duration
        self.extended_duration = 0.0
        self.cartridge_replacements = 0
        self.intervention_log = []
        self.nh3_history = []

        print("\n" + "="*70)
        print("ADAPTIVE REAL-TIME BAL TREATMENT")
        print("="*70)
        print(f"Initial planned duration: {initial_duration:.0f} minutes")
        print(f"NH3 target: {self.NH3_target} µmol/L")
        print(f"Monitoring interval: {self.monitoring_interval} minutes")
        print(f"Flow rate range: {self.min_flow_rate}-{self.max_flow_rate} mL/min")
        print(f"Safety limits: Max {self.max_treatment_duration:.0f} min, "
              f"Max {self.max_interventions} interventions, "
              f"Max {self.max_cartridge_replacements} cartridge swaps")
        print("="*70)

        # Track total treatment time
        total_duration = initial_duration
        time_elapsed = 0.0

        # Run treatment with monitoring checkpoints
        while time_elapsed < total_duration:
            # Check safety limits
            if total_duration > self.max_treatment_duration:
                print(f"\n⚠️  SAFETY LIMIT: Maximum treatment duration ({self.max_treatment_duration:.0f} min) reached")
                print("    Treatment terminated to prevent excessive therapy time")
                total_duration = self.max_treatment_duration
                break

            if len(self.intervention_log) >= self.max_interventions:
                print(f"\n⚠️  SAFETY LIMIT: Maximum interventions ({self.max_interventions}) reached")
                print("    Treatment terminated - patient may need alternative therapy")
                break

            if self.cartridge_replacements >= self.max_cartridge_replacements:
                print(f"\n⚠️  SAFETY LIMIT: Maximum cartridge replacements ({self.max_cartridge_replacements}) reached")
                print("    Treatment terminated - no more cartridges available")
                break

            # Run until next checkpoint or end
            next_checkpoint = min(
                time_elapsed + self.monitoring_interval,
                total_duration
            )
            step_duration = next_checkpoint - time_elapsed

            # Run simulation for this segment
            self._run_segment(step_duration)
            time_elapsed = next_checkpoint

            # Check if we've reached a monitoring checkpoint (not the final step)
            if time_elapsed < total_duration:
                # Monitor and potentially intervene
                intervention = self._monitor_and_intervene()

                # If intervention extended duration, update total
                if intervention and intervention.get('duration_extended', 0) > 0:
                    extension = intervention['duration_extended']
                    total_duration += extension
                    self.extended_duration += extension
                    print(f"\n  → Treatment extended by {extension} min")
                    print(f"  → New total duration: {total_duration:.0f} min")

        # Get final results
        final_outputs = self.engine.get_current_outputs()

        return self._generate_summary(final_outputs)

    def _run_segment(self, duration: float):
        """Run simulation for a segment of time."""
        steps = int(duration / self.engine.dt)
        for _ in range(steps):
            self.engine.step()

    def _monitor_and_intervene(self) -> Dict[str, Any]:
        """
        Monitor current state and apply intervention if needed.

        Returns:
            Dict describing the intervention taken (if any)
        """
        # Get current state
        current_outputs = self.engine.get_current_outputs()
        current_time = self.engine.current_time

        # Extract NH3 level from bioreactor
        nh3_level = current_outputs['bioreactor']['C_NH3']
        viability = current_outputs['bioreactor']['cell_viability']
        current_flow = self.engine.pump.Q_target

        # Log NH3 measurement
        self.nh3_history.append({
            'time': current_time,
            'NH3': nh3_level,
            'viability': viability,
            'flow_rate': current_flow
        })

        print(f"\n[t={current_time:.0f} min] NH3={nh3_level:.1f} µmol/L, "
              f"Viability={viability:.1%}, Flow={current_flow:.0f} mL/min")

        # Determine intervention level
        intervention = self._determine_intervention(nh3_level, viability, current_flow)

        if intervention:
            self._apply_intervention(intervention)
            self.intervention_log.append({
                'time': current_time,
                **intervention
            })

        return intervention

    def _determine_intervention(self, nh3_level: float, viability: float,
                                current_flow: float) -> Dict[str, Any]:
        """
        Determine what intervention (if any) is needed.

        Args:
            nh3_level: Current NH3 concentration (µmol/L)
            viability: Current cell viability (0-1)
            current_flow: Current flow rate (mL/min)

        Returns:
            Dict describing intervention, or None if no intervention needed
        """
        # Calculate NH3 ratio relative to target
        nh3_ratio = nh3_level / self.NH3_target

        # No intervention needed if below threshold
        if nh3_ratio <= self.MEDIUM_THRESHOLD:
            print("  ✓ NH3 within acceptable range")
            return None

        # Determine intervention level
        if nh3_ratio > self.CRITICAL_THRESHOLD:
            # CRITICAL: >3× target (>135 µmol/L)
            return {
                'level': 'CRITICAL',
                'nh3_level': nh3_level,
                'nh3_ratio': nh3_ratio,
                'new_flow_rate': self.max_flow_rate,
                'replace_cartridge': True,
                'duration_extended': 60,
                'reason': f'NH3 critically high ({nh3_level:.1f} µmol/L = {nh3_ratio:.1f}× target)'
            }

        elif nh3_ratio > self.HIGH_THRESHOLD:
            # HIGH: >2× target (>90 µmol/L)
            return {
                'level': 'HIGH',
                'nh3_level': nh3_level,
                'nh3_ratio': nh3_ratio,
                'new_flow_rate': min(current_flow + 10, self.max_flow_rate),
                'replace_cartridge': True,
                'duration_extended': 30,
                'reason': f'NH3 high ({nh3_level:.1f} µmol/L = {nh3_ratio:.1f}× target)'
            }

        else:  # MEDIUM_THRESHOLD < nh3_ratio <= HIGH_THRESHOLD
            # MEDIUM: >1.5× target (>67.5 µmol/L)
            return {
                'level': 'MEDIUM',
                'nh3_level': nh3_level,
                'nh3_ratio': nh3_ratio,
                'new_flow_rate': min(current_flow + 5, self.max_flow_rate),
                'replace_cartridge': False,
                'duration_extended': 15,
                'reason': f'NH3 elevated ({nh3_level:.1f} µmol/L = {nh3_ratio:.1f}× target)'
            }

    def _apply_intervention(self, intervention: Dict[str, Any]):
        """
        Apply the determined intervention to the system.

        Args:
            intervention: Dict describing the intervention
        """
        print(f"\n  ⚠️  INTERVENTION [{intervention['level']}]: {intervention['reason']}")

        # Adjust flow rate
        new_flow = intervention['new_flow_rate']
        old_flow = self.engine.pump.Q_target
        self.engine.pump.Q_target = new_flow
        print(f"  → Adjusting flow rate: {old_flow:.0f} → {new_flow:.0f} mL/min")

        # Replace hepatocyte cartridge if needed (and if limit not exceeded)
        if intervention['replace_cartridge']:
            if self.cartridge_replacements < self.max_cartridge_replacements:
                self._replace_cartridge()
            else:
                print(f"  ⚠️  Cannot replace cartridge - limit reached ({self.max_cartridge_replacements})")

        # Duration extension is tracked but applied in run_adaptive_treatment
        extension = intervention['duration_extended']
        print(f"  → Extending treatment by {extension} minutes")

    def _replace_cartridge(self):
        """
        Replace hepatocyte cartridge with fresh cells.

        Simulates cartridge replacement by resetting bioreactor
        cell viability to 100% (fresh hepatocytes).
        """
        old_viability = self.engine.bioreactor.cell_viability

        # Reset cell viability to fresh cartridge
        self.engine.bioreactor.cell_viability = 1.0

        # Reset to normal operation state
        from config.constants import BIOREACTOR_STATES
        self.engine.bioreactor.state = BIOREACTOR_STATES['NORMAL_OPERATION']
        self.engine.bioreactor.time_in_state = 0.0

        self.cartridge_replacements += 1

        print(f"  → Replacing hepatocyte cartridge (#{self.cartridge_replacements})")
        print(f"     Viability: {old_viability:.1%} → 100% (fresh cells)")

    def _generate_summary(self, final_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive treatment summary.

        Args:
            final_outputs: Final simulation outputs

        Returns:
            Dict with complete treatment summary
        """
        # Extract final metrics
        final_nh3 = final_outputs['bioreactor']['C_NH3']
        final_viability = final_outputs['bioreactor']['cell_viability']
        final_clearance = final_outputs['bioreactor']['NH3_clearance']
        treatment_success = final_outputs['return_monitor']['treatment_success']

        # Check if safety limits were hit
        safety_limits_hit = {
            'max_duration': self.engine.current_time >= self.max_treatment_duration,
            'max_interventions': len(self.intervention_log) >= self.max_interventions,
            'max_cartridges': self.cartridge_replacements >= self.max_cartridge_replacements
        }

        summary = {
            'treatment_duration': {
                'planned': self.planned_duration,
                'extended': self.extended_duration,
                'total': self.engine.current_time
            },
            'final_metrics': {
                'NH3_level': final_nh3,
                'NH3_clearance': final_clearance,
                'cell_viability': final_viability,
                'treatment_success': treatment_success
            },
            'interventions': {
                'total_count': len(self.intervention_log),
                'cartridge_replacements': self.cartridge_replacements,
                'log': self.intervention_log
            },
            'safety_limits': safety_limits_hit,
            'nh3_history': self.nh3_history
        }

        # Print summary
        self._print_summary(summary)

        return summary

    def _print_summary(self, summary: Dict[str, Any]):
        """Print formatted treatment summary."""
        print("\n" + "="*70)
        print("TREATMENT SUMMARY")
        print("="*70)

        # Duration
        print("\nDuration:")
        print(f"  Planned:  {summary['treatment_duration']['planned']:.0f} minutes")
        print(f"  Extended: +{summary['treatment_duration']['extended']:.0f} minutes")
        print(f"  Total:    {summary['treatment_duration']['total']:.0f} minutes")

        # Final metrics
        print("\nFinal Metrics:")
        print(f"  NH3 level:     {summary['final_metrics']['NH3_level']:.1f} µmol/L "
              f"(target: {self.NH3_target} µmol/L)")
        print(f"  NH3 clearance: {summary['final_metrics']['NH3_clearance']:.1%}")
        print(f"  Cell viability: {summary['final_metrics']['cell_viability']:.1%}")
        print(f"  Treatment success: {summary['final_metrics']['treatment_success']}")

        # Interventions
        print(f"\nInterventions:")
        print(f"  Total interventions: {summary['interventions']['total_count']}")
        print(f"  Cartridge replacements: {summary['interventions']['cartridge_replacements']}")

        # Safety limits
        if any(summary['safety_limits'].values()):
            print("\n⚠️  Safety Limits Reached:")
            if summary['safety_limits']['max_duration']:
                print(f"    • Maximum treatment duration ({self.max_treatment_duration:.0f} min)")
            if summary['safety_limits']['max_interventions']:
                print(f"    • Maximum interventions ({self.max_interventions})")
            if summary['safety_limits']['max_cartridges']:
                print(f"    • Maximum cartridge replacements ({self.max_cartridge_replacements})")

        if summary['interventions']['log']:
            print("\n  Intervention Log:")
            for i, intervention in enumerate(summary['interventions']['log'], 1):
                print(f"    {i}. t={intervention['time']:.0f} min - "
                      f"{intervention['level']}: {intervention['reason']}")
                print(f"       Flow: {intervention['new_flow_rate']:.0f} mL/min, "
                      f"Cartridge: {intervention['replace_cartridge']}, "
                      f"Extend: +{intervention['duration_extended']} min")

        print("="*70)


def demo_adaptive_treatment():
    """
    Demonstration of adaptive real-time control.

    Shows how the controller automatically adjusts treatment parameters
    in response to changing NH3 levels.
    """
    print("\n" + "="*70)
    print("DEMO: Adaptive Real-Time BAL Treatment")
    print("="*70)

    # Create simulation engine
    engine = SimulationEngine(dt=1.0)

    # Create adaptive controller
    controller = RealtimeAdaptiveController(engine)

    # Run 180-minute treatment with adaptive control
    # The controller will automatically:
    # - Monitor NH3 every 10 minutes
    # - Adjust flow rate if NH3 is too high
    # - Replace cartridge if viability drops
    # - Extend treatment if needed
    summary = controller.run_adaptive_treatment(initial_duration=180)

    return summary


if __name__ == '__main__':
    # Run demonstration
    summary = demo_adaptive_treatment()

    # Additional analysis
    print("\n" + "="*70)
    print("NH3 MONITORING TIMELINE")
    print("="*70)
    print(f"{'Time (min)':<12} {'NH3 (µmol/L)':<15} {'Viability':<12} {'Flow (mL/min)'}")
    print("-"*70)
    for record in summary['nh3_history']:
        print(f"{record['time']:<12.0f} {record['NH3']:<15.1f} "
              f"{record['viability']:<12.1%} {record['flow_rate']:.0f}")
    print("="*70)
