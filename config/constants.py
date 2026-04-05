"""
BAL Digital Twin - Design Parameters and Constants
Based on Plasmaflo OP-08W specifications and team design decisions
"""

# ============= MODULE 1: PLASMA SEPARATOR =============

# Separator States
SEPARATOR_STATES = {
    0: 'STARTUP_PRIMING',
    1: 'NORMAL_OPERATION',
    2: 'DEGRADED_PERFORMANCE',
    3: 'MEMBRANE_FOULED',
    4: 'MEMBRANE_CLOTTED',
    5: 'MEMBRANE_FAILURE'
}

# Separator Input Parameters (Section 3.1)
SEPARATOR_INPUTS = {
    'Q_blood_nominal': 150,        # mL/min
    'Q_blood_min': 100,
    'Q_blood_max': 200,
    'Hct_in_nominal': 0.32,        # fraction
    'Hct_in_min': 0.20,
    'Hct_in_max': 0.50,
    'T_in_nominal': 37.0,          # °C
    'T_in_min': 36.0,
    'T_in_max': 37.5,
    'P_blood_in_nominal': 100,     # mmHg
    'P_blood_in_min': 80,
    'P_blood_in_max': 150,
    'C_NH3_in_nominal': 90,        # µmol/L
    'C_NH3_in_min': 50,
    'C_NH3_in_max': 500,
    'C_lido_in_nominal': 21,       # µmol/L
    'C_lido_in_min': 10,
    'C_lido_in_max': 30,
    'C_urea_in_nominal': 5.0,      # mmol/L
    'C_urea_in_min': 2.5,
    'C_urea_in_max': 15.0,
}

# Separator Output Parameters (Section 4.1)
SEPARATOR_OUTPUTS = {
    'Q_plasma_nominal': 102,       # mL/min (calculated from Q_blood × (1-Hct) × eta_sep)
    'Q_plasma_min': 50,
    'Q_plasma_max': 160,
    'Q_cells_nominal': 48,         # mL/min
    'P_plasma_nominal': 50,        # mmHg
    'P_plasma_min': 30,
    'P_plasma_max': 80,
    'T_plasma_nominal': 37.0,      # °C (same as input)
    'FF_nominal': 0.25,            # Filtration fraction target
    'Hct_post_nominal': 0.45,      # Post-separation hematocrit
}

# Separator Thresholds (Sections 6.2 and 9)
SEPARATOR_THRESHOLDS = {
    'TMP_normal_max': 40,          # mmHg - Normal operation maximum
    'TMP_warning': 50,             # mmHg - Warning threshold
    'TMP_critical': 60,            # mmHg - Critical threshold
    'TMP_failure': 100,            # mmHg - Membrane failure threshold
    'TMP_clotted': 80,             # mmHg - Clotting threshold
    'eta_sep_normal': 0.95,        # Separation efficiency normal threshold
    'eta_sep_degraded': 0.85,      # Separation efficiency degraded threshold
    'FF_target': 0.25,             # Target filtration fraction
    'FF_max': 0.30,                # Maximum acceptable FF
    'FF_critical': 0.35,           # Critical FF threshold
    'Hct_post_max': 0.55,          # Maximum post-separation hematocrit
    'P_oncotic': 25,               # mmHg - Oncotic pressure constant
    'Q_blood_drop_threshold': 0.30, # 30% drop threshold for clotting detection
    'degraded_duration': 5,        # minutes - sustained degraded condition time
    'startup_duration': 2,         # minutes - minimum startup priming time
}

# ============= MODULE 2: PUMP CONTROL =============

PUMP_STATES = {
    'OFF': 0,
    'STARTUP_PRIMING': 1,
    'NORMAL_OPERATION': 2,
    'LOW_FLOW_WARNING': 3,
    'HIGH_FLOW_WARNING': 4,
    'HIGH_PRESSURE_ALARM': 5,
    'LOW_PRESSURE_ALARM': 6,
    'AIR_IN_LINE_DETECTED': 7,
    'LEAK_DETECTED': 8,
    'TEMPERATURE_ALARM': 9,
    'OPERATOR_PAUSE': 10,
    'EMERGENCY_STOP': 11
}

PUMP_INPUTS = {
    # From separator
    'Q_plasma_nominal': 75,         # mL/min target flow (per unit)
    'P_plasma_nominal': 50,         # mmHg inlet pressure
    'T_plasma_nominal': 37.0,       # °C

    # Operator setpoints
    'Q_target': 75,                 # mL/min desired flow (per unit)
    'P_max_setpoint': 120,          # mmHg max pressure
    'P_min_setpoint': 40,           # mmHg min pressure
}

