"""
Module 4: Sampler

Collects small aliquots for analysis and monitoring.
"""

from typing import Dict, Any
from modules.base_module import BaseModule
from config.constants import SAMPLER_STATES, SAMPLER_THRESHOLDS


class SamplerModule(BaseModule):
    """Sampler Module - Collects samples for offline/inline analysis"""
    
    def __init__(self):
        super().__init__("Sampler")
        self.state = 0  # IDLE_STANDBY
        self.Q_plasma = 0.0
        self.P_plasma = 80.0
        self.T_plasma = 37.0
        self.C_NH3 = 35.0
        self.C_lido = 7.0
        self.C_urea = 5.0
        self.valve_open = False
        self.sample_volume_current = 0.0
        self.samples_collected = 0
        self.time_since_last_sample = 0.0
        self.sampling_triggered = False
        self.sampling_failures = 0
        self.total_volume_collected = 0.0
    
    def update(self, dt: float = 1.0, **inputs) -> Dict[str, Any]:
        self.time_in_state += dt
        self.simulation_time += dt
        self.time_since_last_sample += dt
        
        self.Q_plasma = inputs.get('Q_plasma', 0.0)
        self.P_plasma = inputs.get('P_plasma', 80.0)
        self.T_plasma = inputs.get('T_plasma', 37.0)
        self.C_NH3 = inputs.get('C_NH3', 35.0)
        self.C_lido = inputs.get('C_lido', 7.0)
        self.C_urea = inputs.get('C_urea', 5.0)
        
        if inputs.get('trigger_sample', False):
            self.sampling_triggered = True
        
        # Auto-trigger every 30 min
        if self.time_since_last_sample >= 30.0 and self.state == 0:
            self.sampling_triggered = True
        
        # Collect sample if active
        if self.state == 1 and self.valve_open:
            if self.P_plasma >= 50:
                sample_flow = self.Q_plasma * 0.05
                self.sample_volume_current += sample_flow * dt
                self.total_volume_collected += sample_flow * dt
        
        self._check_state_transition()
        return self._get_outputs()
    
    def _check_state_transition(self):
        if self.state == 0:  # IDLE
            if self.sampling_triggered:
                if self.P_plasma >= 50:
                    self.state = 1  # SAMPLING_ACTIVE
                    self.valve_open = True
                    self.sample_volume_current = 0.0
                    self.time_in_state = 0.0
                else:
                    self.state = 3  # FAILED
                    self.sampling_failures += 1
                self.sampling_triggered = False
        
        elif self.state == 1:  # SAMPLING_ACTIVE
            if self.sample_volume_current >= 5.0:
                self.state = 2  # COLLECTED
                self.valve_open = False
                self.samples_collected += 1
                self.time_since_last_sample = 0.0
                self.time_in_state = 0.0
            elif self.time_in_state >= 2.0:
                if self.sample_volume_current >= 2.0:
                    self.state = 2
                    self.samples_collected += 1
                else:
                    self.state = 3
                    self.sampling_failures += 1
                self.valve_open = False
                self.time_since_last_sample = 0.0
        
        elif self.state == 2:  # COLLECTED
            if self.time_in_state >= 0.5:
                self.state = 4  # PURGE
                self.time_in_state = 0.0
        
        elif self.state == 4:  # PURGE
            if self.time_in_state >= 1.0:
                self.state = 0  # IDLE
                self.sample_volume_current = 0.0
                self.time_in_state = 0.0
        
        elif self.state == 3:  # FAILED
            if self.time_in_state >= 5.0:
                self.state = 0
                self.sample_volume_current = 0.0
                self.time_in_state = 0.0
    
    def _get_outputs(self) -> Dict[str, Any]:
        return {
            'Q_plasma': self.Q_plasma,
            'P_plasma': self.P_plasma,
            'T_plasma': self.T_plasma,
            'C_NH3': self.C_NH3,  # Pass through concentrations
            'C_lido': self.C_lido,
            'C_urea': self.C_urea,
            'state': self.state,
            'state_name': self.get_state_name(),
            'valve_open': self.valve_open,
            'sample_volume_current': self.sample_volume_current,
            'samples_collected': self.samples_collected,
            'sampling_failures': self.sampling_failures,
            'total_volume_collected': self.total_volume_collected,
            'time_since_last_sample': self.time_since_last_sample,
            'alarm_code': self._get_alarm_code()
        }
    
    def _get_alarm_code(self) -> int:
        """Get alarm code based on current state."""
        if self.state == 3:  # SAMPLING_FAILED
            return 1  # Warning
        else:
            return 0  # No alarm

    def get_state_name(self) -> str:
        names = {0: 'IDLE_STANDBY', 1: 'SAMPLING_ACTIVE', 2: 'SAMPLE_COLLECTED',
                3: 'SAMPLING_FAILED', 4: 'PURGE_CLEANING'}
        return names.get(self.state, 'UNKNOWN')
