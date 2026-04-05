"""
Adaptive BAL Controller
Automatically adjusts treatment parameters based on toxin levels
"""

import sys
sys.path.insert(0, '.')

from simulation.engine import SimulationEngine
import config.constants as const
import pandas as pd


class AdaptiveBALController:
    """Smart controller that adjusts treatment in real-time"""
    
    def __init__(self):
        self.adjustment_history = []
    
    def assess_severity(self, nh3_level, lido_level):
        """
        Classify patient severity based on toxin levels
        
        Returns: 'mild', 'moderate', 'severe', or 'critical'
        """
        # NH3 severity thresholds (µmol/L)
        # Normal: <35, Elevated: 35-80, Severe: 80-150, Critical: >150
        
        if nh3_level < 35:
            nh3_severity = 'normal'
        elif nh3_level < 80:
            nh3_severity = 'mild'
        elif nh3_level < 150:
            nh3_severity = 'severe'
        else:
            nh3_severity = 'critical'
        
        # Lidocaine severity (µmol/L)
        # Normal: <10, Elevated: 10-20, Severe: 20-30, Critical: >30
        
        if lido_level < 10:
            lido_severity = 'normal'
        elif lido_level < 20:
            lido_severity = 'mild'
        elif lido_level < 30:
            lido_severity = 'severe'
        else:
            lido_severity = 'critical'
        
        # Return worst case
        severities = ['normal', 'mild', 'severe', 'critical']
        nh3_idx = severities.index(nh3_severity)
        lido_idx = severities.index(lido_severity)
        
        return severities[max(nh3_idx, lido_idx)]
    
    def calculate_adjustments(self, severity, nh3_level, lido_level):
        """
        Calculate real-world adjustable parameters based on severity
        
        Real-world adjustments:
        1. Flow rate (Q_plasma) - operator can adjust pump speed
        2. Treatment duration - can extend if needed
        3. Temperature (affects reaction rates)
        4. Can add fresh hepatocyte cartridge (increases k1 effectively)
        
        Returns: dict of adjustments
        """
        
        adjustments = {
            'Q_plasma': 75,  # Default (per unit, flat-disc design)
            'duration': 60,   # Default
            'temperature_boost': 0,  # Default: 37°C (no boost)
            'fresh_cartridge': False,  # Default: use existing
            'k1_multiplier': 1.0,  # Represents fresh vs aged hepatocytes
            'severity': severity
        }

        if severity == 'mild':
            # Mild case: standard treatment, maybe extend slightly
            adjustments['duration'] = 90
            adjustments['Q_plasma'] = 75

        elif severity == 'severe':
            # Severe case: increase flow OR use fresh cartridge
            adjustments['duration'] = 120
            adjustments['Q_plasma'] = 90  # Increase flow 20%
            adjustments['fresh_cartridge'] = True  # Use fresh hepatocytes
            adjustments['k1_multiplier'] = 1.5  # Fresh cells are more active

        elif severity == 'critical':
            # Critical case: all adjustments
            adjustments['duration'] = 180
            adjustments['Q_plasma'] = 110  # Increase flow ~47%
            adjustments['temperature_boost'] = 0.5  # Slight temp increase (37→37.5°C)
            adjustments['fresh_cartridge'] = True
            adjustments['k1_multiplier'] = 2.0  # Fresh + optimized
        
        # Fine-tune based on specific levels
        if nh3_level > 200:
            adjustments['duration'] = max(adjustments['duration'], 240)
        
        return adjustments
    
    def apply_adjustments(self, adjustments):
        """Apply calculated adjustments to simulation constants"""
        
        print(f"\n{'='*70}")
        print(f"  ADAPTIVE CONTROLLER - ADJUSTING TREATMENT PARAMETERS")
        print(f"{'='*70}")
        print(f"\nPatient Severity: {adjustments['severity'].upper()}")
        print(f"\nReal-world adjustments being made:")
        print(f"  1. Flow rate: 30 → {adjustments['Q_plasma']} mL/min")
        print(f"  2. Treatment duration: 60 → {adjustments['duration']} minutes")
        
        if adjustments['fresh_cartridge']:
            print(f"  3. ✅ Installing fresh hepatocyte cartridge")
            print(f"     (Increases metabolic capacity {adjustments['k1_multiplier']:.1f}×)")
        
        if adjustments['temperature_boost'] > 0:
            print(f"  4. Temperature: 37.0 → 37.5°C (optimized)")
            print(f"     (Slight metabolic boost)")
        
        print(f"\nThese are all REAL adjustments an operator can make!")
        print(f"{'='*70}\n")
        
        # Apply to constants
        const.PUMP_THRESHOLDS['Q_target'] = adjustments['Q_plasma']
        
        # Fresh cartridge = higher k1 (new, active hepatocytes)
        if adjustments['fresh_cartridge']:
            const.HEPATOCYTE_KINETICS['k1_NH3_base'] = 1.0 * adjustments['k1_multiplier']
            const.HEPATOCYTE_KINETICS['k1_lido_base'] = 0.85 * adjustments['k1_multiplier']
        
        # Temperature boost (1% increase per 0.1°C)
        if adjustments['temperature_boost'] > 0:
            temp_factor = 1.0 + (adjustments['temperature_boost'] * 0.01)
            const.HEPATOCYTE_KINETICS['k1_NH3_base'] *= temp_factor
            const.HEPATOCYTE_KINETICS['k1_lido_base'] *= temp_factor
        
        return adjustments['duration']


