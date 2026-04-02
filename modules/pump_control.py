"""
Module 2: Pump Control System

Controls plasma flow and enforces safety limits.
Most complex module with 12 states for comprehensive monitoring.
"""

from typing import Dict, Any
from modules.base_module import BaseModule
from config.constants import (
    PUMP_STATES,
    PUMP_INPUTS,
    PUMP_THRESHOLDS
)


class PumpControlModule(BaseModule):
    """
    Pump Control Module - Drives plasma flow with safety monitoring

    Comprehensive safety system monitoring:
    - Flow rate control
    - Pressure limits (high/low)
    - Temperature monitoring
    - Air-in-line detection
    - Leak detection
    - Emergency stop capability

    States:
        0 - OFF: Pump not running
        1 - STARTUP_PRIMING: Ramping up flow
        2 - NORMAL_OPERATION: Running at target
        3 - LOW_FLOW_WARNING: Flow below target
        4 - HIGH_FLOW_WARNING: Flow above target
        5 - HIGH_PRESSURE_ALARM: Pressure too high (blockage)
        6 - LOW_PRESSURE_ALARM: Pressure too low (leak)
        7 - AIR_IN_LINE_DETECTED: Air bubble detected
        8 - LEAK_DETECTED: Leak sensor triggered
        9 - TEMPERATURE_ALARM: Temperature out of range
        10 - OPERATOR_PAUSE: Manual pause
        11 - EMERGENCY_STOP: Critical failure
    """

    def __init__(self):
        """Initialize Pump Control Module."""
        super().__init__("Plasma Pump and Control")

        # Initial state
        self.state = PUMP_STATES['OFF']

        # Input parameters
        self.Q_plasma_in = 0.0
        self.P_plasma_in = 50.0
        self.T_plasma = 37.0

        # Control parameters
        self.Q_target = PUMP_THRESHOLDS['Q_target']
        self.Q_current = 0.0            # Current flow rate
        self.pump_running = False

        # Sensor readings (simulated)
        self.P_out = 50.0               # Outlet pressure
        self.air_detected = 0.0         # Air volume (mL)
        self.leak_detected = False

        # Operator commands
        self.start_command = False
        self.stop_command = False
        self.pause_command = False
        self.emergency_stop_command = False

    def update(self, dt: float = 1.0, **inputs) -> Dict[str, Any]:
        """
        Update pump control for one time step.

        Args:
            dt: Time step in minutes
            **inputs: From separator and operator
                - Q_plasma: Inlet plasma flow (mL/min)
                - P_plasma: Inlet pressure (mmHg)
                - T_plasma: Temperature (°C)
                - start: Start command (boolean)
                - stop: Stop command (boolean)
                - pause: Pause command (boolean)
                - emergency_stop: Emergency stop (boolean)

        Returns:
            Dict with controlled flow and safety status
        """
        # Update simulation time
        self.simulation_time += dt

        # Update time in state first (so state transitions can see accumulated time)
        self.time_in_state += dt

        # Update inputs
        self._update_inputs(**inputs)

        # Check for operator commands
        self._check_operator_commands(**inputs)

        # Monitor all safety parameters (before state transition to detect issues)
        self._monitor_safety()

        # Update state machine
        old_state = self.state
        self._check_state_transition()

        # Reset time in state if we just transitioned
        if old_state != self.state:
            self.time_in_state = dt  # Just transitioned, count from dt

        # Update pump flow control (after state transition to reflect new state immediately)
        self._control_flow(dt)

        return self._get_outputs()

    def _update_inputs(self, **inputs):
        """Update input parameters from upstream module."""
        self.Q_plasma_in = inputs.get('Q_plasma', 0.0)
        self.P_plasma_in = inputs.get('P_plasma', 50.0)
        self.T_plasma = inputs.get('T_plasma', 37.0)

    def _control_flow(self, dt: float):
        """Control pump flow rate based on state."""
        if self.state == PUMP_STATES['OFF']:
            self.Q_current = 0.0
            self.pump_running = False

        elif self.state == PUMP_STATES['STARTUP_PRIMING']:
            # Ramp up flow gradually
            ramp_rate = PUMP_THRESHOLDS['ramp_rate']
            self.Q_current = min(self.Q_current + ramp_rate * dt, self.Q_target)
            self.pump_running = True

        elif self.state == PUMP_STATES['NORMAL_OPERATION']:
            # Maintain target flow
            self.Q_current = self.Q_target
            self.pump_running = True

        elif self.state in [PUMP_STATES['LOW_FLOW_WARNING'],
                             PUMP_STATES['HIGH_FLOW_WARNING']]:
            # Try to correct to target
            ramp_rate = PUMP_THRESHOLDS['ramp_rate']
            if self.Q_current < self.Q_target:
                self.Q_current = min(self.Q_current + ramp_rate * dt * 0.5, self.Q_target)
            elif self.Q_current > self.Q_target:
                self.Q_current = max(self.Q_current - ramp_rate * dt * 0.5, self.Q_target)
            self.pump_running = True

        elif self.state == PUMP_STATES['OPERATOR_PAUSE']:
            # Hold current flow
            self.pump_running = False

        elif self.state in [PUMP_STATES['EMERGENCY_STOP'],
                             PUMP_STATES['AIR_IN_LINE_DETECTED'],
                             PUMP_STATES['LEAK_DETECTED']]:
            # Immediate stop
            self.Q_current = 0.0
            self.pump_running = False

        # Calculate outlet pressure (simplified)
        if self.pump_running:
            self.P_out = self.P_plasma_in + 10  # Pump adds ~10 mmHg
        else:
            self.P_out = self.P_plasma_in

    def _monitor_safety(self):
        """Monitor all safety parameters."""
        # Simulate sensor readings based on flow
        # In real system, these would come from actual sensors

        # Only update simulated values if not manually set for testing
        # Pressure increases with flow resistance
        if self.Q_current > 0 and self.pump_running:
            # Simplified: higher flow = slightly higher pressure
            calculated_pressure = self.P_plasma_in + 10 + (self.Q_current - 30) * 0.5
            # Don't override if manually set to an alarm value
            if not (self.P_out < PUMP_THRESHOLDS['P_critical_low'] or
                    self.P_out > PUMP_THRESHOLDS['P_critical_high']):
                self.P_out = calculated_pressure
        elif not self.pump_running and self.P_out > self.P_plasma_in:
            self.P_out = self.P_plasma_in

        # Air detection (simplified - check if manually set, otherwise no air)
        if self.air_detected < PUMP_THRESHOLDS['air_volume_max']:
            self.air_detected = 0.0

        # Leak detection (based on pressure)
        if self.P_out < PUMP_THRESHOLDS['P_critical_low'] and self.pump_running:
            self.leak_detected = True
        else:
            self.leak_detected = False

    def _check_state_transition(self):
        """Complex state machine with safety priorities."""
        current = self.state

        # EMERGENCY conditions (highest priority)
        if self.emergency_stop_command:
            if self.state != PUMP_STATES['EMERGENCY_STOP']:
                self.state = PUMP_STATES['EMERGENCY_STOP']
            return

        if self.air_detected >= PUMP_THRESHOLDS['air_volume_critical']:
            if self.state != PUMP_STATES['AIR_IN_LINE_DETECTED']:
                self.state = PUMP_STATES['AIR_IN_LINE_DETECTED']
            return

        if self.leak_detected:
            if self.state != PUMP_STATES['LEAK_DETECTED']:
                self.state = PUMP_STATES['LEAK_DETECTED']
            return

        # ALARM conditions
        if self.P_out >= PUMP_THRESHOLDS['P_critical_high']:
            if self.state != PUMP_STATES['HIGH_PRESSURE_ALARM']:
                self.state = PUMP_STATES['HIGH_PRESSURE_ALARM']
            return

        if self.P_out <= PUMP_THRESHOLDS['P_critical_low'] and self.pump_running:
            if self.state != PUMP_STATES['LOW_PRESSURE_ALARM']:
                self.state = PUMP_STATES['LOW_PRESSURE_ALARM']
            return

        if (self.T_plasma < PUMP_THRESHOLDS['T_critical_low'] or
            self.T_plasma > PUMP_THRESHOLDS['T_critical_high']):
            if self.state != PUMP_STATES['TEMPERATURE_ALARM']:
                self.state = PUMP_STATES['TEMPERATURE_ALARM']
            return

        # OPERATOR commands
        if self.pause_command and current not in [PUMP_STATES['OFF'], PUMP_STATES['EMERGENCY_STOP']]:
            if self.state != PUMP_STATES['OPERATOR_PAUSE']:
                self.state = PUMP_STATES['OPERATOR_PAUSE']
            return

        if self.stop_command:
            if self.state != PUMP_STATES['OFF']:
                self.state = PUMP_STATES['OFF']
            return

        # NORMAL transitions
        if current == PUMP_STATES['OFF']:
            if self.start_command:
                self.state = PUMP_STATES['STARTUP_PRIMING']

        elif current == PUMP_STATES['STARTUP_PRIMING']:
            # Transition after priming duration, flow will continue ramping in NORMAL_OPERATION
            if self.time_in_state >= PUMP_THRESHOLDS['priming_duration']:
                self.state = PUMP_STATES['NORMAL_OPERATION']

        elif current == PUMP_STATES['NORMAL_OPERATION']:
            # Check for flow warnings
            if self.Q_current < PUMP_THRESHOLDS['Q_warning_low']:
                self.state = PUMP_STATES['LOW_FLOW_WARNING']
            elif self.Q_current > PUMP_THRESHOLDS['Q_warning_high']:
                self.state = PUMP_STATES['HIGH_FLOW_WARNING']

        elif current == PUMP_STATES['LOW_FLOW_WARNING']:
            if self._is_flow_normal():
                self.state = PUMP_STATES['NORMAL_OPERATION']
            elif self.Q_current < PUMP_THRESHOLDS['Q_critical_low']:
                self.state = PUMP_STATES['LOW_PRESSURE_ALARM']

        elif current == PUMP_STATES['HIGH_FLOW_WARNING']:
            if self._is_flow_normal():
                self.state = PUMP_STATES['NORMAL_OPERATION']
            elif self.Q_current > PUMP_THRESHOLDS['Q_critical_high']:
                self.state = PUMP_STATES['HIGH_PRESSURE_ALARM']

        elif current == PUMP_STATES['OPERATOR_PAUSE']:
            if self.start_command and not self.pause_command:
                self.state = PUMP_STATES['NORMAL_OPERATION']

    def _is_flow_normal(self) -> bool:
        """Check if flow is within normal range."""
        return (PUMP_THRESHOLDS['Q_target'] - PUMP_THRESHOLDS['Q_tolerance'] <=
                self.Q_current <=
                PUMP_THRESHOLDS['Q_target'] + PUMP_THRESHOLDS['Q_tolerance'])

    def _check_operator_commands(self, **inputs):
        """Process operator commands."""
        self.start_command = inputs.get('start', False)
        self.stop_command = inputs.get('stop', False)
        self.pause_command = inputs.get('pause', False)
        self.emergency_stop_command = inputs.get('emergency_stop', False)

    def _get_outputs(self) -> Dict[str, Any]:
        """Package outputs."""
        return {
            # Controlled flow
            'Q_plasma': self.Q_current,
            'P_plasma': self.P_out,
            'T_plasma': self.T_plasma,

            # Status
            'pump_running': self.pump_running,
            'state': self.state,
            'state_name': self.get_state_name(),

            # Safety monitoring
            'air_detected': self.air_detected,
            'leak_detected': self.leak_detected,

            # Alarm
            'alarm_code': self._get_alarm_code()
        }

    def _get_alarm_code(self) -> int:
        """Return alarm code based on state."""
        alarm_states = [
            PUMP_STATES['HIGH_PRESSURE_ALARM'],
            PUMP_STATES['LOW_PRESSURE_ALARM'],
            PUMP_STATES['AIR_IN_LINE_DETECTED'],
            PUMP_STATES['LEAK_DETECTED'],
            PUMP_STATES['TEMPERATURE_ALARM'],
            PUMP_STATES['EMERGENCY_STOP']
        ]
        return 1 if self.state in alarm_states else 0

    def get_state_name(self) -> str:
        """Return human-readable state name."""
        state_names = {
            0: 'OFF',
            1: 'STARTUP_PRIMING',
            2: 'NORMAL_OPERATION',
            3: 'LOW_FLOW_WARNING',
            4: 'HIGH_FLOW_WARNING',
            5: 'HIGH_PRESSURE_ALARM',
            6: 'LOW_PRESSURE_ALARM',
            7: 'AIR_IN_LINE_DETECTED',
            8: 'LEAK_DETECTED',
            9: 'TEMPERATURE_ALARM',
            10: 'OPERATOR_PAUSE',
            11: 'EMERGENCY_STOP'
        }
        return state_names.get(self.state, 'UNKNOWN')