PUMP_THRESHOLDS = {
    # Flow limits (per unit, flat-disc design)
    'Q_target': 75,                 # mL/min - target flow rate per unit
    'Q_tolerance': 10,              # mL/min - acceptable deviation
    'Q_warning_low': 60,            # mL/min - low flow warning
    'Q_critical_low': 50,           # mL/min - below this = alarm
    'Q_warning_high': 90,           # mL/min - high flow warning
    'Q_critical_high': 100,         # mL/min - above this = alarm

    # Pressure limits
    'P_normal_min': 40,             # mmHg - minimum normal pressure
    'P_normal_max': 100,            # mmHg - maximum normal pressure
    'P_critical_high': 120,         # mmHg - emergency shutdown
    'P_critical_low': 30,           # mmHg - leak indication

    # Temperature limits
    'T_min': 36.0,                  # °C - minimum safe temperature
    'T_max': 38.0,                  # °C - maximum safe temperature
    'T_critical_low': 35.0,         # °C - emergency low
    'T_critical_high': 39.0,        # °C - emergency high

    # Air detection
    'air_volume_max': 0.1,          # mL - maximum acceptable air
    'air_volume_critical': 0.5,     # mL - immediate stop

    # Timing
    'priming_duration': 2.0,        # minutes - startup time
    'ramp_rate': 5.0,               # mL/min per minute - flow increase rate
}

PUMP_OUTPUTS = {
    'Q_controlled': 75,             # mL/min - actual controlled flow (per unit)
    'P_out': 50,                    # mmHg - outlet pressure
    'pump_running': False,          # Boolean - pump status
}

# ============= MODULE 5: MIXER =============

MIXER_STATES = {
    'IDLE_STANDBY': 0,
    'STARTUP_PRIMING': 1,
    'NORMAL_MIXING': 2,
    'IMBALANCED_MIXING': 3,
    'INCOMPLETE_MIXING': 4,
    'SINGLE_STREAM_FAILURE': 5,
    'HEMOLYSIS_DETECTED': 6,
    'CLOTTING_BLOCKAGE': 7,
    'AIR_ENTRAINMENT': 8,
    'MIXER_FAILURE': 9
}

MIXER_INPUTS = {
    # From bioreactor (treated plasma)
    'Q_plasma_nominal': 75,         # mL/min (per unit)
    'Q_plasma_min': 40,
    'Q_plasma_max': 120,
    'P_plasma_nominal': 80,         # mmHg

    # From separator (cellular stream)
    'Q_cells_nominal': 120,         # mL/min
    'Q_cells_min': 75,
    'Q_cells_max': 150,
    'P_cells_nominal': 90,          # mmHg

    # Temperature
    'T_nominal': 37.0,              # °C
    'T_min': 36.0,
    'T_max': 37.5,
}

MIXER_THRESHOLDS = {
    # Flow balance thresholds
    'flow_ratio_target': 0.25,      # Q_plasma / Q_blood (same as FF)
    'flow_ratio_tolerance': 0.05,   # ± tolerance for normal mixing
    'flow_ratio_critical': 0.10,    # Beyond this = imbalanced

    # Hematocrit thresholds
    'Hct_target': 0.32,             # Target hematocrit
    'Hct_min': 0.25,                # Minimum acceptable
    'Hct_max': 0.45,                # Maximum acceptable

    # Pressure thresholds
    'P_output_min': 70,             # mmHg - minimum output pressure
    'P_output_max': 120,            # mmHg - maximum output pressure
    'P_drop_normal': 10,            # mmHg - normal pressure drop across mixer
    'P_drop_blockage': 25,          # mmHg - indicates blockage

    # Mixing quality
    'mixing_efficiency_normal': 0.95,  # >95% = well mixed
    'mixing_efficiency_poor': 0.85,    # <85% = incomplete mixing

    # Hemolysis indicator (simplified)
    'shear_rate_max': 3000,         # s^-1 - above this risks hemolysis

    # Air detection
    'air_volume_threshold': 0.5,    # mL - maximum acceptable air

    # Timing
    'priming_duration': 2.0,        # minutes - time to establish stable flow
}

MIXER_OUTPUTS = {
    'Q_blood_nominal': 150,         # mL/min - recombined blood flow
    'Hct_out_nominal': 0.32,        # Target output hematocrit
    'P_out_nominal': 85,            # mmHg - output pressure
}

# ============= MODULE 6: RETURN MONITOR =============

RETURN_MONITOR_STATES = {
    'MONITORING_TESTING': 0,
    'SAFE_TO_RETURN': 1,
    'ELEVATED_AMMONIA_WARNING': 2,
    'ELEVATED_LIDOCAINE_WARNING': 3,
    'CRITICAL_TOXICITY_DETECTED': 4,
    'TEMPERATURE_ALARM': 5,
    'AIR_DETECTED': 6,
    'HEMOLYSIS_DETECTED': 7,
    'ABNORMAL_HEMATOCRIT': 8,
    'UNSAFE_FOR_RETURN': 9,
    'EMERGENCY_STOP_NO_RETURN': 10
}