def run_adaptive_treatment(nh3_initial, lido_initial):
    """
    Run treatment with adaptive controller
    
    Args:
        nh3_initial: Initial NH3 concentration (µmol/L)
        lido_initial: Initial lidocaine concentration (µmol/L)
    """
    
    print("="*70)
    print("  ADAPTIVE BAL TREATMENT SYSTEM")
    print("="*70)
    print()
    print("Initial Patient Status:")
    print(f"  NH3:       {nh3_initial} µmol/L")
    print(f"  Lidocaine: {lido_initial} µmol/L")
    
    # Create controller
    controller = AdaptiveBALController()
    
    # Assess severity
    severity = controller.assess_severity(nh3_initial, lido_initial)
    print(f"\nSeverity Assessment: {severity.upper()}")
    
    # Calculate adjustments
    adjustments = controller.calculate_adjustments(severity, nh3_initial, lido_initial)
    
    # Apply adjustments
    duration = controller.apply_adjustments(adjustments)
    
    # Set initial conditions
    const.SEPARATOR_INPUTS['C_NH3_in_nominal'] = nh3_initial
    const.SEPARATOR_INPUTS['C_lido_in_nominal'] = lido_initial
    
    # Run simulation
    print(f"Running simulation with adjusted parameters...")
    print()
    
    sim = SimulationEngine(dt=1.0)
    sim.run(duration=duration)
    
    # Check results
    df = pd.read_csv('output/demo_results.csv')
    
    final_nh3 = df['bio_C_NH3'].iloc[-1]
    final_lido = df['bio_C_lido'].iloc[-1]
    
    nh3_clearance = (nh3_initial - final_nh3) / nh3_initial * 100 if nh3_initial > 0 else 0
    lido_clearance = (lido_initial - final_lido) / lido_initial * 100 if lido_initial > 0 else 0
    
    print("="*70)
    print("  TREATMENT RESULTS")
    print("="*70)
    print()
    print(f"Duration: {duration} minutes (auto-adjusted)")
    print()
    print(f"NH3:  {nh3_initial} → {final_nh3:.1f} µmol/L ({nh3_clearance:.1f}% clearance)")
    print(f"Lido: {lido_initial} → {final_lido:.1f} µmol/L ({lido_clearance:.1f}% clearance)")
    print()
    
    # Safety assessment
    nh3_safe = final_nh3 < 50
    lido_safe = final_lido < 15
    
    print("Safety Status:")
    print(f"  NH3:  {'✅ SAFE' if nh3_safe else '⚠️  STILL HIGH'} (target: <50 µmol/L)")
    print(f"  Lido: {'✅ SAFE' if lido_safe else '⚠️  STILL HIGH'} (target: <15 µmol/L)")
    print()
    
    if nh3_safe and lido_safe:
        print("🎉 TREATMENT SUCCESSFUL!")
        print("   Patient blood is safe to return")
    else:
        print("⚠️  Treatment may need further extension")
        print("   Controller would recommend continuing treatment")
    
    print()
    print("="*70)
    print("  ADJUSTMENTS MADE (All Real-World Controllable)")
    print("="*70)
    print()
    print(f"✓ Flow rate adjusted to {adjustments['Q_plasma']} mL/min")
    print(f"✓ Treatment time extended to {duration} minutes")
    if adjustments['fresh_cartridge']:
        print(f"✓ Fresh hepatocyte cartridge installed")
    if adjustments['temperature_boost'] > 0:
        print(f"✓ Temperature optimized")
    print()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  TESTING ADAPTIVE CONTROLLER WITH DIFFERENT SEVERITIES")
    print("="*70 + "\n")
    
    # Test cases
    test_cases = [
        ("Standard Case", 90, 21),
        ("Severe Case", 200, 35),
        ("Critical Case", 300, 45),
    ]
    
    for name, nh3, lido in test_cases:
        print(f"\n{'#'*70}")
        print(f"  TEST: {name}")
        print(f"{'#'*70}\n")
        
        run_adaptive_treatment(nh3, lido)
        
        print("\n" + "="*70 + "\n")
        input("Press Enter to continue to next test case...")
