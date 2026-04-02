"""
Tests for Simulation Engine

Verifies the simulation engine coordinates modules correctly.
"""

import pytest
import os
from simulation.engine import SimulationEngine


def test_engine_initialization():
    """Test that engine initializes correctly."""
    engine = SimulationEngine(dt=1.0)

    # Verify separator is initialized
    assert engine.separator is not None
    assert engine.separator.name == "Plasma Separator"

    # Verify time is initialized
    assert engine.current_time == 0.0

    # Verify history is empty
    assert len(engine.history) == 0

    # Verify data logger exists
    assert engine.data_logger is not None

    # Verify other modules are None (not yet implemented)
    assert engine.pump is None
    assert engine.bioreactor is None
    assert engine.sampler is None
    assert engine.mixer is None
    assert engine.return_monitor is None


def test_engine_initialization_errors():
    """Test that engine validates parameters."""
    # Should raise error for negative dt
    with pytest.raises(ValueError):
        SimulationEngine(dt=-1.0)

    # Should raise error for zero dt
    with pytest.raises(ValueError):
        SimulationEngine(dt=0.0)


def test_single_step():
    """Test that a single simulation step works."""
    engine = SimulationEngine(dt=1.0)

    # Take one step
    outputs = engine.step()

    # Verify time advanced
    assert engine.current_time == 1.0

    # Verify history has one entry
    assert len(engine.history) == 1

    # Verify outputs contain expected keys
    assert 'time' in outputs
    assert 'state' in outputs
    assert 'state_name' in outputs
    assert 'Q_plasma' in outputs
    assert 'Q_cells' in outputs

    # Verify separator state is valid (should be STARTUP_PRIMING initially)
    assert outputs['state'] in [0, 1, 2, 3, 4, 5]
    assert outputs['state_name'] in [
        'STARTUP_PRIMING', 'NORMAL_OPERATION', 'DEGRADED_PERFORMANCE',
        'MEMBRANE_FOULED', 'MEMBRANE_CLOTTED', 'MEMBRANE_FAILURE'
    ]


def test_short_simulation():
    """Test a short 10-minute simulation."""
    engine = SimulationEngine(dt=1.0)

    # Run 10-minute simulation
    final_outputs = engine.run(duration=10.0)

    # Verify correct number of steps
    assert len(engine.history) == 10

    # Verify final time
    assert engine.current_time == 10.0

    # Verify time progression in history
    for i, entry in enumerate(engine.history):
        assert entry['time'] == i  # Should be 0, 1, 2, ..., 9

    # Verify mass balance maintained throughout
    for entry in engine.history:
        Q_blood = 150  # Nominal blood flow
        Q_total = entry['Q_plasma'] + entry['Q_cells']
        # Allow small floating point error
        assert abs(Q_total - Q_blood) < 0.01

    # Verify final outputs are returned
    assert final_outputs is not None
    assert 'state_name' in final_outputs


def test_state_transitions():
    """Test that separator transitions through states correctly."""
    engine = SimulationEngine(dt=1.0)

    # Run simulation and track state changes
    states_seen = []

    for _ in range(5):
        outputs = engine.step()
        states_seen.append(outputs['state_name'])

    # Should start in STARTUP_PRIMING
    assert states_seen[0] == 'STARTUP_PRIMING'

    # Should transition to NORMAL_OPERATION around 2 minutes
    # (after STARTUP_PRIMING completes)
    assert 'NORMAL_OPERATION' in states_seen[2:]


def test_data_export():
    """Test that data export works correctly."""
    engine = SimulationEngine(dt=1.0)

    # Run short simulation
    engine.run(duration=5.0)

    # Export to CSV
    csv_file = "test_results.csv"
    engine.data_logger.export_csv(csv_file)

    # Verify CSV file was created
    csv_path = os.path.join(engine.data_logger.output_dir, csv_file)
    assert os.path.exists(csv_path)

    # Export to JSON
    json_file = "test_results.json"
    engine.data_logger.export_json(json_file)

    # Verify JSON file was created
    json_path = os.path.join(engine.data_logger.output_dir, json_file)
    assert os.path.exists(json_path)

    # Clean up test files
    if os.path.exists(csv_path):
        os.remove(csv_path)
    if os.path.exists(json_path):
        os.remove(json_path)


def test_get_module_states():
    """Test getting module states."""
    engine = SimulationEngine(dt=1.0)

    states = engine.get_module_states()

    # Verify all modules are reported
    assert 'Plasma Separator' in states
    assert 'Plasma Pump and Control' in states
    assert 'Bioreactor System' in states
    assert 'Sampler' in states
    assert 'Mixer' in states
    assert 'Return Monitor' in states

    # Verify Module 1 has a valid state
    assert states['Plasma Separator'] in [
        'STARTUP_PRIMING', 'NORMAL_OPERATION', 'DEGRADED_PERFORMANCE',
        'MEMBRANE_FOULED', 'MEMBRANE_CLOTTED', 'MEMBRANE_FAILURE'
    ]

    # Verify other modules are not implemented
    assert states['Plasma Pump and Control'] == 'NOT_IMPLEMENTED'
    assert states['Bioreactor System'] == 'NOT_IMPLEMENTED'


def test_get_current_outputs():
    """Test getting current outputs."""
    engine = SimulationEngine(dt=1.0)

    # Before any steps, should return empty
    outputs = engine.get_current_outputs()
    assert outputs == {}

    # After one step, should have data
    engine.step()
    outputs = engine.get_current_outputs()
    assert len(outputs) > 0
    assert 'time' in outputs
    assert 'Q_plasma' in outputs


def test_reset():
    """Test resetting the simulation."""
    engine = SimulationEngine(dt=1.0)

    # Run a few steps
    engine.run(duration=5.0)

    # Verify data exists
    assert engine.current_time == 5.0
    assert len(engine.history) > 0
    assert len(engine.data_logger.data) > 0

    # Reset
    engine.reset()

    # Verify everything is cleared
    assert engine.current_time == 0.0
    assert len(engine.history) == 0
    assert len(engine.data_logger.data) == 0


def test_data_logger_summary():
    """Test data logger summary statistics."""
    engine = SimulationEngine(dt=1.0)

    # Empty summary
    summary = engine.data_logger.get_summary()
    assert summary['total_points'] == 0

    # Run simulation
    engine.run(duration=10.0)

    # Get summary
    summary = engine.data_logger.get_summary()
    assert summary['total_points'] == 10
    assert summary['time_range'] == (0.0, 9.0)  # 0 through 9
    assert 'time' in summary['columns']
    assert 'Q_plasma' in summary['columns']


def test_run_duration_validation():
    """Test that run() validates duration."""
    engine = SimulationEngine(dt=1.0)

    # Should raise error for negative duration
    with pytest.raises(ValueError):
        engine.run(duration=-10.0)

    # Should raise error for zero duration
    with pytest.raises(ValueError):
        engine.run(duration=0.0)