RETURN_MONITOR_INPUTS = {
    # From mixer
    'Q_blood_nominal': 150,         # mL/min
    'Hct_nominal': 0.32,            # fraction
    'T_nominal': 37.0,              # °C

    # Concentrations (from treated blood)
    'C_NH3_nominal': 35,            # µmol/L (target after treatment)
    'C_lido_nominal': 7,            # µmol/L (target after treatment)
    'C_urea_nominal': 8.0,          # mmol/L (should increase)
}

RETURN_MONITOR_THRESHOLDS = {
    # Ammonia safety levels
    'C_NH3_safe': 50,               # µmol/L - maximum safe level
    'C_NH3_target': 35,             # µmol/L - target level
    'C_NH3_warning': 45,            # µmol/L - warning threshold
    'C_NH3_critical': 60,           # µmol/L - critical, cannot return

    # Lidocaine safety levels
    'C_lido_safe': 12,              # µmol/L - maximum safe level
    'C_lido_target': 7,             # µmol/L - target level
    'C_lido_warning': 11,           # µmol/L - warning threshold
    'C_lido_critical': 15,          # µmol/L - critical, cannot return

    # Temperature safety
    'T_min': 36.0,                  # °C - minimum safe
    'T_max': 37.5,                  # °C - maximum safe
    'T_critical_low': 35.0,         # °C - critically low
    'T_critical_high': 38.0,        # °C - critically high

    # Hematocrit safety
    'Hct_min': 0.25,                # Minimum acceptable
    'Hct_max': 0.45,                # Maximum acceptable
    'Hct_target': 0.32,             # Target value
    'Hct_critical_low': 0.20,       # Critically low
    'Hct_critical_high': 0.50,      # Critically high

    # Hemolysis indicator (free hemoglobin)
    'free_Hb_normal': 10,           # mg/dL - normal level
    'free_Hb_warning': 50,          # mg/dL - warning level
    'free_Hb_critical': 100,        # mg/dL - critical hemolysis

    # Air detection
    'air_volume_max': 0.1,          # mL - maximum acceptable air
    'air_volume_critical': 0.5,     # mL - critical air embolism risk

    # Urea validation (should increase if ammonia converted)
    'C_urea_min_increase': 1.0,     # mmol/L - minimum increase expected

    # Treatment success criteria
    'treatment_success_NH3': 50,    # µmol/L - must be below this
    'treatment_success_lido': 12,   # µmol/L - must be below this (safe range <15)
}

RETURN_MONITOR_OUTPUTS = {
    'return_approved': False,       # Boolean - safe to return?
    'treatment_success': False,     # Boolean - treatment successful?
}

# ============= MODULE 3: BIOREACTOR =============

BIOREACTOR_STATES = {
    'STARTUP_CONDITIONING': 0,
    'NORMAL_OPERATION': 1,
    'DEGRADED_PERFORMANCE': 2,
    'CRITICAL_FAILURE': 3,
    'SHUTDOWN_POST_TREATMENT': 4
}

BIOREACTOR_INPUTS = {
    # From pump (when implemented) or separator
    'Q_plasma_nominal': 75,         # mL/min (per unit)
    'P_plasma_nominal': 80,         # mmHg
    'T_plasma_nominal': 37.0,       # °C

    # Inlet concentrations (untreated)
    'C_NH3_in_nominal': 90,         # µmol/L
    'C_lido_in_nominal': 21,        # µmol/L
    'C_urea_in_nominal': 5.0,       # mmol/L

    # Reactor design parameters (flat-disc cylindrical cartridge, per unit)
    'membrane_area': 314,           # cm² — flat disc (π × 10²)
    'reactor_volume': 7140,         # mL (CV1 + CV2 = 3570 + 3570)
    'cell_count': 3.6e9,            # cells (3.6 × 10⁹ per unit)
}

