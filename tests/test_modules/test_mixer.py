"""
Unit tests for Mixer Module
"""

import pytest
from modules.mixer import MixerModule
from config.constants import MIXER_STATES


def test_mixer_initialization():
    """Test mixer initializes correctly."""
    mixer = MixerModule()
    assert mixer.name == "Mixer"
    assert mixer.state == MIXER_STATES['IDLE_STANDBY']
    assert mixer.Q_blood_out == 0.0
    assert mixer.Hct_out == 0.0
    assert mixer.mixing_efficiency == 1.0


def test_mixer_mass_balance():
    """Test Q_blood_out = Q_plasma + Q_cells."""
    mixer = MixerModule()

    inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }

    outputs = mixer.update(dt=1.0, **inputs)

    # Mass balance check
    assert abs(outputs['Q_blood'] - 150.0) < 0.01

    # Flow ratio check (30/150 = 0.20)
    assert abs(outputs['flow_ratio'] - 0.20) < 0.01


def test_mixer_state_transitions():
    """Test state transitions."""
    mixer = MixerModule()

    # Should start in IDLE
    assert mixer.state == MIXER_STATES['IDLE_STANDBY']

    # Start flows - should transition to STARTUP_PRIMING
    inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }
    mixer.update(dt=1.0, **inputs)
    assert mixer.state == MIXER_STATES['STARTUP_PRIMING']

    # After priming duration, should go to NORMAL_MIXING
    for _ in range(3):
        mixer.update(dt=1.0, **inputs)
    assert mixer.state == MIXER_STATES['NORMAL_MIXING']


def test_mixer_hematocrit_restoration():
    """Test hematocrit is properly restored."""
    mixer = MixerModule()

    inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'Hct_cells': 0.40,  # Concentrated stream
        'P_plasma': 80.0,
        'P_cells': 90.0
    }

    outputs = mixer.update(dt=1.0, **inputs)

    # Should restore to ~0.32 hematocrit
    # Calculation: (120 * 0.40) / 150 = 48/150 = 0.32
    assert 0.28 <= outputs['Hct_out'] <= 0.36


def test_mixer_imbalanced_flows():
    """Test detection of flow imbalance."""
    mixer = MixerModule()

    # Start with normal flows
    normal_inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }
    for _ in range(5):
        mixer.update(dt=1.0, **normal_inputs)

    assert mixer.state == MIXER_STATES['NORMAL_MIXING']

    # Now create imbalance (70/120 = 0.583, error = 0.333, exceeds critical 0.10)
    imbalanced_inputs = {
        'Q_plasma': 70.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }
    mixer.update(dt=1.0, **imbalanced_inputs)

    # Should detect imbalance (flow_ratio = 70/190 = 0.368, error = 0.118 > 0.10)
    assert mixer.state == MIXER_STATES['IMBALANCED_MIXING']


def test_mixer_single_stream_failure():
    """Test detection when one stream fails."""
    mixer = MixerModule()

    # Start with normal flows
    normal_inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }
    for _ in range(5):
        mixer.update(dt=1.0, **normal_inputs)

    assert mixer.state == MIXER_STATES['NORMAL_MIXING']

    # Now one stream fails
    failed_inputs = {
        'Q_plasma': 0.0,  # Plasma stream fails
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }
    mixer.update(dt=1.0, **failed_inputs)

    # Should detect single stream failure
    assert mixer.state == MIXER_STATES['SINGLE_STREAM_FAILURE']


def test_mixer_pressure_calculation():
    """Test output pressure calculation."""
    mixer = MixerModule()

    inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }

    outputs = mixer.update(dt=1.0, **inputs)

    # Average pressure = (80 + 90) / 2 = 85
    # Minus pressure drop (10 mmHg) = 75
    assert abs(outputs['P_out'] - 75.0) < 0.01


def test_mixer_temperature_averaging():
    """Test temperature is averaged between streams."""
    mixer = MixerModule()

    inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'T_plasma': 36.5,
        'T_cells': 37.5,
        'Hct_cells': 0.40
    }

    outputs = mixer.update(dt=1.0, **inputs)

    # Average temperature = (36.5 + 37.5) / 2 = 37.0
    assert abs(outputs['T_out'] - 37.0) < 0.01


def test_mixer_concentrations_passthrough():
    """Test that concentrations are passed through from plasma."""
    mixer = MixerModule()

    inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'C_NH3': 50.0,
        'C_lido': 15.0,
        'C_urea': 8.0,
        'Hct_cells': 0.40
    }

    outputs = mixer.update(dt=1.0, **inputs)

    # Concentrations should pass through
    assert outputs['C_NH3'] == 50.0
    assert outputs['C_lido'] == 15.0
    assert outputs['C_urea'] == 8.0


def test_mixer_recovery_from_imbalance():
    """Test recovery from imbalanced state."""
    mixer = MixerModule()

    # Get to normal state
    normal_inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }
    for _ in range(5):
        mixer.update(dt=1.0, **normal_inputs)

    assert mixer.state == MIXER_STATES['NORMAL_MIXING']

    # Create imbalance
    imbalanced_inputs = {
        'Q_plasma': 70.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }
    mixer.update(dt=1.0, **imbalanced_inputs)
    assert mixer.state == MIXER_STATES['IMBALANCED_MIXING']

    # Restore balance
    for _ in range(2):
        mixer.update(dt=1.0, **normal_inputs)

    # Should recover to NORMAL_MIXING
    assert mixer.state == MIXER_STATES['NORMAL_MIXING']


def test_mixer_zero_flows():
    """Test behavior with zero flows."""
    mixer = MixerModule()

    inputs = {
        'Q_plasma': 0.0,
        'Q_cells': 0.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }

    outputs = mixer.update(dt=1.0, **inputs)

    # Should remain in IDLE
    assert mixer.state == MIXER_STATES['IDLE_STANDBY']
    assert outputs['Q_blood'] == 0.0
    assert outputs['Hct_out'] == 0.0


def test_mixer_mixing_efficiency():
    """Test mixing efficiency calculation."""
    mixer = MixerModule()

    # Balanced flows (flow_ratio = 0.20, target = 0.25, error = 0.05, within tolerance)
    balanced_inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }

    outputs = mixer.update(dt=1.0, **balanced_inputs)

    # Should have high efficiency
    assert outputs['mixing_efficiency'] >= 0.95


def test_mixer_state_name():
    """Test get_state_name returns correct names."""
    mixer = MixerModule()

    assert mixer.get_state_name() == 'IDLE_STANDBY'

    # Transition to STARTUP
    inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }
    mixer.update(dt=1.0, **inputs)
    assert mixer.get_state_name() == 'STARTUP_PRIMING'


def test_mixer_alarm_codes():
    """Test alarm code generation."""
    mixer = MixerModule()

    # IDLE - no alarm
    outputs = mixer.update(dt=1.0, Q_plasma=0.0, Q_cells=0.0)
    assert outputs['alarm_code'] == 0

    # Get to NORMAL - no alarm
    normal_inputs = {
        'Q_plasma': 30.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }
    for _ in range(5):
        outputs = mixer.update(dt=1.0, **normal_inputs)
    assert outputs['alarm_code'] == 0

    # Create imbalance - warning alarm
    imbalanced_inputs = {
        'Q_plasma': 70.0,
        'Q_cells': 120.0,
        'P_plasma': 80.0,
        'P_cells': 90.0,
        'Hct_cells': 0.40
    }
    outputs = mixer.update(dt=1.0, **imbalanced_inputs)
    assert outputs['alarm_code'] == 1  # Warning
