"""
Unit tests for Return Monitor Module
"""

import pytest
from modules.return_monitor import ReturnMonitorModule
from config.constants import RETURN_MONITOR_STATES


def test_return_monitor_initialization():
    """Test return monitor initializes correctly."""
    monitor = ReturnMonitorModule()
    assert monitor.name == "Return Monitor"
    assert monitor.state == RETURN_MONITOR_STATES['MONITORING_TESTING']
    assert monitor.return_approved == False
    assert monitor.treatment_success == False
    assert monitor.consecutive_safe_checks == 0


def test_safe_blood_approval():
    """Test approval when all parameters are safe."""
    monitor = ReturnMonitorModule()

    safe_inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 35.0,      # Safe level
        'C_lido': 7.0,      # Safe level
        'C_urea': 8.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    # Need multiple consecutive safe checks
    for _ in range(5):
        outputs = monitor.update(dt=1.0, **safe_inputs)

    assert outputs['return_approved'] == True
    assert outputs['treatment_success'] == True
    assert monitor.state == RETURN_MONITOR_STATES['SAFE_TO_RETURN']
    assert len(outputs['violations']) == 0


def test_elevated_ammonia_detection():
    """Test detection of elevated ammonia."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 47.0,      # Above warning (45), below critical (60)
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'WARNING_AMMONIA' in outputs['violations']
    assert monitor.state == RETURN_MONITOR_STATES['ELEVATED_AMMONIA_WARNING']


def test_elevated_lidocaine_detection():
    """Test detection of elevated lidocaine."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 35.0,
        'C_lido': 9.5,      # Above warning (9), below critical (15)
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'WARNING_LIDOCAINE' in outputs['violations']
    assert monitor.state == RETURN_MONITOR_STATES['ELEVATED_LIDOCAINE_WARNING']


def test_critical_ammonia_toxicity():
    """Test critical ammonia toxicity detection."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 70.0,      # Critical level (>60)
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'CRITICAL_AMMONIA' in outputs['violations']
    assert monitor.state == RETURN_MONITOR_STATES['CRITICAL_TOXICITY_DETECTED']
    assert outputs['treatment_success'] == False


def test_critical_lidocaine_toxicity():
    """Test critical lidocaine toxicity detection."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 35.0,
        'C_lido': 16.0,     # Critical level (>15)
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'CRITICAL_LIDOCAINE' in outputs['violations']
    assert monitor.state == RETURN_MONITOR_STATES['CRITICAL_TOXICITY_DETECTED']


def test_air_detection():
    """Test air detection and emergency response."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.6,  # Critical air volume (>0.5)
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'CRITICAL_AIR' in outputs['violations']
    assert monitor.state == RETURN_MONITOR_STATES['AIR_DETECTED']


def test_air_warning():
    """Test air warning detection."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.2,  # Warning level (>0.1, <0.5)
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'WARNING_AIR' in outputs['violations']


def test_temperature_alarm_high():
    """Test high temperature alarm."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 38.5,      # Critical high (>38.0)
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'CRITICAL_TEMPERATURE' in outputs['violations']
    assert monitor.state == RETURN_MONITOR_STATES['TEMPERATURE_ALARM']


def test_temperature_alarm_low():
    """Test low temperature alarm."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 34.5,      # Critical low (<35.0)
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'CRITICAL_TEMPERATURE' in outputs['violations']
    assert monitor.state == RETURN_MONITOR_STATES['TEMPERATURE_ALARM']


def test_temperature_warning():
    """Test temperature warning detection."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.6,      # Warning (>37.5, <38.0)
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'WARNING_TEMPERATURE' in outputs['violations']


def test_hemolysis_detection():
    """Test hemolysis detection."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 110.0    # Critical hemolysis (>100)
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'CRITICAL_HEMOLYSIS' in outputs['violations']
    assert monitor.state == RETURN_MONITOR_STATES['HEMOLYSIS_DETECTED']


