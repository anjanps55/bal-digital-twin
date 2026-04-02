"""
Unit tests for Module 2: Pump Control System

Tests all 12 states and safety monitoring functionality.
"""

import pytest
from modules.pump_control import PumpControlModule
from config.constants import PUMP_STATES, PUMP_THRESHOLDS


class TestPumpControlInitialization:
    """Test module initialization."""

    def test_init(self):
        """Test pump control module initializes correctly."""
        pump = PumpControlModule()

        assert pump.name == "Plasma Pump and Control"
        assert pump.state == PUMP_STATES['OFF']
        assert pump.Q_current == 0.0
        assert pump.pump_running is False
        assert pump.time_in_state == 0.0
        assert pump.simulation_time == 0.0


class TestPumpStartup:
    """Test pump startup and priming sequence."""

    def test_startup_from_off(self):
        """Test pump starts up when start command is issued."""
        pump = PumpControlModule()

        # Issue start command
        outputs = pump.update(dt=1.0, start=True)

        assert pump.state == PUMP_STATES['STARTUP_PRIMING']
        assert pump.pump_running is True
        assert pump.Q_current > 0.0

    def test_priming_ramp_up(self):
        """Test flow ramps up during priming."""
        pump = PumpControlModule()
        pump.update(dt=1.0, start=True)

        initial_flow = pump.Q_current

        # Continue priming
        pump.update(dt=0.5)

        assert pump.Q_current > initial_flow
        assert pump.state == PUMP_STATES['STARTUP_PRIMING']

    def test_transition_to_normal_operation(self):
        """Test transition to normal operation after priming."""
        pump = PumpControlModule()

        # Start pump
        pump.update(dt=1.0, start=True)

        # Run through priming duration
        pump.update(dt=2.5)

        assert pump.state == PUMP_STATES['NORMAL_OPERATION']
        assert pump.Q_current == PUMP_THRESHOLDS['Q_target']


class TestNormalOperation:
    """Test normal pump operation."""

    def test_maintains_target_flow(self):
        """Test pump maintains target flow in normal operation."""
        pump = PumpControlModule()

        # Start and prime
        pump.update(dt=1.0, start=True)
        pump.update(dt=2.5)

        assert pump.state == PUMP_STATES['NORMAL_OPERATION']
        assert pump.Q_current == PUMP_THRESHOLDS['Q_target']

    def test_outlet_pressure_calculation(self):
        """Test outlet pressure is calculated correctly."""
        pump = PumpControlModule()

        inlet_pressure = 50.0
        pump.update(dt=1.0, start=True, P_plasma=inlet_pressure)
        pump.update(dt=2.5)

        # Pump should add pressure
        assert pump.P_out > inlet_pressure

    def test_normal_flow_range(self):
        """Test pump stays in normal operation when flow is within tolerance."""
        pump = PumpControlModule()

        # Get to normal operation
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Should remain normal
        pump.update(dt=1.0)
        assert pump.state == PUMP_STATES['NORMAL_OPERATION']


class TestFlowWarnings:
    """Test flow warning states."""

    def test_low_flow_warning(self):
        """Test low flow warning detection."""
        pump = PumpControlModule()

        # Get to normal operation
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Simulate low flow by reducing current flow
        pump.Q_current = PUMP_THRESHOLDS['Q_warning_low'] - 1
        pump.update(dt=1.0)

        assert pump.state == PUMP_STATES['LOW_FLOW_WARNING']

    def test_high_flow_warning(self):
        """Test high flow warning detection."""
        pump = PumpControlModule()

        # Get to normal operation
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Simulate high flow
        pump.Q_current = PUMP_THRESHOLDS['Q_warning_high'] + 1
        pump.update(dt=1.0)

        assert pump.state == PUMP_STATES['HIGH_FLOW_WARNING']

    def test_recovery_from_low_flow_warning(self):
        """Test pump can recover from low flow warning."""
        pump = PumpControlModule()

        # Get to normal operation
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Trigger low flow warning
        pump.Q_current = PUMP_THRESHOLDS['Q_warning_low'] - 1
        pump.update(dt=1.0)

        assert pump.state == PUMP_STATES['LOW_FLOW_WARNING']

        # Allow time to recover
        for _ in range(5):
            pump.update(dt=1.0)

        # Should recover to normal
        assert pump.state == PUMP_STATES['NORMAL_OPERATION']


