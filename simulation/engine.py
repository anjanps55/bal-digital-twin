"""
Simulation Engine

Coordinates all modules and advances simulation time.
"""

from typing import Dict, List, Any, Optional
from modules.separator import SeparatorModule
from modules.pump_control import PumpControlModule
from modules.mixer import MixerModule
from modules.return_monitor import ReturnMonitorModule
from modules.sampler import SamplerModule
from modules.bioreactor.bioreactor_system import BioreactorSystem
from simulation.data_logger import DataLogger


class SimulationEngine:
    """
    Main simulation coordinator for BAL Digital Twin.

    Manages time stepping, module connections, and data flow.
    Currently implements Module 1 (Separator) with placeholders for future modules.
    """

    def __init__(self, dt: float = 1.0):
        """
        Initialize simulation engine.

        Args:
            dt: Time step in minutes (default: 1.0)

        Raises:
            ValueError: If dt <= 0
        """
        if dt <= 0:
            raise ValueError("Time step dt must be positive")

        self.dt = dt
        self.current_time = 0.0

        # Initialize implemented modules
        self.separator = SeparatorModule()  # Module 1
        self.pump = PumpControlModule()  # Module 2
        self.bioreactor = BioreactorSystem()  # Module 3
        self.sampler = SamplerModule()  # Module 4
        self.mixer = MixerModule()  # Module 5
        self.return_monitor = ReturnMonitorModule()  # Module 6

        # Module list for easy iteration
        self.modules = [self.separator, self.pump, self.bioreactor, self.sampler, self.mixer, self.return_monitor]

        # Data storage
        self.history = []

        # Data logger
        self.data_logger = DataLogger()

    def step(self) -> Dict[str, Any]:
        """
        Advance simulation by one time step.

        Executes one iteration of the simulation:
        1. Updates all active modules
        2. Logs data
        3. Increments time
        4. Returns current state

        Returns:
            Dict containing current state of all modules and outputs
        """
        # Module 1: Separator
        sep_outputs = self.separator.update(dt=self.dt)

        # Module 2: Pump Control (NEW! - controls plasma flow with safety monitoring)
        pump_inputs = {
            'Q_plasma': sep_outputs['Q_plasma'],
            'P_plasma': sep_outputs['P_plasma'],
            'T_plasma': sep_outputs['T_plasma'],
            'start': True,  # Auto-start
            'stop': False,
            'pause': False,
            'emergency_stop': False
        }
        pump_outputs = self.pump.update(dt=self.dt, **pump_inputs)

        # Module 3: Bioreactor (treats the plasma with controlled flow from pump)
        bio_inputs = {
            'Q_plasma': pump_outputs['Q_plasma'],
            'P_plasma': pump_outputs['P_plasma'],
            'T_plasma': pump_outputs['T_plasma'],
            'C_NH3': sep_outputs['C_NH3_plasma'],
            'C_lido': sep_outputs['C_lido_plasma'],
            'C_urea': sep_outputs.get('C_urea_plasma', 5.0)
        }
        bio_outputs = self.bioreactor.update(dt=self.dt, **bio_inputs)

        # Module 4: Sampler (monitoring between bioreactor and mixer)
        sampler_inputs = {
            'Q_plasma': bio_outputs['Q_plasma'],
            'P_plasma': bio_outputs['P_plasma'],
            'C_NH3': bio_outputs['C_NH3'],
            'C_lido': bio_outputs['C_lido'],
            'trigger_sample': False  # Auto mode
        }
        sampler_outputs = self.sampler.update(dt=self.dt, **sampler_inputs)

        # Module 5: Mixer
        # Now receives TREATED plasma from bioreactor!
        mixer_inputs = {
            'Q_plasma': sampler_outputs['Q_plasma'],
            'Q_cells': sep_outputs['Q_cells'],
            'P_plasma': bio_outputs['P_plasma'],
            'P_cells': sep_outputs.get('P_cells', 90.0),
            'T_plasma': bio_outputs['T_plasma'],
            'Hct_cells': sep_outputs.get('Hct_post', 0.40),
            'C_NH3': sampler_outputs['C_NH3'],
            'C_lido': sampler_outputs['C_lido'],
            'C_urea': sampler_outputs['C_urea']
        }
        mixer_outputs = self.mixer.update(dt=self.dt, **mixer_inputs)

        # Module 6: Return Monitor
        monitor_inputs = {
            'Q_blood': mixer_outputs['Q_blood'],
            'Hct_out': mixer_outputs['Hct_out'],
            'T_out': mixer_outputs['T_out'],
            'C_NH3': mixer_outputs['C_NH3'],
            'C_lido': mixer_outputs['C_lido'],
            'C_urea': mixer_outputs['C_urea'],
            'air_volume': 0.0,  # Simplified for now
            'free_Hb': 5.0      # Normal level
        }
        monitor_outputs = self.return_monitor.update(dt=self.dt, **monitor_inputs)

        # Future module connections (commented out for now):
        # pump_inputs = {
        #     'Q_plasma': sep_outputs['Q_plasma'],
        #     'P_plasma': sep_outputs['P_plasma'],
        #     'T_plasma': sep_outputs['T_plasma'],
        #     'C_NH3_plasma': sep_outputs['C_NH3_plasma'],
        #     'C_lido_plasma': sep_outputs['C_lido_plasma'],
        #     'C_urea_plasma': sep_outputs['C_urea_plasma'],
        # }
        # pump_outputs = self.pump.update(dt=self.dt, **pump_inputs)
        #
        # bio_inputs = {
        #     'Q_plasma': pump_outputs['Q_plasma_controlled'],
        #     'P_plasma': pump_outputs['P_plasma_out'],
        #     'T_plasma': pump_outputs['T_plasma'],
        #     ...
        # }
        # bio_outputs = self.bioreactor.update(dt=self.dt, **bio_inputs)
        # ... continue chain through all modules

        # Collect all outputs for logging
        all_outputs = {
            'time': self.current_time,
            'separator': sep_outputs,
            'pump': pump_outputs,
            'bioreactor': bio_outputs,
            'sampler': sampler_outputs,
            'mixer': mixer_outputs,
            'return_monitor': monitor_outputs,
        }

        # Log data (flatten outputs for logging)
        log_data = {**sep_outputs}
        # Add pump outputs with prefix
        for key, value in pump_outputs.items():
            if key not in ['state', 'alarm_code']:  # Skip redundant state info
                log_data[f'pump_{key}'] = value
        # Add bioreactor outputs with prefix
        for key, value in bio_outputs.items():
            log_data[f'bio_{key}'] = value
        # Add sampler outputs with prefix
        for key, value in sampler_outputs.items():
            if key not in ['state', 'alarm_code']:  # Skip redundant state info
                log_data[f'sampler_{key}'] = value
        # Add mixer outputs with prefix to avoid conflicts
        for key, value in mixer_outputs.items():
            log_data[f'mixer_{key}'] = value
        # Add return monitor outputs with prefix
        for key, value in monitor_outputs.items():
            # Skip violations list for CSV logging
            if key != 'violations':
                log_data[f'monitor_{key}'] = value
        self.data_logger.log(self.current_time, log_data)

        # Store in history
        self.history.append(all_outputs)

        # Increment time
        self.current_time += self.dt

        return all_outputs

    def run(self, duration: float):
        """
        Run simulation for specified duration.

        Args:
            duration: Simulation time in minutes

        Raises:
            ValueError: If duration <= 0
        """
        if duration <= 0:
            raise ValueError("Duration must be positive")

        # Calculate number of steps
        steps = int(duration / self.dt)

        print(f"\nRunning {duration:.0f}-minute simulation...")
        print(f"Time step: {self.dt} min, Total steps: {steps}")

        # Run simulation loop
        for step_num in range(steps):
            self.step()

            # Print progress every 10%
            progress = (step_num + 1) / steps
            if (step_num + 1) % max(1, steps // 10) == 0:
                print(f"Progress: {progress*100:.0f}% ({self.current_time:.1f} min)")

        # Print summary
        print(f"\nSimulation complete: {self.current_time:.1f} minutes simulated")
        print(f"Total data points: {len(self.history)}")

        # Get final states
        final_outputs = self.get_current_outputs()
        if 'separator' in final_outputs:
            print(f"\nFinal separator state: {final_outputs['separator'].get('state_name', 'Unknown')}")
        if 'pump' in final_outputs:
            print(f"Final pump state: {final_outputs['pump'].get('state_name', 'Unknown')}")
            print(f"  Pump running: {final_outputs['pump'].get('pump_running', False)}")
        if 'bioreactor' in final_outputs:
            print(f"Final bioreactor state: {final_outputs['bioreactor'].get('state_name', 'Unknown')}")
            print(f"  NH3 clearance: {final_outputs['bioreactor'].get('NH3_clearance', 0.0):.1%}")
            print(f"  Lidocaine clearance: {final_outputs['bioreactor'].get('lido_clearance', 0.0):.1%}")
            print(f"  Cell viability: {final_outputs['bioreactor'].get('cell_viability', 0.0):.1%}")
        if 'mixer' in final_outputs:
            print(f"Final mixer state: {final_outputs['mixer'].get('state_name', 'Unknown')}")
        if 'return_monitor' in final_outputs:
            print(f"Final return monitor state: {final_outputs['return_monitor'].get('state_name', 'Unknown')}")
            print(f"  Return approved: {final_outputs['return_monitor'].get('return_approved', False)}")
            print(f"  Treatment success: {final_outputs['return_monitor'].get('treatment_success', False)}")

        return final_outputs

    def get_module_states(self) -> Dict[str, str]:
        """
        Get current state of all modules.

        Returns:
            Dict mapping module name to current state string
        """
        states = {}

        # Module 1: Separator
        if self.separator:
            states['Plasma Separator'] = self.separator.get_state_name()

        # Module 2: Pump Control
        if self.pump:
            states['Plasma Pump and Control'] = self.pump.get_state_name()

        if self.bioreactor is not None:
            states['Bioreactor System'] = self.bioreactor.get_state_name()
        else:
            states['Bioreactor System'] = 'NOT_IMPLEMENTED'

        if self.sampler is None:
            states['Sampler'] = 'NOT_IMPLEMENTED'
        else:
            states['Sampler'] = self.sampler.get_state_name()

        if self.mixer is None:
            states['Mixer'] = 'NOT_IMPLEMENTED'
        else:
            states['Mixer'] = self.mixer.get_state_name()

        if self.return_monitor is not None:
            states['Return Monitor'] = self.return_monitor.get_state_name()
        else:
            states['Return Monitor'] = 'NOT_IMPLEMENTED'

        return states

    def get_current_outputs(self) -> Dict[str, Any]:
        """
        Get latest outputs from all modules.

        Returns:
            Dict containing most recent outputs from all active modules
        """
        if not self.history:
            return {}

        return self.history[-1]

    def reset(self):
        """
        Reset simulation to initial state.

        Clears all data and resets modules to t=0.
        """
        # Reset time
        self.current_time = 0.0

        # Clear data
        self.history = []
        self.data_logger.clear()

        # Reset implemented modules
        if self.separator:
            self.separator.reset()
        if self.pump:
            self.pump.reset()
        if self.bioreactor:
            self.bioreactor.reset()
        if self.sampler:
            self.sampler.reset()
        if self.mixer:
            self.mixer.reset()
        if self.return_monitor:
            self.return_monitor.reset()

        print("Simulation reset to initial state")