BIOREACTOR_THRESHOLDS = {
    # Treatment targets (from your project docs)
    'C_NH3_target': 35,             # µmol/L - target outlet
    'C_lido_target': 7,             # µmol/L - target outlet
    'C_urea_target': 8.0,           # mmol/L - should increase

    # Performance thresholds
    'NH3_clearance_normal': 0.50,   # >50% reduction = normal
    'NH3_clearance_degraded': 0.30, # 30-50% = degraded
    'lido_clearance_normal': 0.60,  # >60% reduction = normal
    'lido_clearance_degraded': 0.40,# 40-60% = degraded

    # Cell viability (affects performance)
    'viability_normal': 0.80,       # >80% = normal
    'viability_degraded': 0.60,     # 60-80% = degraded
    'viability_critical': 0.40,     # <40% = critical

    # Conversion rates (simplified - per minute)
    'k_NH3_to_urea': 0.15,         # NH₃ conversion rate (1.5%/min)
    'k_lido_metabolism': 0.020,     # Lidocaine metabolism rate (2%/min)
    'k_cell_decay': 0.0001,         # Cell decay rate (0.01%/min)

    # Temperature and oxygen (monitored but simplified)
    'T_min': 36.5,                  # °C
    'T_max': 37.5,                  # °C
    'DO_min': 25,                   # mmHg - minimum dissolved oxygen

    # Timing
    'conditioning_duration': 5.0,   # minutes - startup period
    'treatment_duration_max': 360,  # minutes - 6 hours max
}

BIOREACTOR_OUTPUTS = {
    # Target outlet concentrations
    'C_NH3_out_target': 35,         # µmol/L
    'C_lido_out_target': 7,         # µmol/L
    'C_urea_out_target': 8.0,       # mmol/L
}

# ============= MODULE 4: SAMPLER =============

SAMPLER_STATES = {
    'IDLE_STANDBY': 0,
    'SAMPLING_ACTIVE': 1,
    'SAMPLE_COLLECTED': 2,
    'SAMPLING_FAILED': 3,
    'PURGE_CLEANING': 4
}

SAMPLER_THRESHOLDS = {
    'sample_volume_target': 5.0,      # mL - target sample volume
    'sample_volume_min': 2.0,         # mL - minimum acceptable
    'sampling_duration_max': 2.0,     # minutes - max time to collect
    'P_min_for_sampling': 50,         # mmHg - minimum pressure needed
    'purge_duration': 1.0,            # minutes - purge time
    'auto_sample_interval': 30.0,     # minutes - automatic sampling interval
}

# ============= BIOREACTOR: TWO-COMPARTMENT MASS BALANCE PARAMETERS =============

# Control Volume Sizes (flat-disc cylindrical cartridge, 35×20 cm, per unit)
BIOREACTOR_VOLUMES = {
    'V_CV1': 3570.0,             # mL - Plasma compartment volume (per unit)
    'V_CV2': 3570.0,             # mL - Hepatocyte compartment volume (per unit)
}

# Membrane Transport Parameters (from BAL_Mass_Balance_Full.docx Section 2.3)
MEMBRANE_TRANSPORT = {
    # Membrane area — flat polysulfone disc (π × 10² cm²) per unit
    'A_m': 314.0,    # cm² - Flat disc membrane area per unit

    # Permeability coefficients (cm/min)
    # True literature values for polysulfone membrane (no scaling tricks)
    'P_m_NH3': 0.006,   # cm/min
    'P_m_urea': 0.006,  # cm/min
    'P_m_lido': 0.003,  # cm/min — updated from final design document
    'P_m_MEGX': 0.0048, # cm/min
    'P_m_GX': 0.0044,   # cm/min
}

# Hepatocyte Reaction Kinetics (from Section 3.5)
HEPATOCYTE_KINETICS = {
    # NH3 removal rate: 21.7 µg/10⁶ cells/day (porcine hepatocytes)
    'k1_NH3_base': 1.0,        # 1/min - First-order rate constant (base)

    # Lidocaine: ~80% of urea cycle rate (approximate from CYP450 data)
    'k1_lido_base': 0.85,       # 1/min - Lido → MEGX (CYP3A4 N-deethylation)

    # MEGX → GX: secondary CYP450 N-dealkylation, ~60% of primary rate
    'k2_MEGX_base': 0.50,       # 1/min - MEGX → GX conversion rate

    # Stoichiometry
    'urea_stoich': 0.5,          # 2 NH3 → 1 urea (factor of 1/2)
    'MEGX_stoich': 1.0,          # 1:1 lidocaine → MEGX
    'GX_stoich': 1.0,            # 1:1 MEGX → GX
}

# Initial Conditions for Compartments
BIOREACTOR_INITIAL = {
    # CV1 starts at inlet concentrations
    'C_NH3_CV1_frac': 1.0,       # Fraction of inlet
    'C_lido_CV1_frac': 1.0,
    'C_urea_CV1_frac': 1.0,
    'C_MEGX_CV1': 0.0,           # µmol/L - Initially zero
    'C_GX_CV1': 0.0,             # µmol/L - Initially zero

    # CV2 starts at ~50% of inlet (equilibration assumption)
    'C_NH3_CV2_frac': 0.5,
    'C_lido_CV2_frac': 0.5,
    'C_urea_CV2_frac': 1.0,
    'C_MEGX_CV2': 0.0,
    'C_GX_CV2': 0.0,             # µmol/L - Initially zero
}

