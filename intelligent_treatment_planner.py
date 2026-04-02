"""
Intelligent Treatment Planner for BAL System

Automatically calculates optimal treatment parameters based on patient condition.
No trial-and-error needed - the system figures out what's needed for success!
"""

from typing import Dict, Any, Tuple
from simulation.engine import SimulationEngine
from adaptive_realtime_controller import RealtimeAdaptiveController
import math


class IntelligentTreatmentPlanner:
    """
    Analyzes patient condition and automatically determines optimal treatment parameters.

    Instead of guessing duration and flow rate, this planner:
    1. Analyzes patient toxin levels and severity
    2. Calculates required treatment parameters
    3. Pre-optimizes for successful clearance
    4. Runs treatment with calculated optimal settings
    """

    def __init__(self):
        """Initialize treatment planner with clinical knowledge."""

        # Target levels for successful treatment
        self.NH3_target_safe = 50.0  # µmol/L - maximum safe level
        self.NH3_target_optimal = 45.0  # µmol/L - optimal target
        self.lido_target_safe = 15.0  # µmol/L

        # Hepatocyte performance parameters (from bioreactor constants)
        self.base_NH3_clearance_rate = 0.50  # 50% clearance at baseline
        self.base_lido_clearance_rate = 0.60  # 60% clearance at baseline

        # Flow rate impact on clearance (higher flow = better clearance)
        self.flow_clearance_factor = 0.008  # 0.8% improvement per mL/min increase

        # Fresh cartridge impact
        self.fresh_cartridge_boost = 1.3  # 30% better performance

    def analyze_patient(self, NH3_initial: float, lido_initial: float) -> Dict[str, Any]:
        """
        Analyze patient condition and determine severity.

        Args:
            NH3_initial: Initial NH3 concentration (µmol/L)
            lido_initial: Initial lidocaine concentration (µmol/L)

        Returns:
            Dict with patient analysis
        """
        analysis = {
            'NH3_initial': NH3_initial,
            'lido_initial': lido_initial,
            'NH3_excess': NH3_initial - self.NH3_target_safe,
            'lido_excess': lido_initial - self.lido_target_safe,
        }

        # Determine severity based on NH3 levels
        if NH3_initial < 50:
            severity = 'NORMAL'
            risk_level = 1
        elif NH3_initial < 90:
            severity = 'MILD'
            risk_level = 2
        elif NH3_initial < 150:
            severity = 'MODERATE'
            risk_level = 3
        elif NH3_initial < 250:
            severity = 'SEVERE'
            risk_level = 4
        else:
            severity = 'CRITICAL'
            risk_level = 5

        analysis['severity'] = severity
        analysis['risk_level'] = risk_level

        # Calculate NH3 reduction needed
        analysis['NH3_reduction_needed'] = max(0, NH3_initial - self.NH3_target_optimal)
        analysis['NH3_reduction_percent'] = (analysis['NH3_reduction_needed'] / NH3_initial * 100) if NH3_initial > 0 else 0

        return analysis

    def calculate_optimal_parameters(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate optimal treatment parameters based on patient analysis.

        This is the core intelligence - determines exactly what's needed for success.

        Args:
            analysis: Patient analysis from analyze_patient()

        Returns:
            Dict with optimal treatment parameters
        """
        NH3_initial = analysis['NH3_initial']
        severity = analysis['severity']
        risk_level = analysis['risk_level']
        reduction_needed_pct = analysis['NH3_reduction_percent']

        # Initialize optimal parameters
        optimal = {
            'initial_flow_rate': 30.0,  # mL/min
            'initial_duration': 120.0,  # minutes
            'use_fresh_cartridge': False,
            'enable_adaptive': True,
            'estimated_final_NH3': 0.0,
            'confidence': 'HIGH'
        }

        # Calculate required clearance efficiency
        # We need to remove enough NH3 to reach target
        target_clearance = reduction_needed_pct / 100.0

        # Determine if fresh cartridge needed
        if target_clearance > 0.60:  # Need >60% clearance
            optimal['use_fresh_cartridge'] = True
            effective_clearance_rate = self.base_NH3_clearance_rate * self.fresh_cartridge_boost
        else:
            effective_clearance_rate = self.base_NH3_clearance_rate

        # Calculate optimal flow rate
        # Higher flow = better clearance up to a limit
        if severity == 'NORMAL':
            optimal['initial_flow_rate'] = 30.0
            optimal['initial_duration'] = 90.0

        elif severity == 'MILD':
            optimal['initial_flow_rate'] = 35.0
            optimal['initial_duration'] = 120.0

        elif severity == 'MODERATE':
            optimal['initial_flow_rate'] = 40.0
            optimal['initial_duration'] = 150.0
            optimal['use_fresh_cartridge'] = True

        elif severity == 'SEVERE':
            optimal['initial_flow_rate'] = 50.0
            optimal['initial_duration'] = 180.0
            optimal['use_fresh_cartridge'] = True

        elif severity == 'CRITICAL':
            optimal['initial_flow_rate'] = 60.0  # Maximum
            optimal['initial_duration'] = 240.0
            optimal['use_fresh_cartridge'] = True
            optimal['confidence'] = 'MEDIUM'

            # For extremely high NH3, warn that success may not be guaranteed
            if NH3_initial > 300:
                optimal['confidence'] = 'LOW'
                optimal['initial_duration'] = 300.0  # Extended

        # Refine flow rate based on exact NH3 level
        # Flow rate optimization formula
        if NH3_initial > 100:
            # For high NH3, calculate optimal flow more precisely
            excess_nh3 = NH3_initial - self.NH3_target_optimal
            # Each 50 µmol/L excess suggests +5 mL/min flow
            flow_adjustment = (excess_nh3 / 50) * 5
            optimal['initial_flow_rate'] = min(60.0, optimal['initial_flow_rate'] + flow_adjustment)

        # Calculate duration based on clearance kinetics
        # Exponential decay: C(t) = C0 * e^(-k*t)
        # We want: C(t) / C0 = target_ratio
        if target_clearance > 0:
            # Estimate time constant based on flow and clearance
            k_clearance = effective_clearance_rate * (optimal['initial_flow_rate'] / 30.0)  # Normalized to 30 mL/min

            # Time to reach target (minutes)
            if k_clearance > 0.001:
                target_ratio = 1.0 - target_clearance
                if target_ratio > 0:
                    calculated_duration = -math.log(target_ratio) / (k_clearance / 60.0)  # Convert to minutes

                    # Add safety margin (20% extra time)
                    optimal['initial_duration'] = calculated_duration * 1.2

                    # Ensure reasonable bounds
                    optimal['initial_duration'] = max(60.0, min(360.0, optimal['initial_duration']))

        # Estimate final NH3
        # Using exponential decay model
        flow_factor = optimal['initial_flow_rate'] / 30.0
        cartridge_factor = self.fresh_cartridge_boost if optimal['use_fresh_cartridge'] else 1.0
        clearance_rate = self.base_NH3_clearance_rate * flow_factor * cartridge_factor

        time_hours = optimal['initial_duration'] / 60.0
        decay_factor = math.exp(-clearance_rate * time_hours)
        optimal['estimated_final_NH3'] = NH3_initial * decay_factor

        # Adjust if estimated final is still too high
        if optimal['estimated_final_NH3'] > self.NH3_target_safe:
            # Need more time or flow
            additional_reduction = (optimal['estimated_final_NH3'] - self.NH3_target_optimal) / NH3_initial
            additional_time = -math.log(1.0 - additional_reduction) / (clearance_rate / 60.0)
            optimal['initial_duration'] += additional_time * 1.2
            optimal['initial_duration'] = min(360.0, optimal['initial_duration'])

            # Recalculate estimate
            time_hours = optimal['initial_duration'] / 60.0
            decay_factor = math.exp(-clearance_rate * time_hours)
            optimal['estimated_final_NH3'] = NH3_initial * decay_factor

        return optimal

    def show_treatment_plan(self, analysis: Dict[str, Any], optimal: Dict[str, Any]):
        """Display the calculated treatment plan."""
        print("\n" + "="*70)
        print("  🧠 INTELLIGENT TREATMENT PLAN")
        print("="*70)

        print(f"\n📊 PATIENT ANALYSIS:")
        print(f"  Initial NH₃:        {analysis['NH3_initial']:.1f} µmol/L")
        print(f"  Severity:           {analysis['severity']}")
        print(f"  Risk Level:         {'⚠️ ' * analysis['risk_level']}")
        print(f"  Reduction Needed:   {analysis['NH3_reduction_needed']:.1f} µmol/L ({analysis['NH3_reduction_percent']:.1f}%)")

        print(f"\n🎯 CALCULATED OPTIMAL PARAMETERS:")
        print(f"  Flow Rate:          {optimal['initial_flow_rate']:.0f} mL/min")
        print(f"  Duration:           {optimal['initial_duration']:.0f} minutes ({optimal['initial_duration']/60:.1f} hours)")
        print(f"  Fresh Cartridge:    {'Yes ✅' if optimal['use_fresh_cartridge'] else 'No (standard)'}")
        print(f"  Adaptive Control:   {'Enabled 🤖' if optimal['enable_adaptive'] else 'Disabled'}")

        print(f"\n📈 PREDICTED OUTCOME:")
        print(f"  Estimated Final NH₃: {optimal['estimated_final_NH3']:.1f} µmol/L")

        target_met = optimal['estimated_final_NH3'] <= self.NH3_target_safe
        print(f"  Target Achievement:  {'✅ Expected SUCCESS' if target_met else '⚠️  May need adjustments'}")
        print(f"  Confidence:          {optimal['confidence']}")

        print(f"\n💡 RATIONALE:")
        if analysis['severity'] == 'NORMAL':
            print(f"  Standard treatment protocol - minimal intervention needed")
        elif analysis['severity'] == 'MILD':
            print(f"  Slightly elevated toxins - modest flow increase and extended time")
        elif analysis['severity'] == 'MODERATE':
            print(f"  Significant toxin load - fresh cartridge + higher flow required")
        elif analysis['severity'] == 'SEVERE':
            print(f"  High toxin levels - maximum flow + fresh cells + extended duration")
        elif analysis['severity'] == 'CRITICAL':
            print(f"  Critical condition - aggressive therapy with all available interventions")
            if optimal['confidence'] == 'LOW':
                print(f"  ⚠️  Patient may require liver transplant if BAL therapy insufficient")

        print("="*70)

    def plan_and_execute(self, NH3_initial: float, lido_initial: float,
                        patient_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Complete intelligent treatment planning and execution.

        Args:
            NH3_initial: Initial NH3 concentration (µmol/L)
            lido_initial: Initial lidocaine concentration (µmol/L)
            patient_params: Optional additional patient parameters

        Returns:
            Dict with complete treatment results
        """
        print("\n" + "="*70)
        print("  🧠 INTELLIGENT TREATMENT PLANNING SYSTEM")
        print("="*70)
        print("\nAnalyzing patient condition and calculating optimal parameters...")

        # Step 1: Analyze patient
        analysis = self.analyze_patient(NH3_initial, lido_initial)

        # Step 2: Calculate optimal parameters
        optimal = self.calculate_optimal_parameters(analysis)

        # Step 3: Show treatment plan
        self.show_treatment_plan(analysis, optimal)

        # Step 4: Execute treatment with optimal parameters
        print("\n" + "="*70)
        print("  🚀 EXECUTING OPTIMIZED TREATMENT")
        print("="*70)
        print("\nApplying calculated parameters to simulation...")

        # Create simulation engine
        engine = SimulationEngine(dt=1.0)

        # Apply patient parameters
        if patient_params:
            engine.separator.Q_blood_in = patient_params.get('Q_blood', 150)
            engine.separator.Hct_in = patient_params.get('Hct', 0.32)

        engine.separator.C_NH3_in = NH3_initial
        engine.separator.C_lido_in = lido_initial

        # Apply optimal flow rate
        engine.pump.Q_target = optimal['initial_flow_rate']

        # Apply fresh cartridge if recommended
        if optimal['use_fresh_cartridge']:
            print("  ✅ Installing fresh hepatocyte cartridge...")
            engine.bioreactor.cell_viability = 1.0

            # Boost clearance rates for fresh cartridge
            from config.constants import HEPATOCYTE_KINETICS
            HEPATOCYTE_KINETICS['k1_NH3_base'] = 1.0 * self.fresh_cartridge_boost
            HEPATOCYTE_KINETICS['k1_lido_base'] = 0.85 * self.fresh_cartridge_boost

        print(f"  ✅ Flow rate set to {optimal['initial_flow_rate']:.0f} mL/min")
        print(f"  ✅ Treatment duration: {optimal['initial_duration']:.0f} minutes")

        # Create adaptive controller with optimal settings
        controller = RealtimeAdaptiveController(engine)

        # Run treatment with calculated duration
        summary = controller.run_adaptive_treatment(initial_duration=optimal['initial_duration'])

        # Add planning info to summary
        summary['treatment_plan'] = {
            'analysis': analysis,
            'optimal_parameters': optimal,
            'planning_accuracy': self._calculate_planning_accuracy(optimal, summary)
        }

        return summary

    def _calculate_planning_accuracy(self, optimal: Dict[str, Any],
                                     summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate how accurate the planning was."""
        estimated_nh3 = optimal['estimated_final_NH3']
        actual_nh3 = summary['final_metrics']['NH3_level']

        error = abs(estimated_nh3 - actual_nh3)
        error_percent = (error / estimated_nh3 * 100) if estimated_nh3 > 0 else 0

        if error_percent < 10:
            accuracy_rating = "EXCELLENT"
        elif error_percent < 20:
            accuracy_rating = "GOOD"
        elif error_percent < 30:
            accuracy_rating = "FAIR"
        else:
            accuracy_rating = "NEEDS_REFINEMENT"

        return {
            'estimated_NH3': estimated_nh3,
            'actual_NH3': actual_nh3,
            'error': error,
            'error_percent': error_percent,
            'accuracy_rating': accuracy_rating
        }


def demo_intelligent_planner():
    """Demonstration of intelligent treatment planning."""
    print("\n" + "#"*70)
    print("# INTELLIGENT TREATMENT PLANNER - DEMO")
    print("#"*70)

    planner = IntelligentTreatmentPlanner()

    # Test case 1: Moderate patient
    print("\n\n" + "="*70)
    print("TEST CASE 1: Moderate Patient")
    print("="*70)

    summary1 = planner.plan_and_execute(NH3_initial=120, lido_initial=25)

    print("\n" + "="*70)
    print("  PLANNING ACCURACY ASSESSMENT")
    print("="*70)
    accuracy = summary1['treatment_plan']['planning_accuracy']
    print(f"\nEstimated Final NH₃: {accuracy['estimated_NH3']:.1f} µmol/L")
    print(f"Actual Final NH₃:    {accuracy['actual_NH3']:.1f} µmol/L")
    print(f"Prediction Error:    {accuracy['error']:.1f} µmol/L ({accuracy['error_percent']:.1f}%)")
    print(f"Accuracy Rating:     {accuracy['accuracy_rating']}")
    print("="*70)

    return summary1


if __name__ == '__main__':
    demo_intelligent_planner()
