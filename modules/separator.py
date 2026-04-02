"""
Module 1: Plasma Separator

Splits whole blood into plasma and cellular components using
hollow-fiber membrane filtration (Plasmaflo OP-08W design).
"""

from typing import Dict, Any
from modules.base_module import BaseModule
from config.constants import (
    SEPARATOR_STATES,
    SEPARATOR_INPUTS,
    SEPARATOR_THRESHOLDS
)


class SeparatorModule(BaseModule):
    """
    Plasma Separator Module

    Implements hollow-fiber membrane plasma separation with:
    - 6-state machine (startup, normal, degraded, fouled, clotted, failure)
    - Real-time separation efficiency tracking
    - Safety interlocks for TMP, filtration fraction, and hematocrit
    - State transition logic based on operational thresholds

    States:
        0 - STARTUP_PRIMING: Initial priming phase
        1 - NORMAL_OPERATION: Optimal separation performance
        2 - DEGRADED_PERFORMANCE: Reduced efficiency, still functional
        3 - MEMBRANE_FOULED: Significant fouling detected
        4 - MEMBRANE_CLOTTED: Clotting detected in membrane
        5 - MEMBRANE_FAILURE: Complete membrane failure
    """

    def __init__(self):
        """
        Initialize Plasma Separator Module.

        Sets initial state to STARTUP_PRIMING and initializes all
        input/output parameters to nominal/zero values.
        """
        super().__init__("Plasma Separator")

        # Initial state
        self.state = 0  # STARTUP_PRIMING

        # Input parameters (initialized to nominal values)
        self.Q_blood = SEPARATOR_INPUTS['Q_blood_nominal']
        self.Hct_in = SEPARATOR_INPUTS['Hct_in_nominal']
        self.T_in = SEPARATOR_INPUTS['T_in_nominal']
        self.P_blood_in = SEPARATOR_INPUTS['P_blood_in_nominal']
        self.C_NH3_in = SEPARATOR_INPUTS['C_NH3_in_nominal']
        self.C_lido_in = SEPARATOR_INPUTS['C_lido_in_nominal']
        self.C_urea_in = SEPARATOR_INPUTS['C_urea_in_nominal']

        # Output parameters (initialized to zero)
        self.Q_plasma = 0.0
        self.Q_cells = 0.0
        self.P_plasma = 0.0
        self.T_plasma = 0.0
        self.C_NH3_plasma = 0.0
        self.C_lido_plasma = 0.0
        self.C_urea_plasma = 0.0

        # Performance metrics
        self.eta_sep = 1.0  # Separation efficiency (perfect initially)
        self.TMP = 0.0      # Transmembrane pressure
        self.FF_actual = 0.0  # Actual filtration fraction
        self.Hct_post = 0.0   # Post-separation hematocrit

        # Alarm status
        self.alarm_code = 0  # 0=OK, 1=warning, 2=critical

        # State transition tracking
        self.degraded_condition_start = None  # Track when degraded conditions began
        self.Q_blood_baseline = self.Q_blood  # Baseline for clot detection

    def update(self, dt: float = 1.0, **inputs) -> Dict[str, Any]:
        """
        Advance separator simulation by dt minutes.

        Performs the following operations:
        1. Update time tracking
        2. Update input parameters from upstream
        3. Calculate output flows and concentrations
        4. Check safety interlocks
        5. Check state transition conditions
        6. Return all outputs

        Args:
            dt: Time step in minutes (default 1.0)
            **inputs: Optional input parameters to override defaults:
                - Q_blood: Blood flow rate (mL/min)
                - Hct_in: Input hematocrit (fraction)
                - T_in: Input temperature (°C)
                - P_blood_in: Input blood pressure (mmHg)
                - C_NH3_in: Input ammonia concentration (µmol/L)
                - C_lido_in: Input lidocaine concentration (µmol/L)
                - C_urea_in: Input urea concentration (mmol/L)

        Returns:
            Dict containing all separator outputs and state information
        """
        # Update time tracking
        self.time_in_state += dt
        self.simulation_time += dt

        # Update input parameters if provided
        self.Q_blood = inputs.get('Q_blood', self.Q_blood)
        self.Hct_in = inputs.get('Hct_in', self.Hct_in)
        self.T_in = inputs.get('T_in', self.T_in)
        self.P_blood_in = inputs.get('P_blood_in', self.P_blood_in)
        self.C_NH3_in = inputs.get('C_NH3_in', self.C_NH3_in)
        self.C_lido_in = inputs.get('C_lido_in', self.C_lido_in)
        self.C_urea_in = inputs.get('C_urea_in', self.C_urea_in)

        # Clamp inputs to acceptable ranges
        self.Q_blood = max(SEPARATOR_INPUTS['Q_blood_min'],
                          min(SEPARATOR_INPUTS['Q_blood_max'], self.Q_blood))
        self.Hct_in = max(SEPARATOR_INPUTS['Hct_in_min'],
                         min(SEPARATOR_INPUTS['Hct_in_max'], self.Hct_in))

        # Calculate outputs using equations from Section 7

        # Equation 7.1: Q_plasma = Q_blood × (1 - Hct_in) × eta_sep
        self.Q_plasma = self.Q_blood * (1 - self.Hct_in) * self.eta_sep

        # Equation 7.2: Q_cells = Q_blood - Q_plasma
        self.Q_cells = self.Q_blood - self.Q_plasma

        # Equation 7.3: FF_actual = Q_plasma / [Q_blood × (1 - Hct_in)]
        # Avoid division by zero
        denominator = self.Q_blood * (1 - self.Hct_in)
        if denominator > 0:
            self.FF_actual = self.Q_plasma / denominator
        else:
            self.FF_actual = 0.0

        # Equation 7.4: Hct_post = Hct_in / [1 - (Q_plasma / Q_blood)]
        # Avoid division by zero
        if self.Q_blood > 0:
            denominator = 1 - (self.Q_plasma / self.Q_blood)
            if denominator > 0:
                self.Hct_post = self.Hct_in / denominator
            else:
                self.Hct_post = 0.99  # Maximum realistic value
        else:
            self.Hct_post = self.Hct_in

        # Equation 7.5: TMP = P_blood_in - P_plasma - P_oncotic
        # P_oncotic ≈ 25 mmHg (constant)
        self.P_plasma = 50  # Nominal plasma side pressure (mmHg)
        self.TMP = self.P_blood_in - self.P_plasma - SEPARATOR_THRESHOLDS['P_oncotic']

        # Equation 7.6: Concentrations pass through unchanged
        self.C_NH3_plasma = self.C_NH3_in
        self.C_lido_plasma = self.C_lido_in
        self.C_urea_plasma = self.C_urea_in

        # Temperature passes through unchanged
        self.T_plasma = self.T_in

        # Check safety interlocks
        self._check_safety()

        # Check state transition conditions
        self._check_state_transition()

        # Return all outputs
        return self._get_outputs()

    def _check_safety(self):
        """
        Check safety interlocks and adjust alarm codes.

        Implements safety logic from Section 9:
        - TMP > 100 mmHg → Immediate MEMBRANE_FAILURE
        - FF_actual > 0.35 → Warning, reduce plasma flow
        - Hct_post > 0.55 → Warning, reduce plasma flow

        Sets alarm_code:
        - 0: OK (normal operation)
        - 1: Warning (degraded but safe)
        - 2: Critical (immediate attention required)
        """
        # Reset alarm code
        self.alarm_code = 0

        # Critical: TMP > 100 mmHg → immediate failure
        if self.TMP > SEPARATOR_THRESHOLDS['TMP_failure']:
            self.state = 5  # MEMBRANE_FAILURE
            self.alarm_code = 2
            self.time_in_state = 0.0
            return

        # Warning: FF_actual > 0.35 → reduce plasma flow
        if self.FF_actual > SEPARATOR_THRESHOLDS['FF_critical']:
            self.alarm_code = max(self.alarm_code, 1)
            # Reduce separation efficiency to lower plasma flow
            self.eta_sep = max(0.8, self.eta_sep - 0.05)

        # Warning: Hct_post > 0.55 → reduce plasma flow
        if self.Hct_post > SEPARATOR_THRESHOLDS['Hct_post_max']:
            self.alarm_code = max(self.alarm_code, 1)
            # Reduce separation efficiency to lower plasma flow
            self.eta_sep = max(0.8, self.eta_sep - 0.05)

        # Set critical alarm for membrane failure state
        if self.state == 5:
            self.alarm_code = 2
        # Set warning alarm for fouled/clotted states
        elif self.state in [3, 4]:
            self.alarm_code = max(self.alarm_code, 1)

    def _check_state_transition(self):
        """
        Check and execute state transitions based on operating conditions.

        Implements state machine logic from Section 6.2:
        - STARTUP_PRIMING → NORMAL_OPERATION
        - NORMAL_OPERATION ↔ DEGRADED_PERFORMANCE
        - DEGRADED_PERFORMANCE → MEMBRANE_FOULED
        - MEMBRANE_FOULED → MEMBRANE_CLOTTED
        - Any State → MEMBRANE_FAILURE

        State transitions may require sustained conditions (tracked over time).
        """
        old_state = self.state

        # First, adjust efficiency based on current state (before transition checks)
        # This allows proper state transition logic based on updated efficiency
        if self.state == 0:
            # Startup: efficiency is reduced
            self.eta_sep = 0.8
        elif self.state == 1:
            # Normal operation: maintain optimal efficiency (unless degraded by external factors)
            # Only adjust if efficiency has dropped below optimal
            if self.eta_sep < 0.96:
                self.eta_sep = 0.97  # Immediately restore to optimal
        elif self.state == 2:
            # Degraded: reduced but functional (fixed value)
            self.eta_sep = 0.90
        elif self.state == 3:
            # Fouled: significantly reduced
            self.eta_sep = 0.75
        elif self.state == 4:
            # Clotted: severely reduced
            self.eta_sep = 0.50
        elif self.state == 5:
            # Complete failure
            self.eta_sep = 0.0

        # State 0: STARTUP_PRIMING → NORMAL_OPERATION
        if self.state == 0:
            # Transition when: time_in_state ≥ 2 min AND TMP < 40 mmHg
            if (self.time_in_state >= SEPARATOR_THRESHOLDS['startup_duration'] and
                self.TMP < SEPARATOR_THRESHOLDS['TMP_normal_max']):
                self.state = 1  # NORMAL_OPERATION
                self.time_in_state = 0.0

        # State 1: NORMAL_OPERATION → DEGRADED_PERFORMANCE
        elif self.state == 1:
            # Check for degraded conditions
            degraded = (self.eta_sep < SEPARATOR_THRESHOLDS['eta_sep_normal'] or
                       self.TMP > SEPARATOR_THRESHOLDS['TMP_warning'])

            if degraded:
                # Start tracking degraded condition if not already
                if self.degraded_condition_start is None:
                    self.degraded_condition_start = self.simulation_time
                # Transition if sustained > 5 minutes
                elif (self.simulation_time - self.degraded_condition_start >=
                      SEPARATOR_THRESHOLDS['degraded_duration']):
                    self.state = 2  # DEGRADED_PERFORMANCE
                    self.time_in_state = 0.0
                    self.degraded_condition_start = None
            else:
                # Reset tracking if conditions improve
                self.degraded_condition_start = None

        # State 2: DEGRADED_PERFORMANCE transitions
        elif self.state == 2:
            # Check for recovery to NORMAL_OPERATION
            if (self.eta_sep >= SEPARATOR_THRESHOLDS['eta_sep_normal'] and
                self.TMP < SEPARATOR_THRESHOLDS['TMP_warning']):
                self.state = 1  # NORMAL_OPERATION
                self.time_in_state = 0.0
            # Check for progression to MEMBRANE_FOULED
            elif (self.eta_sep < SEPARATOR_THRESHOLDS['eta_sep_degraded'] or
                  self.TMP > SEPARATOR_THRESHOLDS['TMP_critical']):
                self.state = 3  # MEMBRANE_FOULED
                self.time_in_state = 0.0

        # State 3: MEMBRANE_FOULED → MEMBRANE_CLOTTED
        elif self.state == 3:
            # Check for flow drop or extreme TMP
            Q_blood_drop = (self.Q_blood_baseline - self.Q_blood) / self.Q_blood_baseline
            if (Q_blood_drop > SEPARATOR_THRESHOLDS['Q_blood_drop_threshold'] or
                self.TMP > SEPARATOR_THRESHOLDS['TMP_clotted']):
                self.state = 4  # MEMBRANE_CLOTTED
                self.time_in_state = 0.0

        # State 4: MEMBRANE_CLOTTED (terminal state, requires intervention)
        # No automatic transition out of this state

        # State 5: MEMBRANE_FAILURE (terminal state)
        # No automatic transition out of this state

    def _get_outputs(self) -> Dict[str, Any]:
        """
        Get all separator outputs and state information.

        Returns:
            Dict containing:
                - Q_plasma (mL/min): Plasma flow rate
                - Q_cells (mL/min): Cellular component flow rate
                - P_plasma (mmHg): Plasma side pressure
                - T_plasma (°C): Plasma temperature
                - C_NH3_plasma (µmol/L): Ammonia concentration in plasma
                - C_lido_plasma (µmol/L): Lidocaine concentration in plasma
                - C_urea_plasma (mmol/L): Urea concentration in plasma
                - state (int): Current state code (0-5)
                - state_name (str): Human-readable state name
                - TMP (mmHg): Transmembrane pressure
                - eta_sep (fraction): Separation efficiency
                - FF_actual (fraction): Actual filtration fraction
                - Hct_post (fraction): Post-separation hematocrit
                - alarm_code (int): Alarm status (0=OK, 1=warning, 2=critical)
        """
        return {
            # Flow rates
            'Q_plasma': self.Q_plasma,
            'Q_cells': self.Q_cells,

            # Pressures and temperature
            'P_plasma': self.P_plasma,
            'T_plasma': self.T_plasma,
            'TMP': self.TMP,

            # Concentrations
            'C_NH3_plasma': self.C_NH3_plasma,
            'C_lido_plasma': self.C_lido_plasma,
            'C_urea_plasma': self.C_urea_plasma,

            # State information
            'state': self.state,
            'state_name': SEPARATOR_STATES[self.state],

            # Performance metrics
            'eta_sep': self.eta_sep,
            'FF_actual': self.FF_actual,
            'Hct_post': self.Hct_post,

            # Alarm status
            'alarm_code': self.alarm_code,
        }

    def get_state_name(self) -> str:
        """
        Get human-readable state name.

        Returns:
            String representation of current state
        """
        return SEPARATOR_STATES.get(self.state, f'UNKNOWN_STATE_{self.state}')