class TestPressureAlarms:
    """Test pressure alarm conditions."""

    def test_high_pressure_alarm(self):
        """Test high pressure alarm triggers correctly."""
        pump = PumpControlModule()

        # Get to normal operation
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Simulate critical high pressure
        pump.P_out = PUMP_THRESHOLDS['P_critical_high'] + 5
        pump.update(dt=1.0)

        assert pump.state == PUMP_STATES['HIGH_PRESSURE_ALARM']

    def test_low_pressure_alarm(self):
        """Test low pressure alarm triggers correctly."""
        pump = PumpControlModule()

        # Get to normal operation
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Simulate critical low pressure (leak condition has higher priority)
        pump.P_out = PUMP_THRESHOLDS['P_critical_low'] - 5
        pump.update(dt=1.0)

        # Should trigger LEAK_DETECTED (higher priority) or LOW_PRESSURE_ALARM
        assert pump.state in [PUMP_STATES['LOW_PRESSURE_ALARM'], PUMP_STATES['LEAK_DETECTED']]


class TestTemperatureMonitoring:
    """Test temperature alarm conditions."""

    def test_high_temperature_alarm(self):
        """Test high temperature alarm."""
        pump = PumpControlModule()

        # Get to normal operation
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Simulate critical high temperature
        pump.update(dt=1.0, T_plasma=PUMP_THRESHOLDS['T_critical_high'] + 1)

        assert pump.state == PUMP_STATES['TEMPERATURE_ALARM']

    def test_low_temperature_alarm(self):
        """Test low temperature alarm."""
        pump = PumpControlModule()

        # Get to normal operation
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Simulate critical low temperature
        pump.update(dt=1.0, T_plasma=PUMP_THRESHOLDS['T_critical_low'] - 1)

        assert pump.state == PUMP_STATES['TEMPERATURE_ALARM']


class TestOperatorControls:
    """Test operator commands."""

    def test_stop_command(self):
        """Test stop command halts pump."""
        pump = PumpControlModule()

        # Start pump
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Issue stop command
        pump.update(dt=1.0, stop=True)

        assert pump.state == PUMP_STATES['OFF']
        assert pump.pump_running is False
        assert pump.Q_current == 0.0

    def test_pause_command(self):
        """Test pause command."""
        pump = PumpControlModule()

        # Start pump
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Issue pause command
        pump.update(dt=1.0, pause=True)

        assert pump.state == PUMP_STATES['OPERATOR_PAUSE']
        assert pump.pump_running is False

    def test_resume_from_pause(self):
        """Test resuming from pause."""
        pump = PumpControlModule()

        # Start, then pause
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)
        pump.update(dt=1.0, pause=True)

        assert pump.state == PUMP_STATES['OPERATOR_PAUSE']

        # Resume
        pump.update(dt=1.0, start=True, pause=False)

        assert pump.state == PUMP_STATES['NORMAL_OPERATION']


class TestEmergencyStop:
    """Test emergency stop functionality."""

    def test_emergency_stop_command(self):
        """Test emergency stop has highest priority."""
        pump = PumpControlModule()

        # Start pump
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Issue emergency stop
        pump.update(dt=1.0, emergency_stop=True)

        assert pump.state == PUMP_STATES['EMERGENCY_STOP']
        assert pump.pump_running is False
        assert pump.Q_current == 0.0

    def test_emergency_stop_priority(self):
        """Test emergency stop overrides other states."""
        pump = PumpControlModule()

        # Start pump and get to normal operation
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Emergency stop should override even with start command
        pump.update(dt=1.0, start=True, emergency_stop=True)

        assert pump.state == PUMP_STATES['EMERGENCY_STOP']


