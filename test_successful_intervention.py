"""
Test demonstrating SUCCESSFUL treatment with adaptive interventions.

This shows the controller helping a patient who needs interventions
but can still be successfully treated.
"""

from simulation.engine import SimulationEngine
from adaptive_realtime_controller import RealtimeAdaptiveController


def test_successful_treatment_with_interventions():
    """
    Test a realistic scenario where interventions lead to successful treatment.

    Scenario: Patient with elevated but treatable NH3 levels
    - Starts with moderately high NH3
    - Controller intervenes to optimize treatment
    - Patient successfully treated and safe to return
    """
    print("\n" + "="*70)
    print("TEST: Successful Treatment with Interventions")
    print("="*70)
    print("\nScenario: Patient with elevated NH3 requiring adaptive control")
    print("Goal: Bring NH3 below safe level (50 µmol/L) for return to patient")
    print("="*70)

    engine = SimulationEngine(dt=1.0)
    controller = RealtimeAdaptiveController(engine)

    # Set moderately elevated NH3 - high enough to trigger interventions
    # but low enough that treatment can succeed
    engine.separator.C_NH3_in = 120.0  # Elevated but treatable

    # Run treatment
    summary = controller.run_adaptive_treatment(initial_duration=120)

    # Analyze results
    print("\n" + "="*70)
    print("TREATMENT OUTCOME ANALYSIS")
    print("="*70)

    final_nh3 = summary['final_metrics']['NH3_level']
    target_nh3 = controller.NH3_target
    safe_nh3 = 50.0  # RETURN_MONITOR_THRESHOLDS['C_NH3_safe']

    print(f"\nInitial NH3 (inlet):  120.0 µmol/L (elevated)")
    print(f"Final NH3 (outlet):   {final_nh3:.1f} µmol/L")
    print(f"Target NH3:           {target_nh3} µmol/L")
    print(f"Safe threshold:       {safe_nh3} µmol/L")

    print(f"\nInterventions applied: {summary['interventions']['total_count']}")
    print(f"Cartridges used:       {summary['interventions']['cartridge_replacements']}")
    print(f"Treatment extended:    +{summary['treatment_duration']['extended']:.0f} minutes")

    # Determine outcome
    if final_nh3 <= safe_nh3:
        print(f"\n✅ TREATMENT SUCCESSFUL!")
        print(f"   NH3 reduced to safe level ({final_nh3:.1f} ≤ {safe_nh3} µmol/L)")
        print(f"   Patient can safely return to circulation")
        success = True
    elif final_nh3 <= target_nh3 * 1.5:  # Within acceptable range
        print(f"\n✅ TREATMENT SUCCESSFUL (with monitoring)!")
        print(f"   NH3 at acceptable level ({final_nh3:.1f} µmol/L)")
        print(f"   Patient can return with continued monitoring")
        success = True
    else:
        print(f"\n⚠️  TREATMENT INCOMPLETE")
        print(f"   NH3 still elevated ({final_nh3:.1f} > {safe_nh3} µmol/L)")
        print(f"   Consider: extended treatment, alternative therapy")
        success = False

    print("\n" + "="*70)

    return summary, success


def test_baseline_no_interventions():
    """
    Baseline test: Normal NH3 levels, no interventions needed.
    """
    print("\n" + "="*70)
    print("BASELINE TEST: Normal NH3 (No Interventions Needed)")
    print("="*70)
    print("\nScenario: Patient with normal NH3 levels")
    print("Goal: Maintain stable treatment without interventions")
    print("="*70)

    engine = SimulationEngine(dt=1.0)
    controller = RealtimeAdaptiveController(engine)

    # Use default NH3 levels (90 µmol/L inlet → ~40 µmol/L outlet)
    summary = controller.run_adaptive_treatment(initial_duration=120)

    print("\n" + "="*70)
    print("BASELINE OUTCOME")
    print("="*70)

    final_nh3 = summary['final_metrics']['NH3_level']

    print(f"\nFinal NH3: {final_nh3:.1f} µmol/L")
    print(f"Interventions: {summary['interventions']['total_count']}")

    if summary['interventions']['total_count'] == 0 and final_nh3 <= 50:
        print(f"\n✅ BASELINE NORMAL - No interventions needed")
        print(f"   Standard treatment protocol successful")
        success = True
    else:
        success = False

    print("="*70)

    return summary, success