def test_hemolysis_warning():
    """Test hemolysis warning detection."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 60.0     # Warning level (>50, <100)
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'WARNING_HEMOLYSIS' in outputs['violations']


def test_abnormal_hematocrit_low():
    """Test low hematocrit detection."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.18,    # Critical low (<0.20)
        'T_out': 37.0,
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'CRITICAL_HEMATOCRIT' in outputs['violations']
    assert monitor.state == RETURN_MONITOR_STATES['ABNORMAL_HEMATOCRIT']


def test_abnormal_hematocrit_high():
    """Test high hematocrit detection."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.55,    # Critical high (>0.50)
        'T_out': 37.0,
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'CRITICAL_HEMATOCRIT' in outputs['violations']
    assert monitor.state == RETURN_MONITOR_STATES['ABNORMAL_HEMATOCRIT']


def test_hematocrit_warning():
    """Test hematocrit warning detection."""
    monitor = ReturnMonitorModule()

    inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.22,    # Warning low (>0.20, <0.25)
        'T_out': 37.0,
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **inputs)

    assert outputs['return_approved'] == False
    assert 'WARNING_HEMATOCRIT' in outputs['violations']


def test_treatment_success_evaluation():
    """Test treatment success criteria."""
    monitor = ReturnMonitorModule()

    # Successful treatment
    success_inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 40.0,      # Below success threshold (50)
        'C_lido': 8.0,      # Below success threshold (10)
        'C_urea': 8.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    for _ in range(5):
        outputs = monitor.update(dt=1.0, **success_inputs)

    assert outputs['treatment_success'] == True


def test_treatment_failure():
    """Test treatment failure detection."""
    monitor = ReturnMonitorModule()

    # Failed treatment (toxins still too high)
    failure_inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 55.0,      # Above success threshold (50)
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **failure_inputs)

    assert outputs['treatment_success'] == False


def test_consecutive_safe_checks():
    """Test that multiple consecutive safe checks are required."""
    monitor = ReturnMonitorModule()

    safe_inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }

    # First check - not yet approved
    outputs = monitor.update(dt=1.0, **safe_inputs)
    assert outputs['return_approved'] == False

    # Second check - not yet approved
    outputs = monitor.update(dt=1.0, **safe_inputs)
    assert outputs['return_approved'] == False

    # Third check - now approved
    outputs = monitor.update(dt=1.0, **safe_inputs)
    assert outputs['return_approved'] == True


def test_alarm_codes():
    """Test alarm code generation."""
    monitor = ReturnMonitorModule()

    # No violations - no alarm
    safe_inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 35.0,
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }
    outputs = monitor.update(dt=1.0, **safe_inputs)
    assert outputs['alarm_code'] == 0

    # Warning - alarm code 1
    warning_inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 47.0,      # Warning level
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }
    outputs = monitor.update(dt=1.0, **warning_inputs)
    assert outputs['alarm_code'] == 1

    # Critical - alarm code 2
    critical_inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 70.0,      # Critical level
        'C_lido': 7.0,
        'air_volume': 0.0,
        'free_Hb': 5.0
    }
    outputs = monitor.update(dt=1.0, **critical_inputs)
    assert outputs['alarm_code'] == 2


def test_violation_tracking():
    """Test that violations are tracked correctly."""
    monitor = ReturnMonitorModule()

    # Multiple violations
    multi_violation_inputs = {
        'Q_blood': 150.0,
        'Hct_out': 0.32,
        'T_out': 37.0,
        'C_NH3': 47.0,      # Warning
        'C_lido': 9.5,      # Warning
        'air_volume': 0.2,  # Warning
        'free_Hb': 5.0
    }

    outputs = monitor.update(dt=1.0, **multi_violation_inputs)

    assert outputs['violation_count'] == 3
    assert 'WARNING_AMMONIA' in outputs['violations']
    assert 'WARNING_LIDOCAINE' in outputs['violations']
    assert 'WARNING_AIR' in outputs['violations']
