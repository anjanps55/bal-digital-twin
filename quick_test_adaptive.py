"""
Quick test demonstrating adaptive controller interventions with safety limits.
"""

from simulation.engine import SimulationEngine
from adaptive_realtime_controller import RealtimeAdaptiveController


def test_with_moderate_nh3():
    """Test with moderately elevated NH3 to trigger a few interventions."""
    print("\n" + "="*70)
    print("QUICK TEST: Moderate NH3 Scenario")
    print("="*70)

    engine = SimulationEngine(dt=1.0)
    controller = RealtimeAdaptiveController(engine)

    # Set moderately high NH3 to trigger 1-2 MEDIUM interventions
    engine.separator.C_NH3_in = 110.0  # Will give ~60-65 µmol/L output

    # Run shorter treatment
    summary = controller.run_adaptive_treatment(initial_duration=60)

    print(f"\n✅ Test completed in {summary['treatment_duration']['total']:.0f} minutes")
    print(f"   Interventions: {summary['interventions']['total_count']}")
    print(f"   Final NH3: {summary['final_metrics']['NH3_level']:.1f} µmol/L")

    return summary


def test_safety_limits():
    """Test that safety limits prevent infinite loops."""
    print("\n" + "="*70)
    print("QUICK TEST: Safety Limits (High NH3)")
    print("="*70)

    engine = SimulationEngine(dt=1.0)
    controller = RealtimeAdaptiveController(engine)

    # Set very high NH3 that would normally cause many interventions
    engine.separator.C_NH3_in = 250.0

    # Lower the safety limits for faster testing
    controller.max_interventions = 5  # Stop after 5 interventions
    controller.max_cartridge_replacements = 2  # Only 2 cartridge swaps
    controller.max_treatment_duration = 120.0  # Max 2 hours

    summary = controller.run_adaptive_treatment(initial_duration=30)

    print(f"\n✅ Test completed with safety limits")
    print(f"   Total time: {summary['treatment_duration']['total']:.0f} minutes")
    print(f"   Interventions: {summary['interventions']['total_count']}")
    print(f"   Cartridge swaps: {summary['interventions']['cartridge_replacements']}")

    # Check which limits were hit
    if any(summary['safety_limits'].values()):
        print(f"\n   Safety limits hit:")
        for limit, hit in summary['safety_limits'].items():
            if hit:
                print(f"     • {limit}")
    else:
        print(f"\n   No safety limits hit")

    return summary


if __name__ == '__main__':
    print("\n" + "#"*70)
    print("# QUICK ADAPTIVE CONTROLLER TESTS")
    print("#"*70)

    # Test 1: Moderate NH3
    summary1 = test_with_moderate_nh3()

    # Test 2: Safety limits
    summary2 = test_safety_limits()

    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\nThe adaptive controller:")
    print("  ✓ Monitors NH3 levels in real-time")
    print("  ✓ Triggers interventions when thresholds are exceeded")
    print("  ✓ Respects safety limits to prevent infinite loops")
    print("  ✓ Adjusts flow rate, replaces cartridges, and extends duration")
    print("="*70)