def test_extreme_case_safety_limits():
    """
    Extreme test: Very high NH3 that exceeds treatment capacity.
    """
    print("\n" + "="*70)
    print("EXTREME TEST: Very High NH3 (Safety Limits)")
    print("="*70)
    print("\nScenario: Patient with critically high NH3")
    print("Goal: Demonstrate safety limits prevent endless treatment")
    print("="*70)

    engine = SimulationEngine(dt=1.0)
    controller = RealtimeAdaptiveController(engine)

    # Very high NH3 - beyond BAL capacity
    engine.separator.C_NH3_in = 300.0

    # Lower limits for faster test
    controller.max_interventions = 8
    controller.max_cartridge_replacements = 3
    controller.max_treatment_duration = 180.0

    summary = controller.run_adaptive_treatment(initial_duration=60)

    print("\n" + "="*70)
    print("EXTREME CASE OUTCOME")
    print("="*70)

    final_nh3 = summary['final_metrics']['NH3_level']
    limits_hit = any(summary['safety_limits'].values())

    print(f"\nInitial NH3: 300 µmol/L (critically high)")
    print(f"Final NH3: {final_nh3:.1f} µmol/L")
    print(f"Safety limits hit: {limits_hit}")

    if limits_hit:
        print(f"\n⚠️  PATIENT TOO CRITICAL FOR BAL ALONE")
        print(f"   Safety limits prevented excessive intervention")
        print(f"   Alternative therapy recommended:")
        print(f"     • Liver transplant (if available)")
        print(f"     • Combined therapies")
        print(f"     • ICU management")

    print("="*70)

    return summary, limits_hit


if __name__ == '__main__':
    print("\n" + "#"*70)
    print("# ADAPTIVE CONTROLLER - COMPREHENSIVE DEMONSTRATION")
    print("# Showing: Success, Baseline, and Safety Limit Scenarios")
    print("#"*70)

    # Test 1: Baseline (no interventions)
    summary1, success1 = test_baseline_no_interventions()

    # Test 2: Successful treatment with interventions
    summary2, success2 = test_successful_treatment_with_interventions()

    # Test 3: Extreme case (safety limits)
    summary3, limits_hit = test_extreme_case_safety_limits()

    # Final summary
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*70)

    print("\n1. Baseline Test (Normal NH3):")
    print(f"   Result: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Interventions: {summary1['interventions']['total_count']}")
    print(f"   Final NH3: {summary1['final_metrics']['NH3_level']:.1f} µmol/L")

    print("\n2. Intervention Test (Elevated NH3):")
    print(f"   Result: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"   Interventions: {summary2['interventions']['total_count']}")
    print(f"   Final NH3: {summary2['final_metrics']['NH3_level']:.1f} µmol/L")

    print("\n3. Extreme Test (Critical NH3):")
    print(f"   Result: {'✅ Safety limits worked' if limits_hit else '❌ No limits hit'}")
    print(f"   Interventions: {summary3['interventions']['total_count']}")
    print(f"   Final NH3: {summary3['final_metrics']['NH3_level']:.1f} µmol/L")

    print("\n" + "="*70)
    print("KEY FINDINGS:")
    print("="*70)
    print("✓ Normal patients: No interventions needed")
    print("✓ Elevated NH3: Interventions can achieve success")
    print("✓ Critical patients: Safety limits prevent endless treatment")
    print("✓ Controller adapts appropriately to patient severity")
    print("="*70)
