"""
Module 5: Mixer

Recombines treated plasma with cellular components before return to patient.
"""

from typing import Dict, Any
from modules.base_module import BaseModule
from config.constants import (
    MIXER_STATES,
    MIXER_INPUTS,
    MIXER_THRESHOLDS,
    MIXER_OUTPUTS
)


class MixerModule(BaseModule):
    """
    Mixer Module - Recombines treated plasma with blood cells

    Combines two input streams:
    1. Treated plasma from bioreactor (ammonia reduced, toxins removed)
    2. Cellular components from separator (RBCs, WBCs, platelets)

    States:
        0 - IDLE_STANDBY: Waiting for both input streams
        1 - STARTUP_PRIMING: Flows establishing, chamber filling
        2 - NORMAL_MIXING: Proper mixing, correct ratios
        3 - IMBALANCED_MIXING: Flow ratio incorrect
        4 - INCOMPLETE_MIXING: Stratification, poor mixing
        5 - SINGLE_STREAM_FAILURE: Only one input flowing
        6 - HEMOLYSIS_DETECTED: Excessive shear damage
        7 - CLOTTING_BLOCKAGE: Clot formation
        8 - AIR_ENTRAINMENT: Air bubbles detected
        9 - MIXER_FAILURE: Complete failure
    """

    def __init__(self):
        """Initialize Mixer Module."""
        super().__init__("Mixer")

        # Initial state
        self.state = MIXER_STATES['IDLE_STANDBY']

        # Input parameters (from upstream modules)
        self.Q_plasma = 0.0           # From bioreactor
        self.Q_cells = 0.0            # From separator
        self.P_plasma = 0.0           # Plasma pressure
        self.P_cells = 0.0            # Cells pressure
        self.T_plasma = 37.0          # Temperature
        self.T_cells = 37.0

        # Concentrations (from treated plasma)
        self.C_NH3 = 0.0              # Should be reduced
        self.C_lido = 0.0             # Should be reduced
        self.C_urea = 0.0             # Should be increased

        # Cellular stream hematocrit (concentrated)
        self.Hct_cells = 0.40

        # Internal state tracking
        self.mixing_efficiency = 1.0   # 0.0-1.0
        self.shear_rate = 0.0         # Simplified shear calculation
        self.air_volume = 0.0         # Detected air volume

        # Output parameters (calculated)
        self.Q_blood_out = 0.0        # Total output flow
        self.Hct_out = 0.0            # Output hematocrit
        self.P_out = 0.0              # Output pressure
        self.flow_ratio = 0.0         # Actual plasma fraction
        self.mixing_quality = 1.0     # 0.0-1.0 quality metric

    def update(self, dt: float = 1.0, **inputs) -> Dict[str, Any]:
        """
        Update mixer module for one time step.

        Args:
            dt: Time step in minutes
            **inputs: Input parameters from upstream modules
                - Q_plasma: Treated plasma flow rate (mL/min)
                - Q_cells: Cellular stream flow rate (mL/min)
                - P_plasma: Plasma pressure (mmHg)
                - P_cells: Cells pressure (mmHg)
                - T_plasma: Plasma temperature (°C)
                - C_NH3: Ammonia concentration (µmol/L)
                - C_lido: Lidocaine concentration (µmol/L)
                - C_urea: Urea concentration (mmol/L)
                - Hct_cells: Hematocrit of cellular stream

        Returns:
            Dict with all mixer outputs
        """
        # Update timing
        self.time_in_state += dt
        self.simulation_time += dt

        # Update inputs from upstream modules
        self._update_inputs(**inputs)

        # Calculate mixing behavior
        self._calculate_mixing()

        # Check for problems
        self._check_safety()

        # Update state machine
        self._check_state_transition()

        return self._get_outputs()

    def _update_inputs(self, **inputs):
        """Update input parameters from upstream modules."""
        self.Q_plasma = inputs.get('Q_plasma', 0.0)
        self.Q_cells = inputs.get('Q_cells', 0.0)
        self.P_plasma = inputs.get('P_plasma', 80.0)
        self.P_cells = inputs.get('P_cells', 90.0)
        self.T_plasma = inputs.get('T_plasma', 37.0)
        self.T_cells = inputs.get('T_cells', 37.0)

        # Concentrations from treated plasma
        self.C_NH3 = inputs.get('C_NH3', 90.0)
        self.C_lido = inputs.get('C_lido', 21.0)
        self.C_urea = inputs.get('C_urea', 5.0)

        # Cellular stream hematocrit (concentrated)
        self.Hct_cells = inputs.get('Hct_cells', 0.40)

    def _calculate_mixing(self):
        """Calculate mixing behavior and outputs."""
        # Total output flow (mass balance)
        self.Q_blood_out = self.Q_plasma + self.Q_cells

        # Calculate output hematocrit
        # Plasma has Hct=0, cells stream has elevated Hct
        if self.Q_blood_out > 0:
            self.Hct_out = (self.Q_cells * self.Hct_cells) / self.Q_blood_out
        else:
            self.Hct_out = 0.0

        # Flow ratio (should match FF from separator)
        if self.Q_blood_out > 0:
            self.flow_ratio = self.Q_plasma / self.Q_blood_out
        else:
            self.flow_ratio = 0.0

        # Output pressure (average minus pressure drop)
        P_avg = (self.P_plasma + self.P_cells) / 2.0
        P_drop = MIXER_THRESHOLDS['P_drop_normal']
        self.P_out = P_avg - P_drop

        # Simplified shear rate calculation
        # Higher flows = higher shear
        self.shear_rate = (self.Q_blood_out / 150.0) * 2000  # Simplified

        # Mixing efficiency decreases with imbalance
        flow_ratio_error = abs(self.flow_ratio - MIXER_THRESHOLDS['flow_ratio_target'])
        if flow_ratio_error < MIXER_THRESHOLDS['flow_ratio_tolerance']:
            self.mixing_efficiency = 0.98  # Excellent mixing
        elif flow_ratio_error < MIXER_THRESHOLDS['flow_ratio_critical']:
            self.mixing_efficiency = 0.88  # Acceptable but declining
        else:
            self.mixing_efficiency = 0.75  # Poor mixing

        # Set mixing quality (same as efficiency for now)
        self.mixing_quality = self.mixing_efficiency

    def _check_safety(self):
        """Check for critical conditions."""
        # Check for single stream failure
        if (self.Q_plasma == 0 and self.Q_cells > 0) or (self.Q_cells == 0 and self.Q_plasma > 0):
            if self.state not in [MIXER_STATES['IDLE_STANDBY'], MIXER_STATES['SINGLE_STREAM_FAILURE']]:
                # Only transition to failure if we're not already idle
                pass  # Will be handled in state transition

        # Check for hemolysis risk
        if self.shear_rate > MIXER_THRESHOLDS['shear_rate_max']:
            # High shear detected
            pass  # Will be handled in state transition

        # Check for clotting (pressure drop too high)
        if self.P_plasma > 0 and self.P_cells > 0:
            P_avg = (self.P_plasma + self.P_cells) / 2.0
            P_drop = P_avg - self.P_out
            if P_drop > MIXER_THRESHOLDS['P_drop_blockage']:
                # Possible blockage
                pass  # Will be handled in state transition

        # Temperature check
        T_avg = (self.T_plasma + self.T_cells) / 2.0
        if T_avg < MIXER_INPUTS['T_min'] or T_avg > MIXER_INPUTS['T_max']:
            # Temperature out of range
            pass  # Could add temperature alarm state if needed

    def _check_state_transition(self):
        """Check and update state based on current conditions."""

        current_state = self.state

        # IDLE → STARTUP_PRIMING
        if current_state == MIXER_STATES['IDLE_STANDBY']:
            if self.Q_plasma > 0 and self.Q_cells > 0:
                self.state = MIXER_STATES['STARTUP_PRIMING']
                self.time_in_state = 0.0

        # STARTUP_PRIMING → NORMAL_MIXING
        elif current_state == MIXER_STATES['STARTUP_PRIMING']:
            if self.time_in_state >= MIXER_THRESHOLDS['priming_duration']:
                if self._is_mixing_normal():
                    self.state = MIXER_STATES['NORMAL_MIXING']
                    self.time_in_state = 0.0

        # NORMAL_MIXING → other states
        elif current_state == MIXER_STATES['NORMAL_MIXING']:
            # Check for problems
            if self.Q_plasma == 0 or self.Q_cells == 0:
                self.state = MIXER_STATES['SINGLE_STREAM_FAILURE']
                self.time_in_state = 0.0
            elif self.shear_rate > MIXER_THRESHOLDS['shear_rate_max']:
                self.state = MIXER_STATES['HEMOLYSIS_DETECTED']
                self.time_in_state = 0.0
            elif abs(self.flow_ratio - MIXER_THRESHOLDS['flow_ratio_target']) > MIXER_THRESHOLDS['flow_ratio_critical']:
                self.state = MIXER_STATES['IMBALANCED_MIXING']
                self.time_in_state = 0.0
            elif self.mixing_efficiency < MIXER_THRESHOLDS['mixing_efficiency_poor']:
                self.state = MIXER_STATES['INCOMPLETE_MIXING']
                self.time_in_state = 0.0

        # Recovery transitions
        elif current_state == MIXER_STATES['IMBALANCED_MIXING']:
            if self.Q_plasma == 0 or self.Q_cells == 0:
                self.state = MIXER_STATES['SINGLE_STREAM_FAILURE']
                self.time_in_state = 0.0
            elif self._is_mixing_normal():
                self.state = MIXER_STATES['NORMAL_MIXING']
                self.time_in_state = 0.0

        elif current_state == MIXER_STATES['INCOMPLETE_MIXING']:
            if self.Q_plasma == 0 or self.Q_cells == 0:
                self.state = MIXER_STATES['SINGLE_STREAM_FAILURE']
                self.time_in_state = 0.0
            elif self._is_mixing_normal():
                self.state = MIXER_STATES['NORMAL_MIXING']
                self.time_in_state = 0.0

        # SINGLE_STREAM_FAILURE → recovery
        elif current_state == MIXER_STATES['SINGLE_STREAM_FAILURE']:
            if self.Q_plasma == 0 and self.Q_cells == 0:
                self.state = MIXER_STATES['IDLE_STANDBY']
                self.time_in_state = 0.0
            elif self.Q_plasma > 0 and self.Q_cells > 0:
                # Both streams restored, go to startup
                self.state = MIXER_STATES['STARTUP_PRIMING']
                self.time_in_state = 0.0

    def _is_mixing_normal(self) -> bool:
        """Check if mixing conditions are normal."""
        flow_ratio_ok = abs(self.flow_ratio - MIXER_THRESHOLDS['flow_ratio_target']) < MIXER_THRESHOLDS['flow_ratio_tolerance']
        hct_ok = MIXER_THRESHOLDS['Hct_min'] <= self.Hct_out <= MIXER_THRESHOLDS['Hct_max']
        pressure_ok = MIXER_THRESHOLDS['P_output_min'] <= self.P_out <= MIXER_THRESHOLDS['P_output_max']
        efficiency_ok = self.mixing_efficiency >= MIXER_THRESHOLDS['mixing_efficiency_normal']

        return flow_ratio_ok and hct_ok and pressure_ok and efficiency_ok

    def _get_outputs(self) -> Dict[str, Any]:
        """Package outputs for downstream modules."""
        return {
            # Flow outputs
            'Q_blood': self.Q_blood_out,
            'Hct_out': self.Hct_out,
            'P_out': self.P_out,
            'T_out': (self.T_plasma + self.T_cells) / 2.0,

            # Concentrations (passed through from plasma)
            'C_NH3': self.C_NH3,
            'C_lido': self.C_lido,
            'C_urea': self.C_urea,

            # Status
            'state': self.state,
            'state_name': self.get_state_name(),
            'mixing_efficiency': self.mixing_efficiency,
            'flow_ratio': self.flow_ratio,
            'shear_rate': self.shear_rate,

            # Alarms
            'alarm_code': self._get_alarm_code()
        }

    def _get_alarm_code(self) -> int:
        """Get alarm code based on current state."""
        if self.state in [MIXER_STATES['IDLE_STANDBY'], MIXER_STATES['STARTUP_PRIMING'], MIXER_STATES['NORMAL_MIXING']]:
            return 0  # No alarm
        elif self.state == MIXER_STATES['IMBALANCED_MIXING']:
            return 1  # Warning
        elif self.state == MIXER_STATES['INCOMPLETE_MIXING']:
            return 1  # Warning
        elif self.state in [MIXER_STATES['SINGLE_STREAM_FAILURE'], MIXER_STATES['HEMOLYSIS_DETECTED'],
                           MIXER_STATES['CLOTTING_BLOCKAGE'], MIXER_STATES['AIR_ENTRAINMENT']]:
            return 2  # Critical
        elif self.state == MIXER_STATES['MIXER_FAILURE']:
            return 3  # Failure
        else:
            return 0

    def get_state_name(self) -> str:
        """Return human-readable state name."""
        state_names = {
            0: 'IDLE_STANDBY',
            1: 'STARTUP_PRIMING',
            2: 'NORMAL_MIXING',
            3: 'IMBALANCED_MIXING',
            4: 'INCOMPLETE_MIXING',
            5: 'SINGLE_STREAM_FAILURE',
            6: 'HEMOLYSIS_DETECTED',
            7: 'CLOTTING_BLOCKAGE',
            8: 'AIR_ENTRAINMENT',
            9: 'MIXER_FAILURE'
        }
        return state_names.get(self.state, 'UNKNOWN')
