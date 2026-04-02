"""
Module 6: Return Monitor

Final safety validation before returning blood to patient.
Monitors toxin levels, blood composition, and safety parameters.
"""

from typing import Dict, Any, List
from modules.base_module import BaseModule
from config.constants import (
    RETURN_MONITOR_STATES,
    RETURN_MONITOR_INPUTS,
    RETURN_MONITOR_THRESHOLDS
)


class ReturnMonitorModule(BaseModule):
    """
    Return Monitor Module - Final safety check before patient return

    Validates all critical parameters before allowing blood return:
    - Ammonia and lidocaine levels (toxicity check)
    - Temperature (physiological range)
    - Hematocrit (blood composition)
    - Air detection (embolism prevention)
    - Hemolysis (cell damage check)

    States:
        0 - MONITORING_TESTING: Active parameter monitoring
        1 - SAFE_TO_RETURN: All parameters safe
        2 - ELEVATED_AMMONIA_WARNING: Ammonia marginal
        3 - ELEVATED_LIDOCAINE_WARNING: Lidocaine marginal
        4 - CRITICAL_TOXICITY_DETECTED: Unsafe toxin levels
        5 - TEMPERATURE_ALARM: Temperature out of range
        6 - AIR_DETECTED: Air bubbles detected
        7 - HEMOLYSIS_DETECTED: Cell damage detected
        8 - ABNORMAL_HEMATOCRIT: Hematocrit out of range
        9 - UNSAFE_FOR_RETURN: Multiple failures
        10 - EMERGENCY_STOP_NO_RETURN: Critical failure, stop system
    """

    def __init__(self):
        """Initialize Return Monitor Module."""
        super().__init__("Return Monitor")

        # Initial state
        self.state = RETURN_MONITOR_STATES['MONITORING_TESTING']

        # Input parameters (from mixer)
        self.Q_blood = 0.0
        self.Hct = 0.0
        self.T_blood = 37.0

        # Measured concentrations
        self.C_NH3 = 90.0             # Should be reduced from inlet
        self.C_lido = 21.0            # Should be reduced from inlet
        self.C_urea = 5.0             # Should be increased

        # Safety monitoring
        self.air_volume = 0.0         # Detected air (mL)
        self.free_Hb = 5.0            # Free hemoglobin (hemolysis indicator)

        # Decision outputs
        self.return_approved = False   # Can blood be returned?
        self.treatment_success = False # Was treatment successful?

        # Violation tracking
        self.violations = []           # List of current violations
        self.consecutive_safe_checks = 0  # Safety streak counter

    def update(self, dt: float = 1.0, **inputs) -> Dict[str, Any]:
        """
        Update return monitor for one time step.

        Args:
            dt: Time step in minutes
            **inputs: Input parameters from mixer
                - Q_blood: Blood flow rate (mL/min)
                - Hct_out: Hematocrit
                - T_out: Temperature (°C)
                - C_NH3: Ammonia concentration (µmol/L)
                - C_lido: Lidocaine concentration (µmol/L)
                - C_urea: Urea concentration (mmol/L)
                - air_volume: Detected air (mL) - optional
                - free_Hb: Free hemoglobin (mg/dL) - optional

        Returns:
            Dict with monitoring results and safety decision
        """
        # Update timing
        self.time_in_state += dt
        self.simulation_time += dt

        # Update inputs
        self._update_inputs(**inputs)

        # Evaluate all safety parameters
        self._evaluate_safety()

        # Make return decision
        self._make_return_decision()

        # Update state machine
        self._check_state_transition()

        return self._get_outputs()

    def _update_inputs(self, **inputs):
        """Update input parameters from mixer."""
        self.Q_blood = inputs.get('Q_blood', 0.0)
        self.Hct = inputs.get('Hct_out', 0.32)
        self.T_blood = inputs.get('T_out', 37.0)

        # Concentrations
        self.C_NH3 = inputs.get('C_NH3', 90.0)
        self.C_lido = inputs.get('C_lido', 21.0)
        self.C_urea = inputs.get('C_urea', 5.0)

        # Safety sensors
        self.air_volume = inputs.get('air_volume', 0.0)
        self.free_Hb = inputs.get('free_Hb', 5.0)

    def _evaluate_safety(self):
        """Evaluate all safety parameters and identify violations."""
        self.violations = []

        # Check ammonia level
        if self.C_NH3 >= RETURN_MONITOR_THRESHOLDS['C_NH3_critical']:
            self.violations.append('CRITICAL_AMMONIA')
        elif self.C_NH3 >= RETURN_MONITOR_THRESHOLDS['C_NH3_warning']:
            self.violations.append('WARNING_AMMONIA')

        # Check lidocaine level
        if self.C_lido >= RETURN_MONITOR_THRESHOLDS['C_lido_critical']:
            self.violations.append('CRITICAL_LIDOCAINE')
        elif self.C_lido >= RETURN_MONITOR_THRESHOLDS['C_lido_warning']:
            self.violations.append('WARNING_LIDOCAINE')

        # Check temperature
        if (self.T_blood < RETURN_MONITOR_THRESHOLDS['T_critical_low'] or
            self.T_blood > RETURN_MONITOR_THRESHOLDS['T_critical_high']):
            self.violations.append('CRITICAL_TEMPERATURE')
        elif (self.T_blood < RETURN_MONITOR_THRESHOLDS['T_min'] or
              self.T_blood > RETURN_MONITOR_THRESHOLDS['T_max']):
            self.violations.append('WARNING_TEMPERATURE')

        # Check hematocrit
        if (self.Hct < RETURN_MONITOR_THRESHOLDS['Hct_critical_low'] or
            self.Hct > RETURN_MONITOR_THRESHOLDS['Hct_critical_high']):
            self.violations.append('CRITICAL_HEMATOCRIT')
        elif (self.Hct < RETURN_MONITOR_THRESHOLDS['Hct_min'] or
              self.Hct > RETURN_MONITOR_THRESHOLDS['Hct_max']):
            self.violations.append('WARNING_HEMATOCRIT')

        # Check for air
        if self.air_volume >= RETURN_MONITOR_THRESHOLDS['air_volume_critical']:
            self.violations.append('CRITICAL_AIR')
        elif self.air_volume >= RETURN_MONITOR_THRESHOLDS['air_volume_max']:
            self.violations.append('WARNING_AIR')

        # Check for hemolysis
        if self.free_Hb >= RETURN_MONITOR_THRESHOLDS['free_Hb_critical']:
            self.violations.append('CRITICAL_HEMOLYSIS')
        elif self.free_Hb >= RETURN_MONITOR_THRESHOLDS['free_Hb_warning']:
            self.violations.append('WARNING_HEMOLYSIS')

    def _make_return_decision(self):
        """Decide if blood is safe to return to patient."""
        # Check for any CRITICAL violations
        critical_violations = [v for v in self.violations if 'CRITICAL' in v]

        if len(critical_violations) > 0:
            self.return_approved = False
            self.consecutive_safe_checks = 0
        else:
            # No critical violations - check warnings
            warning_violations = [v for v in self.violations if 'WARNING' in v]

            if len(warning_violations) == 0:
                # All parameters normal
                self.consecutive_safe_checks += 1
                # Require multiple consecutive safe checks before approval
                if self.consecutive_safe_checks >= 3:
                    self.return_approved = True
            else:
                # Has warnings but no criticals - marginal case
                self.return_approved = False
                self.consecutive_safe_checks = 0

        # Evaluate treatment success
        self._evaluate_treatment_success()

    def _evaluate_treatment_success(self):
        """Determine if treatment was successful."""
        ammonia_ok = self.C_NH3 <= RETURN_MONITOR_THRESHOLDS['treatment_success_NH3']
        lidocaine_ok = self.C_lido <= RETURN_MONITOR_THRESHOLDS['treatment_success_lido']
        composition_ok = (RETURN_MONITOR_THRESHOLDS['Hct_min'] <= self.Hct <=
                         RETURN_MONITOR_THRESHOLDS['Hct_max'])

        self.treatment_success = ammonia_ok and lidocaine_ok and composition_ok

    def _check_state_transition(self):
        """Update state based on violations and safety status."""
        # If EMERGENCY_STOP, stay there
        if self.state == RETURN_MONITOR_STATES['EMERGENCY_STOP_NO_RETURN']:
            return

        # Check for critical failures
        if 'CRITICAL_AIR' in self.violations:
            self.state = RETURN_MONITOR_STATES['AIR_DETECTED']
            self.time_in_state = 0.0
        elif 'CRITICAL_AMMONIA' in self.violations or 'CRITICAL_LIDOCAINE' in self.violations:
            self.state = RETURN_MONITOR_STATES['CRITICAL_TOXICITY_DETECTED']
            self.time_in_state = 0.0
        elif 'CRITICAL_TEMPERATURE' in self.violations:
            self.state = RETURN_MONITOR_STATES['TEMPERATURE_ALARM']
            self.time_in_state = 0.0
        elif 'CRITICAL_HEMOLYSIS' in self.violations:
            self.state = RETURN_MONITOR_STATES['HEMOLYSIS_DETECTED']
            self.time_in_state = 0.0
        elif 'CRITICAL_HEMATOCRIT' in self.violations:
            self.state = RETURN_MONITOR_STATES['ABNORMAL_HEMATOCRIT']
            self.time_in_state = 0.0

        # If multiple critical issues, escalate to UNSAFE or EMERGENCY_STOP
        elif len([v for v in self.violations if 'CRITICAL' in v]) >= 2:
            if self.time_in_state > 5.0:  # Sustained for 5+ minutes
                self.state = RETURN_MONITOR_STATES['EMERGENCY_STOP_NO_RETURN']
                self.time_in_state = 0.0
            else:
                self.state = RETURN_MONITOR_STATES['UNSAFE_FOR_RETURN']
                self.time_in_state = 0.0

        # Check for warnings
        elif 'WARNING_AMMONIA' in self.violations:
            self.state = RETURN_MONITOR_STATES['ELEVATED_AMMONIA_WARNING']
            self.time_in_state = 0.0
        elif 'WARNING_LIDOCAINE' in self.violations:
            self.state = RETURN_MONITOR_STATES['ELEVATED_LIDOCAINE_WARNING']
            self.time_in_state = 0.0

        # If no violations, safe to return
        elif len(self.violations) == 0 and self.return_approved:
            self.state = RETURN_MONITOR_STATES['SAFE_TO_RETURN']
            # Don't reset time_in_state here to allow tracking how long we've been safe

        # Otherwise, monitoring
        elif len(self.violations) == 0:
            self.state = RETURN_MONITOR_STATES['MONITORING_TESTING']
            # Don't reset time_in_state

    def _get_outputs(self) -> Dict[str, Any]:
        """Package outputs for logging and display."""
        return {
            # Flow through
            'Q_blood': self.Q_blood,
            'Hct': self.Hct,
            'T_blood': self.T_blood,

            # Monitored concentrations
            'C_NH3': self.C_NH3,
            'C_lido': self.C_lido,
            'C_urea': self.C_urea,

            # Safety indicators
            'air_volume': self.air_volume,
            'free_Hb': self.free_Hb,

            # Decisions
            'return_approved': self.return_approved,
            'treatment_success': self.treatment_success,

            # Status
            'state': self.state,
            'state_name': self.get_state_name(),
            'violations': self.violations,
            'violation_count': len(self.violations),
            'alarm_code': self._get_alarm_code()
        }

    def _get_alarm_code(self) -> int:
        """Get alarm code based on current state and violations."""
        critical_violations = [v for v in self.violations if 'CRITICAL' in v]
        warning_violations = [v for v in self.violations if 'WARNING' in v]

        if self.state == RETURN_MONITOR_STATES['EMERGENCY_STOP_NO_RETURN']:
            return 3  # Emergency
        elif len(critical_violations) > 0:
            return 2  # Critical alarm
        elif len(warning_violations) > 0:
            return 1  # Warning
        else:
            return 0  # No alarm

    def get_state_name(self) -> str:
        """Return human-readable state name."""
        state_names = {
            0: 'MONITORING_TESTING',
            1: 'SAFE_TO_RETURN',
            2: 'ELEVATED_AMMONIA_WARNING',
            3: 'ELEVATED_LIDOCAINE_WARNING',
            4: 'CRITICAL_TOXICITY_DETECTED',
            5: 'TEMPERATURE_ALARM',
            6: 'AIR_DETECTED',
            7: 'HEMOLYSIS_DETECTED',
            8: 'ABNORMAL_HEMATOCRIT',
            9: 'UNSAFE_FOR_RETURN',
            10: 'EMERGENCY_STOP_NO_RETURN'
        }
        return state_names.get(self.state, 'UNKNOWN')
