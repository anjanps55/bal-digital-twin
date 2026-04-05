"""
Bioreactor Module - Two-Compartment Mass Balance Implementation

Implements complete mass balance from BAL_Mass_Balance_Full.docx:
- CV1 (Plasma Compartment): Equations 16-20
- CV2 (Hepatocyte Compartment): Equations 21-24

This replaces the simplified demo mode with full ODE integration.
"""

from typing import Dict, Any
from modules.base_module import BaseModule
from config.constants import (
    BIOREACTOR_STATES,
    BIOREACTOR_INPUTS,
    BIOREACTOR_THRESHOLDS,
    BIOREACTOR_VOLUMES,
    MEMBRANE_TRANSPORT,
    HEPATOCYTE_KINETICS,
    BIOREACTOR_INITIAL
)


class BioreactorSystem(BaseModule):
    """
    Bioreactor Module with Two-Compartment Mass Balance
    
    Implements full membrane transport and hepatocyte metabolism:
    
    CV1 (Plasma Side):
        - Convective transport (in/out)
        - Diffusive transport across membrane
        - No reactions
        
    CV2 (Hepatocyte Side):
        - Diffusive transport across membrane
        - First-order metabolism (NH3 → Urea, Lido → MEGX → GX)
        - Cell viability affects reaction rates
    
    States:
        0 - STARTUP_CONDITIONING: Initial equilibration
        1 - NORMAL_OPERATION: Optimal treatment
        2 - DEGRADED_PERFORMANCE: Declining viability
        3 - CRITICAL_FAILURE: Minimal function
        4 - SHUTDOWN: Treatment complete
    """
    
    def __init__(self):
        """Initialize bioreactor with two-compartment model."""
        super().__init__("Bioreactor System")
        
        # Initial state
        self.state = BIOREACTOR_STATES['STARTUP_CONDITIONING']
        
        # Input parameters
        self.Q_plasma = 0.0
        self.P_plasma = 50.0
        self.T_plasma = 37.0
        self.C_NH3_in = BIOREACTOR_INPUTS['C_NH3_in_nominal']
        self.C_lido_in = BIOREACTOR_INPUTS['C_lido_in_nominal']
        self.C_urea_in = BIOREACTOR_INPUTS['C_urea_in_nominal']
        
        # Compartment volumes
        self.V_CV1 = BIOREACTOR_VOLUMES['V_CV1']
        self.V_CV2 = BIOREACTOR_VOLUMES['V_CV2']
        
        # Membrane parameters
        self.A_m = MEMBRANE_TRANSPORT['A_m']
        self.P_m_NH3 = MEMBRANE_TRANSPORT['P_m_NH3']
        self.P_m_urea = MEMBRANE_TRANSPORT['P_m_urea']
        self.P_m_lido = MEMBRANE_TRANSPORT['P_m_lido']
        self.P_m_MEGX = MEMBRANE_TRANSPORT['P_m_MEGX']
        self.P_m_GX = MEMBRANE_TRANSPORT['P_m_GX']

        # Reaction kinetics
        self.k1_NH3_base = HEPATOCYTE_KINETICS['k1_NH3_base']
        self.k1_lido_base = HEPATOCYTE_KINETICS['k1_lido_base']
        self.k2_MEGX_base = HEPATOCYTE_KINETICS['k2_MEGX_base']

        # Initialize compartment concentrations
        self.C_NH3_CV1 = self.C_NH3_in * BIOREACTOR_INITIAL['C_NH3_CV1_frac']
        self.C_NH3_CV2 = self.C_NH3_in * BIOREACTOR_INITIAL['C_NH3_CV2_frac']
        self.C_urea_CV1 = self.C_urea_in
        self.C_urea_CV2 = self.C_urea_in
        self.C_lido_CV1 = self.C_lido_in * BIOREACTOR_INITIAL['C_lido_CV1_frac']
        self.C_lido_CV2 = self.C_lido_in * BIOREACTOR_INITIAL['C_lido_CV2_frac']
        self.C_MEGX_CV1 = BIOREACTOR_INITIAL['C_MEGX_CV1']
        self.C_MEGX_CV2 = BIOREACTOR_INITIAL['C_MEGX_CV2']
        self.C_GX_CV1 = BIOREACTOR_INITIAL['C_GX_CV1']
        self.C_GX_CV2 = BIOREACTOR_INITIAL['C_GX_CV2']
        
        # Output concentrations (from CV1)
        self.C_NH3_out = self.C_NH3_CV1
        self.C_lido_out = self.C_lido_CV1
        self.C_urea_out = self.C_urea_CV1
        
        # Cell viability
        self.cell_viability = 1.0
        
        # Performance metrics
        self.NH3_clearance = 0.0
        self.lido_clearance = 0.0
    
    def update(self, dt: float = 1.0, **inputs) -> Dict[str, Any]:
        """Update bioreactor state using two-compartment mass balance."""
        # Update timing
        self.time_in_state += dt
        self.simulation_time += dt
        
        # Update inputs
        self._update_inputs(**inputs)
        
        # Perform two-compartment mass balance integration
        self._integrate_mass_balance(dt)
        
        # Update cell viability
        self._update_cell_viability(dt)
        
        # Calculate performance metrics
        self._calculate_performance()
        
        # Check state transitions
        self._check_state_transition()
        
        return self._get_outputs()
    
    def _update_inputs(self, **inputs):
        """Update input parameters."""
        self.Q_plasma = inputs.get('Q_plasma', 75.0)
        self.P_plasma = inputs.get('P_plasma', 50.0)
        self.T_plasma = inputs.get('T_plasma', 37.0)
        self.C_NH3_in = inputs.get('C_NH3', BIOREACTOR_INPUTS['C_NH3_in_nominal'])
        self.C_lido_in = inputs.get('C_lido', BIOREACTOR_INPUTS['C_lido_in_nominal'])
        self.C_urea_in = inputs.get('C_urea', BIOREACTOR_INPUTS['C_urea_in_nominal'])
    
    def _integrate_mass_balance(self, dt: float):
        """
        Integrate two-compartment mass balance ODEs.
        
        Implements Equations 16-24 from BAL_Mass_Balance_Full.docx
        Uses Forward Euler integration for simplicity.
        """
        # Reaction rate constants (adjusted for viability)
        k1_NH3 = self.k1_NH3_base * self.cell_viability
        k1_lido = self.k1_lido_base * self.cell_viability
        k2_MEGX = self.k2_MEGX_base * self.cell_viability

        # --- CV1 (Plasma Compartment) ---

        # Ammonia (Eq 16)
        flux_NH3 = self.P_m_NH3 * self.A_m * (self.C_NH3_CV1 - self.C_NH3_CV2)
        dC_NH3_CV1_dt = (self.Q_plasma / self.V_CV1) * (self.C_NH3_in - self.C_NH3_CV1) - \
                         (flux_NH3 / self.V_CV1)

        # Urea (Eq 17)
        flux_urea = self.P_m_urea * self.A_m * (self.C_urea_CV2 - self.C_urea_CV1)
        dC_urea_CV1_dt = flux_urea / self.V_CV1

        # Lidocaine (Eq 18)
        flux_lido = self.P_m_lido * self.A_m * (self.C_lido_CV1 - self.C_lido_CV2)
        dC_lido_CV1_dt = (self.Q_plasma / self.V_CV1) * (self.C_lido_in - self.C_lido_CV1) - \
                          (flux_lido / self.V_CV1)

        # MEGX (Eq 19 — product diffuses from CV2 to CV1)
        flux_MEGX = self.P_m_MEGX * self.A_m * (self.C_MEGX_CV2 - self.C_MEGX_CV1)
        dC_MEGX_CV1_dt = flux_MEGX / self.V_CV1

        # GX (secondary metabolite — diffuses from CV2 to CV1)
        flux_GX = self.P_m_GX * self.A_m * (self.C_GX_CV2 - self.C_GX_CV1)
        dC_GX_CV1_dt = flux_GX / self.V_CV1

        # --- CV2 (Hepatocyte Compartment) ---

        # Ammonia (Eq 21a — first-order approximation)
        dC_NH3_CV2_dt = (flux_NH3 / self.V_CV2) - k1_NH3 * self.C_NH3_CV2

        # Urea (Eq 22 — with 1/2 stoichiometry: 2 NH3 → 1 urea)
        urea_generation = HEPATOCYTE_KINETICS['urea_stoich'] * k1_NH3 * self.C_NH3_CV2
        dC_urea_CV2_dt = urea_generation - (flux_urea / self.V_CV2)

        # Lidocaine (Eq 23a)
        dC_lido_CV2_dt = (flux_lido / self.V_CV2) - k1_lido * self.C_lido_CV2

        # MEGX (1:1 from lido, consumed by secondary metabolism to GX)
        MEGX_generation = HEPATOCYTE_KINETICS['MEGX_stoich'] * k1_lido * self.C_lido_CV2
        MEGX_consumption = k2_MEGX * self.C_MEGX_CV2
        dC_MEGX_CV2_dt = MEGX_generation - MEGX_consumption - (flux_MEGX / self.V_CV2)

        # GX (1:1 from MEGX — secondary CYP450 N-dealkylation)
        GX_generation = HEPATOCYTE_KINETICS['GX_stoich'] * k2_MEGX * self.C_MEGX_CV2
        dC_GX_CV2_dt = GX_generation - (flux_GX / self.V_CV2)

        # --- Forward Euler Integration ---

        self.C_NH3_CV1 += dC_NH3_CV1_dt * dt
        self.C_urea_CV1 += dC_urea_CV1_dt * dt
        self.C_lido_CV1 += dC_lido_CV1_dt * dt
        self.C_MEGX_CV1 += dC_MEGX_CV1_dt * dt
        self.C_GX_CV1 += dC_GX_CV1_dt * dt

        self.C_NH3_CV2 += dC_NH3_CV2_dt * dt
        self.C_urea_CV2 += dC_urea_CV2_dt * dt
        self.C_lido_CV2 += dC_lido_CV2_dt * dt
        self.C_MEGX_CV2 += dC_MEGX_CV2_dt * dt
        self.C_GX_CV2 += dC_GX_CV2_dt * dt

        # Ensure physical bounds (concentrations can't be negative)
        self.C_NH3_CV1 = max(0.0, self.C_NH3_CV1)
        self.C_NH3_CV2 = max(0.0, self.C_NH3_CV2)
        self.C_urea_CV1 = max(0.0, self.C_urea_CV1)
        self.C_urea_CV2 = max(0.0, self.C_urea_CV2)
        self.C_lido_CV1 = max(0.0, self.C_lido_CV1)
        self.C_lido_CV2 = max(0.0, self.C_lido_CV2)
        self.C_MEGX_CV1 = max(0.0, self.C_MEGX_CV1)
        self.C_MEGX_CV2 = max(0.0, self.C_MEGX_CV2)
        self.C_GX_CV1 = max(0.0, self.C_GX_CV1)
        self.C_GX_CV2 = max(0.0, self.C_GX_CV2)
        
        # Output concentrations (what exits CV1 to mixer)
        self.C_NH3_out = self.C_NH3_CV1
        self.C_lido_out = self.C_lido_CV1
        self.C_urea_out = self.C_urea_CV1
    
    def _update_cell_viability(self, dt: float):
        """Update cell viability with exponential decay."""
        decay_rate = BIOREACTOR_THRESHOLDS['k_cell_decay']
        self.cell_viability *= (1 - decay_rate * dt)
        self.cell_viability = max(0.1, self.cell_viability)
    
    def _calculate_performance(self):
        """Calculate clearance efficiency."""
        if self.C_NH3_in > 0:
            self.NH3_clearance = (self.C_NH3_in - self.C_NH3_out) / self.C_NH3_in
        else:
            self.NH3_clearance = 0.0
        
        if self.C_lido_in > 0:
            self.lido_clearance = (self.C_lido_in - self.C_lido_out) / self.C_lido_in
        else:
            self.lido_clearance = 0.0
    
    def _check_state_transition(self):
        """Update state based on performance."""
        current = self.state
        
        if current == BIOREACTOR_STATES['STARTUP_CONDITIONING']:
            if self.time_in_state >= BIOREACTOR_THRESHOLDS['conditioning_duration']:
                self.state = BIOREACTOR_STATES['NORMAL_OPERATION']
                self.time_in_state = 0.0
        
        elif current == BIOREACTOR_STATES['NORMAL_OPERATION']:
            if self.cell_viability < BIOREACTOR_THRESHOLDS['viability_critical']:
                self.state = BIOREACTOR_STATES['CRITICAL_FAILURE']
            elif self.cell_viability < BIOREACTOR_THRESHOLDS['viability_degraded']:
                self.state = BIOREACTOR_STATES['DEGRADED_PERFORMANCE']
        
        elif current == BIOREACTOR_STATES['DEGRADED_PERFORMANCE']:
            if self.cell_viability >= BIOREACTOR_THRESHOLDS['viability_degraded']:
                self.state = BIOREACTOR_STATES['NORMAL_OPERATION']
            elif self.cell_viability < BIOREACTOR_THRESHOLDS['viability_critical']:
                self.state = BIOREACTOR_STATES['CRITICAL_FAILURE']
    
    def _get_outputs(self) -> Dict[str, Any]:
        """Package outputs."""
        return {
            'Q_plasma': self.Q_plasma,
            'P_plasma': self.P_plasma,
            'T_plasma': self.T_plasma,
            'C_NH3': self.C_NH3_out,
            'C_lido': self.C_lido_out,
            'C_urea': self.C_urea_out,
            'C_NH3_CV1': self.C_NH3_CV1,
            'C_NH3_CV2': self.C_NH3_CV2,
            'C_urea_CV1': self.C_urea_CV1,
            'C_urea_CV2': self.C_urea_CV2,
            'C_lido_CV1': self.C_lido_CV1,
            'C_lido_CV2': self.C_lido_CV2,
            'C_MEGX_CV1': self.C_MEGX_CV1,
            'C_MEGX_CV2': self.C_MEGX_CV2,
            'C_GX_CV1': self.C_GX_CV1,
            'C_GX_CV2': self.C_GX_CV2,
            'cell_viability': self.cell_viability,
            'NH3_clearance': self.NH3_clearance,
            'lido_clearance': self.lido_clearance,
            'state': self.state,
            'state_name': self.get_state_name(),
            'alarm_code': self._get_alarm_code(),
            'treatment_time': self.simulation_time
        }
    
    def _get_alarm_code(self) -> int:
        """Return alarm code based on state."""
        if self.state == BIOREACTOR_STATES['CRITICAL_FAILURE']:
            return 2  # Critical
        elif self.state == BIOREACTOR_STATES['DEGRADED_PERFORMANCE']:
            return 1  # Warning
        else:
            return 0  # Normal
    
    def get_state_name(self) -> str:
        """Return human-readable state name."""
        state_names = {
            0: 'STARTUP_CONDITIONING',
            1: 'NORMAL_OPERATION',
            2: 'DEGRADED_PERFORMANCE',
            3: 'CRITICAL_FAILURE',
            4: 'SHUTDOWN'
        }
        return state_names.get(self.state, 'UNKNOWN')

    @property
    def treatment_time(self):
        """Alias for simulation_time for backward compatibility."""
        return self.simulation_time

