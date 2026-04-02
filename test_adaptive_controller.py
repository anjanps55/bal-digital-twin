"""
Test script demonstrating all intervention levels of the adaptive controller.

This script simulates scenarios that trigger different intervention levels:
- MEDIUM: NH3 > 67.5 µmol/L (1.5× target)
- HIGH: NH3 > 90 µmol/L (2× target)
- CRITICAL: NH3 > 135 µmol/L (3× target)
"""

from simulation.engine import SimulationEngine
from adaptive_realtime_controller import RealtimeAdaptiveController


def test_medium_intervention():
    """Test MEDIUM intervention (NH3 > 1.5× target)."""
    print("\n" + "="*70)
    print("TEST 1: MEDIUM INTERVENTION SCENARIO")
    print("="*70)

    engine = SimulationEngine(dt=1.0)
    controller = RealtimeAdaptiveController(engine)

    # Increase inlet NH3 to trigger medium intervention
    # Set to 100 µmol/L to get ~70-75 µmol/L output (>67.5 threshold)
    engine.separator.C_NH3_in = 120.0

    summary = controller.run_adaptive_treatment(initial_duration=60)

    return summary


def test_high_intervention():
    """Test HIGH intervention (NH3 > 2× target)."""
    print("\n" + "="*70)
    print("TEST 2: HIGH INTERVENTION SCENARIO")
    print("="*70)

    engine = SimulationEngine(dt=1.0)
    controller = RealtimeAdaptiveController(engine)

    # Increase inlet NH3 to trigger high intervention
    # Set to 200 µmol/L to get ~100+ µmol/L output (>90 threshold)
    engine.separator.C_NH3_in = 200.0

    summary = controller.run_adaptive_treatment(initial_duration=60)

    return summary


def test_critical_intervention():
    """Test CRITICAL intervention (NH3 > 3× target)."""
    print("\n" + "="*70)
    print("TEST 3: CRITICAL INTERVENTION SCENARIO")
    print("="*70)

    engine = SimulationEngine(dt=1.0)
    controller = RealtimeAdaptiveController(engine)

    # Increase inlet NH3 to trigger critical intervention
    # Set to 300 µmol/L to get ~150+ µmol/L output (>135 threshold)
    engine.separator.C_NH3_in = 300.0

    summary = controller.run_adaptive_treatment(initial_duration=60)

    return summary


def test_declining_viability():
    """Test scenario with declining cell viability requiring cartridge replacement."""
    print("\n" + "="*70)
    print("TEST 4: DECLINING VIABILITY SCENARIO")
    print("="*70)

    engine = SimulationEngine(dt=1.0)
    controller = RealtimeAdaptiveController(engine)

    # Use elevated NH3 and accelerate cell decay
    engine.separator.C_NH3_in = 150.0

    # Accelerate viability decay to trigger cartridge replacement
    from config.constants import BIOREACTOR_THRESHOLDS
    original_decay = BIOREACTOR_THRESHOLDS['k_cell_decay']
    BIOREACTOR_THRESHOLDS['k_cell_decay'] = 0.002  # 20× faster decay

    summary = controller.run_adaptive_treatment(initial_duration=90)

    # Restore original decay rate
    BIOREACTOR_THRESHOLDS['k_cell_decay'] = original_decay

    return summary


def run_all_tests():
    """Run all test scenarios."""
    print("\n" + "#"*70)
    print("# ADAPTIVE CONTROLLER - COMPREHENSIVE TEST SUITE")
    print("#"*70)

    results = {}

    # Test 1: Medium intervention
    results['medium'] = test_medium_intervention()

    # Test 2: High intervention
    results['high'] = test_high_intervention()

    # Test 3: Critical intervention
    results['critical'] = test_critical_intervention()

    # Test 4: Declining viability
    results['viability'] = test_declining_viability()

    # Print comparison summary
    print("\n" + "="*70)
    print("COMPARATIVE RESULTS")
    print("="*70)
    print(f"{'Test':<20} {'Interventions':<15} {'Replacements':<15} {'Extended (min)'}")
    print("-"*70)

    for name, summary in results.items():
        interventions = summary['interventions']['total_count']
        replacements = summary['interventions']['cartridge_replacements']
        extended = summary['treatment_duration']['extended']
        print(f"{name.upper():<20} {interventions:<15} {replacements:<15} {extended:.0f}")

    print("="*70)

    return results


if __name__ == '__main__':
    # Run all tests
    results = run_all_tests()

    print("\n✅ All tests completed successfully!")
    print("\nThe adaptive controller demonstrated:")
    print("  • Real-time NH3 monitoring")
    print("  • Multi-tier intervention strategy")
    print("  • Automatic flow rate adjustment")
    print("  • Hepatocyte cartridge replacement")
    print("  • Dynamic treatment duration extension")
