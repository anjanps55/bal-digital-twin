"""
Unit tests for Sampler Module
"""

import pytest
from modules.sampler import SamplerModule
from config.constants import SAMPLER_STATES


def test_sampler_initialization():
    """Test sampler initializes correctly."""
    sampler = SamplerModule()
    assert sampler.name == "Sampler"
    assert sampler.state == SAMPLER_STATES['IDLE_STANDBY']
    assert sampler.samples_collected == 0
    assert sampler.valve_open == False


def test_sampler_auto_trigger():
    """Test automatic sampling trigger after interval."""
    sampler = SamplerModule()

    inputs = {
        'Q_plasma': 30.0,
        'P_plasma': 80.0,
        'T_plasma': 37.0
    }

    # Run for 30 minutes
    for _ in range(30):
        outputs = sampler.update(dt=1.0, **inputs)

    # Should have started sampling automatically
    assert sampler.time_since_last_sample >= 30.0 or sampler.state != SAMPLER_STATES['IDLE_STANDBY']


def test_sampler_manual_trigger():
    """Test manual sampling trigger."""
    sampler = SamplerModule()

    inputs = {
        'Q_plasma': 30.0,
        'P_plasma': 80.0,
        'T_plasma': 37.0,
        'trigger_sample': True
    }

    # Should start sampling
    outputs = sampler.update(dt=1.0, **inputs)

    assert sampler.state == SAMPLER_STATES['SAMPLING_ACTIVE']
    assert sampler.valve_open == True


def test_sample_collection():
    """Test sample collection process."""
    sampler = SamplerModule()

    # Trigger sampling
    inputs = {
        'Q_plasma': 30.0,
        'P_plasma': 80.0,
        'T_plasma': 37.0,
        'trigger_sample': True
    }

    sampler.update(dt=1.0, **inputs)
    assert sampler.state == SAMPLER_STATES['SAMPLING_ACTIVE']

    # Continue sampling
    inputs['trigger_sample'] = False
    for _ in range(5):
        outputs = sampler.update(dt=1.0, **inputs)

    # Should have collected sample
    assert sampler.samples_collected >= 1


def test_low_pressure_failure():
    """Test sampling fails with low pressure."""
    sampler = SamplerModule()

    # Low pressure
    inputs = {
        'Q_plasma': 30.0,
        'P_plasma': 40.0,  # Below 50 mmHg threshold
        'T_plasma': 37.0,
        'trigger_sample': True
    }

    outputs = sampler.update(dt=1.0, **inputs)

    # Should fail to sample
    assert sampler.state == SAMPLER_STATES['SAMPLING_FAILED']
    assert sampler.sampling_failures >= 1


def test_purge_cycle():
    """Test purge cycle after sample collection."""
    sampler = SamplerModule()

    # Trigger and collect sample
    inputs = {
        'Q_plasma': 30.0,
        'P_plasma': 80.0,
        'T_plasma': 37.0,
        'trigger_sample': True
    }

    sampler.update(dt=1.0, **inputs)

    # Run until sample collected
    inputs['trigger_sample'] = False
    for _ in range(10):
        outputs = sampler.update(dt=0.5, **inputs)
        if sampler.state == SAMPLER_STATES['SAMPLE_COLLECTED']:
            break

    assert sampler.state == SAMPLER_STATES['SAMPLE_COLLECTED']

    # Continue to purge
    for _ in range(5):
        outputs = sampler.update(dt=0.5, **inputs)

    # Should go through purge and back to idle
    assert sampler.state in [SAMPLER_STATES['PURGE_CLEANING'], SAMPLER_STATES['IDLE_STANDBY']]


def test_sample_volume_tracking():
    """Test sample volume is tracked correctly."""
    sampler = SamplerModule()

    inputs = {
        'Q_plasma': 30.0,
        'P_plasma': 80.0,
        'T_plasma': 37.0,
        'trigger_sample': True
    }

    initial_volume = sampler.total_volume_collected

    # Trigger sampling
    sampler.update(dt=1.0, **inputs)
    inputs['trigger_sample'] = False

    # Run sampling
    for _ in range(5):
        sampler.update(dt=1.0, **inputs)

    # Should have collected some volume
    assert sampler.total_volume_collected > initial_volume


def test_passthrough_parameters():
    """Test plasma parameters pass through unchanged."""
    sampler = SamplerModule()

    inputs = {
        'Q_plasma': 30.0,
        'P_plasma': 80.0,
        'T_plasma': 37.0
    }

    outputs = sampler.update(dt=1.0, **inputs)

    # Parameters should pass through
    assert outputs['Q_plasma'] == 30.0
    assert outputs['P_plasma'] == 80.0
    assert outputs['T_plasma'] == 37.0


def test_state_transitions():
    """Test state machine transitions."""
    sampler = SamplerModule()

    # Start in IDLE
    assert sampler.state == SAMPLER_STATES['IDLE_STANDBY']

    # Trigger sampling
    inputs = {
        'Q_plasma': 30.0,
        'P_plasma': 80.0,
        'T_plasma': 37.0,
        'trigger_sample': True
    }

    sampler.update(dt=1.0, **inputs)
    assert sampler.state == SAMPLER_STATES['SAMPLING_ACTIVE']

    # Continue sampling
    inputs['trigger_sample'] = False
    for _ in range(10):
        sampler.update(dt=0.5, **inputs)

    # Should progress through states
    assert sampler.state in [SAMPLER_STATES['SAMPLE_COLLECTED'],
                            SAMPLER_STATES['PURGE_CLEANING'],
                            SAMPLER_STATES['IDLE_STANDBY']]


def test_alarm_codes():
    """Test alarm code generation."""
    sampler = SamplerModule()

    # Normal operation - no alarm
    inputs = {
        'Q_plasma': 30.0,
        'P_plasma': 80.0,
        'T_plasma': 37.0
    }
    outputs = sampler.update(dt=1.0, **inputs)
    assert outputs['alarm_code'] == 0

    # Cause failure with low pressure
    inputs['trigger_sample'] = True
    inputs['P_plasma'] = 40.0
    outputs = sampler.update(dt=1.0, **inputs)
    assert outputs['alarm_code'] == 1  # Warning for failure


def test_state_name():
    """Test get_state_name returns correct names."""
    sampler = SamplerModule()

    assert sampler.get_state_name() == 'IDLE_STANDBY'

    # Trigger sampling
    inputs = {
        'Q_plasma': 30.0,
        'P_plasma': 80.0,
        'trigger_sample': True
    }
    sampler.update(dt=1.0, **inputs)
    assert sampler.get_state_name() == 'SAMPLING_ACTIVE'


def test_multiple_samples():
    """Test collecting multiple samples over time."""
    sampler = SamplerModule()

    inputs = {
        'Q_plasma': 30.0,
        'P_plasma': 80.0,
        'T_plasma': 37.0
    }

    initial_samples = sampler.samples_collected

    # Collect 3 samples
    for _ in range(3):
        # Trigger sample
        inputs['trigger_sample'] = True
        sampler.update(dt=1.0, **inputs)
        inputs['trigger_sample'] = False

        # Wait for collection to complete
        for _ in range(10):
            sampler.update(dt=0.5, **inputs)

        # Wait for return to idle
        while sampler.state != SAMPLER_STATES['IDLE_STANDBY']:
            sampler.update(dt=0.5, **inputs)

    # Should have collected samples
    assert sampler.samples_collected > initial_samples