class TestLeakDetection:
    """Test leak detection functionality."""

    def test_leak_detection(self):
        """Test leak is detected when pressure drops critically."""
        pump = PumpControlModule()

        # Start pump
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Simulate leak condition (critical low pressure while running)
        pump.P_out = PUMP_THRESHOLDS['P_critical_low'] - 5
        pump.pump_running = True
        pump.update(dt=1.0)

        assert pump.state == PUMP_STATES['LEAK_DETECTED']
        assert pump.pump_running is False


class TestAirDetection:
    """Test air-in-line detection."""

    def test_air_detection(self):
        """Test air detection triggers emergency stop."""
        pump = PumpControlModule()

        # Start pump
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)

        # Simulate air detection
        pump.air_detected = PUMP_THRESHOLDS['air_volume_critical'] + 0.1
        pump.update(dt=1.0)

        assert pump.state == PUMP_STATES['AIR_IN_LINE_DETECTED']
        assert pump.pump_running is False


class TestOutputs:
    """Test output data structure."""

    def test_output_structure(self):
        """Test outputs contain all required fields."""
        pump = PumpControlModule()
        outputs = pump.update(dt=1.0)

        # Check required output fields
        assert 'Q_plasma' in outputs
        assert 'P_plasma' in outputs
        assert 'T_plasma' in outputs
        assert 'pump_running' in outputs
        assert 'state' in outputs
        assert 'state_name' in outputs
        assert 'air_detected' in outputs
        assert 'leak_detected' in outputs
        assert 'alarm_code' in outputs

    def test_alarm_code_generation(self):
        """Test alarm code is set correctly."""
        pump = PumpControlModule()

        # Normal operation - no alarm
        pump.update(dt=1.0, start=True)
        pump.update(dt=3.0)
        outputs = pump.update(dt=1.0)

        assert outputs['alarm_code'] == 0

        # Trigger alarm
        pump.update(dt=1.0, emergency_stop=True)
        outputs = pump.update(dt=1.0)

        assert outputs['alarm_code'] == 1

    def test_state_name_mapping(self):
        """Test state names are mapped correctly."""
        pump = PumpControlModule()

        assert pump.get_state_name() == 'OFF'

        pump.update(dt=1.0, start=True)
        assert pump.get_state_name() == 'STARTUP_PRIMING'

        pump.update(dt=3.0)
        assert pump.get_state_name() == 'NORMAL_OPERATION'


class TestSimulationTime:
    """Test simulation time tracking."""

    def test_time_advancement(self):
        """Test simulation time advances correctly."""
        pump = PumpControlModule()

        pump.update(dt=1.0)
        assert pump.simulation_time == 1.0

        pump.update(dt=2.5)
        assert pump.simulation_time == 3.5

    def test_time_in_state(self):
        """Test time_in_state resets on state change."""
        pump = PumpControlModule()

        # Start pump - transitions from OFF to STARTUP_PRIMING
        pump.update(dt=1.0, start=True)
        assert pump.time_in_state == 1.0
        assert pump.state == PUMP_STATES['STARTUP_PRIMING']

        # Second update - will transition to NORMAL_OPERATION after 2 min total (>= priming_duration)
        pump.update(dt=1.0)
        # After priming duration (2.0 min), transitions to NORMAL_OPERATION
        assert pump.state == PUMP_STATES['NORMAL_OPERATION']
        assert pump.time_in_state == 1.0  # Reset to dt after transition

        # Continue in NORMAL_OPERATION
        pump.update(dt=1.0)
        assert pump.state == PUMP_STATES['NORMAL_OPERATION']
        assert pump.time_in_state == 2.0  # Accumulated time
