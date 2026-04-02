"""
BAL Digital Twin — Streamlit Dashboard
Interactive simulation and monitoring for the Bioartificial Liver Support Device.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import copy
import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components

from simulation.engine import SimulationEngine
from adaptive_controller import AdaptiveBALController
import config.constants as constants

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BAL Digital Twin",
    page_icon="\U0001fac0",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme / CSS
# ---------------------------------------------------------------------------
NAVY = "#1e3a5f"
INDIGO = "#6366f1"
TEAL = "#0d9488"
GREEN = "#10b981"
AMBER = "#f59e0b"
RED = "#ef4444"
BG = "#f0f4f8"
CARD = "#ffffff"
GRAY = "#6b7280"

def inject_css():
    st.markdown(
        f"""
        <style>
        /* page background */
        .stApp {{background-color: {BG};}}

        /* metric cards */
        [data-testid="stMetric"] {{
            background: {CARD};
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        [data-testid="stMetricValue"] {{font-size: 1.5rem !important;}}

        /* sidebar */
        section[data-testid="stSidebar"] {{background: #e8eef4;}}
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{color: {NAVY};}}

        /* tab labels */
        .stTabs [data-baseweb="tab"] {{color: {NAVY}; font-weight: 600;}}

        /* hide streamlit footer */
        footer {{visibility: hidden;}}

        /* pipeline card */
        .mod-card {{
            border-radius: 6px;
            padding: 10px 6px;
            text-align: center;
            min-height: 80px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .mod-name {{font-size: 0.7rem; color: {GRAY}; text-transform: uppercase; letter-spacing: 0.5px;}}
        .mod-state {{font-size: 0.8rem; font-weight: 600; margin-top: 4px;}}

        /* flow arrow */
        .flow-arrow {{
            display: flex; align-items: center; justify-content: center;
            font-size: 1.4rem; color: {GRAY}; padding-top: 18px;
        }}

        /* sidebar config buttons */
        .cfg-btn {{
            display: flex; align-items: center; gap: 10px;
            background: {CARD}; border: 1px solid #d1d5db; border-radius: 8px;
            padding: 10px 14px; margin-bottom: 6px; cursor: pointer;
            transition: border-color 0.15s, box-shadow 0.15s;
        }}
        .cfg-btn:hover {{border-color: {NAVY}; box-shadow: 0 0 0 1px {NAVY};}}
        .cfg-icon {{font-size: 1.3rem; line-height: 1;}}
        .cfg-body {{flex: 1; min-width: 0;}}
        .cfg-title {{font-size: 0.82rem; font-weight: 600; color: {NAVY};}}
        .cfg-sub {{font-size: 0.72rem; color: {GRAY}; line-height: 1.3; margin-top: 1px;
                   white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}}
        .cfg-arrow {{color: #d1d5db; font-size: 0.9rem;}}

        /* Make edit-config buttons compact & link-like in sidebar */
        section[data-testid="stSidebar"] button[kind="secondary"] {{
            font-size: 0.75rem !important;
            padding: 4px 0 !important;
            height: auto !important;
            min-height: 0 !important;
            color: {NAVY} !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            text-decoration: underline !important;
            text-underline-offset: 2px !important;
        }}
        section[data-testid="stSidebar"] button[kind="secondary"]:hover {{
            color: {INDIGO} !important;
            background: transparent !important;
        }}

        /* Keep primary button prominent */
        section[data-testid="stSidebar"] button[kind="primary"] {{
            margin-top: 4px;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            padding: 10px 0 !important;
            border-radius: 8px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------
PRESETS = {
    "Standard Adult": {
        "NH3": 90.0, "lido": 21.0, "urea": 5.0,
        "Q_blood": 150.0, "Hct": 0.32, "Q_target": 30.0, "duration": 60,
    },
    "Severe Case": {
        "NH3": 200.0, "lido": 35.0, "urea": 3.0,
        "Q_blood": 150.0, "Hct": 0.30, "Q_target": 40.0, "duration": 120,
    },
    "Pediatric Patient": {
        "NH3": 110.0, "lido": 25.0, "urea": 4.0,
        "Q_blood": 75.0, "Hct": 0.35, "Q_target": 20.0, "duration": 90,
    },
    "Mild Case": {
        "NH3": 60.0, "lido": 15.0, "urea": 6.0,
        "Q_blood": 150.0, "Hct": 0.34, "Q_target": 25.0, "duration": 45,
    },
    "Custom": {
        "NH3": 90.0, "lido": 21.0, "urea": 5.0,
        "Q_blood": 150.0, "Hct": 0.32, "Q_target": 30.0, "duration": 60,
    },
}


# ---------------------------------------------------------------------------
# Session-state defaults for dialogs
# ---------------------------------------------------------------------------
_PATIENT_DEFAULTS = {
    "NH3": 90.0, "lido": 21.0, "urea": 5.0,
    "Q_blood": 150.0, "Hct": 0.32,
}

_BIO_DEFAULTS = {
    "V_CV1": 100.0, "V_CV2": 100.0, "A_m": 10000.0,
    "P_m_NH3": 0.006, "P_m_urea": 0.006, "P_m_lido": 0.0042,
    "P_m_MEGX": 0.0048, "P_m_GX": 0.0044,
    "k1_NH3": 1.0, "k1_lido": 0.85, "k2_MEGX": 0.50, "k_decay": 0.0001,
}


def _init_defaults():
    """Seed session state on first load."""
    for k, v in _PATIENT_DEFAULTS.items():
        if f"_pt_{k}" not in st.session_state:
            st.session_state[f"_pt_{k}"] = v
    for k, v in _BIO_DEFAULTS.items():
        if f"_bio_{k}" not in st.session_state:
            st.session_state[f"_bio_{k}"] = v


# ---------------------------------------------------------------------------
# Patient Condition dialog
# ---------------------------------------------------------------------------
@st.dialog("Patient Condition", width="large")
def _patient_dialog():
    st.markdown(
        f"<p style='color:{GRAY};margin-top:-8px'>"
        "Set inlet toxin concentrations and blood parameters for the patient.</p>",
        unsafe_allow_html=True,
    )

    # --- Toxin levels ---
    st.markdown("#### Toxin Concentrations")
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        nh3 = st.number_input(
            "NH\u2083 (\u00b5mol/L)", 20.0, 500.0,
            value=st.session_state["_pt_NH3"], step=5.0,
            help="Normal < 35 \u00b5mol/L")
    with tc2:
        lido = st.number_input(
            "Lidocaine (\u00b5mol/L)", 5.0, 100.0,
            value=st.session_state["_pt_lido"], step=1.0,
            help="Normal < 10 \u00b5mol/L")
    with tc3:
        urea = st.number_input(
            "Urea (mmol/L)", 1.0, 30.0,
            value=st.session_state["_pt_urea"], step=0.5)

    # severity badge
    if nh3 >= 150:
        sev, sev_c = "CRITICAL", RED
    elif nh3 >= 80:
        sev, sev_c = "SEVERE", AMBER
    elif nh3 >= 35:
        sev, sev_c = "ELEVATED", "#d97706"
    else:
        sev, sev_c = "NORMAL", GREEN
    st.markdown(
        f"<div style='display:inline-block;background:{sev_c}18;color:{sev_c};"
        f"font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:10px;"
        f"border:1px solid {sev_c}40;margin-top:2px'>NH\u2083 severity: {sev}</div>",
        unsafe_allow_html=True,
    )

    # --- Blood parameters ---
    st.markdown("#### Blood Parameters")
    bc1, bc2 = st.columns(2)
    with bc1:
        q_blood = st.number_input(
            "Blood Flow (mL/min)", 50.0, 300.0,
            value=st.session_state["_pt_Q_blood"], step=5.0)
    with bc2:
        hct = st.number_input(
            "Hematocrit", 0.15, 0.65,
            value=st.session_state["_pt_Hct"], step=0.01, format="%.2f")

    # --- Action buttons ---
    st.markdown("")
    _, b2, b3 = st.columns([2, 1, 1])
    with b2:
        if st.button("Reset Defaults", key="_pt_reset", use_container_width=True):
            for k, v in _PATIENT_DEFAULTS.items():
                st.session_state[f"_pt_{k}"] = v
            st.rerun()
    with b3:
        if st.button("Apply", type="primary", key="_pt_apply", use_container_width=True):
            st.session_state["_pt_NH3"] = nh3
            st.session_state["_pt_lido"] = lido
            st.session_state["_pt_urea"] = urea
            st.session_state["_pt_Q_blood"] = q_blood
            st.session_state["_pt_Hct"] = hct
            st.rerun()


# ---------------------------------------------------------------------------
# Bioreactor Configuration dialog
# ---------------------------------------------------------------------------
@st.dialog("Bioreactor Configuration", width="large")
def _bioreactor_dialog():
    st.markdown(
        f"<p style='color:{GRAY};margin-top:-8px'>Adjust the two-compartment bioreactor "
        "geometry, membrane transport, and hepatocyte kinetics.</p>",
        unsafe_allow_html=True,
    )

    # --- Geometry ---
    st.markdown("#### Reactor Geometry")
    gc1, gc2, gc3 = st.columns(3)
    with gc1:
        v1 = st.number_input("CV1 \u2014 Plasma (mL)", 10.0, 500.0,
                              value=st.session_state["_bio_V_CV1"], step=10.0)
    with gc2:
        v2 = st.number_input("CV2 \u2014 Hepatocyte (mL)", 10.0, 500.0,
                              value=st.session_state["_bio_V_CV2"], step=10.0)
    with gc3:
        am = st.number_input("Membrane Area (cm\u00b2)", 100.0, 50000.0,
                              value=st.session_state["_bio_A_m"], step=500.0,
                              help="Polysulfone flat-disc membrane surface area")

    # --- Membrane permeabilities ---
    st.markdown("#### Membrane Permeability")
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        pm_nh3 = st.number_input("P_m NH\u2083", 0.0001, 0.1,
                                  value=st.session_state["_bio_P_m_NH3"],
                                  step=0.001, format="%.4f")
    with mc2:
        pm_urea = st.number_input("P_m Urea", 0.0001, 0.1,
                                   value=st.session_state["_bio_P_m_urea"],
                                   step=0.001, format="%.4f")
    with mc3:
        pm_lido = st.number_input("P_m Lido", 0.0001, 0.1,
                                   value=st.session_state["_bio_P_m_lido"],
                                   step=0.001, format="%.4f")
    mc4, mc5, _ = st.columns(3)
    with mc4:
        pm_megx = st.number_input("P_m MEGX", 0.0001, 0.1,
                                   value=st.session_state["_bio_P_m_MEGX"],
                                   step=0.001, format="%.4f")
    with mc5:
        pm_gx = st.number_input("P_m GX", 0.0001, 0.1,
                                 value=st.session_state["_bio_P_m_GX"],
                                 step=0.001, format="%.4f")
    st.caption("All permeabilities in cm/min.  Flux = P_m \u00d7 A_m \u00d7 \u0394C")

    # --- Kinetics ---
    st.markdown("#### Hepatocyte Kinetics")
    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1:
        k_nh3 = st.number_input("k\u2081 NH\u2083 (/min)", 0.01, 5.0,
                                 value=st.session_state["_bio_k1_NH3"], step=0.05,
                                 help="First-order ammonia removal rate")
    with kc2:
        k_lido = st.number_input("k\u2081 Lido (/min)", 0.01, 5.0,
                                  value=st.session_state["_bio_k1_lido"], step=0.05,
                                  help="CYP450 Lido \u2192 MEGX rate")
    with kc3:
        k_megx = st.number_input("k\u2082 MEGX (/min)", 0.01, 5.0,
                                  value=st.session_state["_bio_k2_MEGX"], step=0.05,
                                  help="CYP450 MEGX \u2192 GX rate")
    with kc4:
        k_dec = st.number_input("k_decay (/min)", 0.0, 0.01,
                                 value=st.session_state["_bio_k_decay"],
                                 step=0.0001, format="%.4f",
                                 help="Hepatocyte viability decay rate")

    # --- KoA preview ---
    koa_nh3 = pm_nh3 * am
    koa_lido = pm_lido * am
    koa_gx = pm_gx * am
    st.markdown(
        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;"
        f"padding:10px 14px;margin-top:4px;font-size:0.85rem;color:{GRAY}'>"
        f"<strong>Derived:</strong> &nbsp; "
        f"KoA<sub>NH\u2083</sub> = {koa_nh3:,.0f} cm\u00b3/min &nbsp;\u2022&nbsp; "
        f"KoA<sub>Lido</sub> = {koa_lido:,.0f} cm\u00b3/min &nbsp;\u2022&nbsp; "
        f"KoA<sub>GX</sub> = {koa_gx:,.0f} cm\u00b3/min &nbsp;\u2022&nbsp; "
        f"Total reactor vol = {v1 + v2:,.0f} mL"
        f"</div>",
        unsafe_allow_html=True,
    )

    # --- Action buttons ---
    st.markdown("")
    _, b2, b3 = st.columns([2, 1, 1])
    with b2:
        if st.button("Reset Defaults", key="_bio_reset", use_container_width=True):
            for k, v in _BIO_DEFAULTS.items():
                st.session_state[f"_bio_{k}"] = v
            st.rerun()
    with b3:
        if st.button("Apply", type="primary", key="_bio_apply", use_container_width=True):
            st.session_state["_bio_V_CV1"] = v1
            st.session_state["_bio_V_CV2"] = v2
            st.session_state["_bio_A_m"] = am
            st.session_state["_bio_P_m_NH3"] = pm_nh3
            st.session_state["_bio_P_m_urea"] = pm_urea
            st.session_state["_bio_P_m_lido"] = pm_lido
            st.session_state["_bio_P_m_MEGX"] = pm_megx
            st.session_state["_bio_P_m_GX"] = pm_gx
            st.session_state["_bio_k1_NH3"] = k_nh3
            st.session_state["_bio_k1_lido"] = k_lido
            st.session_state["_bio_k2_MEGX"] = k_megx
            st.session_state["_bio_k_decay"] = k_dec
            st.rerun()


# ---------------------------------------------------------------------------
# Preset info dialog
# ---------------------------------------------------------------------------
@st.dialog("Patient Preset Definitions", width="large")
def _preset_info_dialog():
    st.markdown(
        f"<p style='color:{GRAY};margin-top:-8px'>"
        "Each preset represents a different clinical scenario for acute hepatic failure. "
        "Normal reference ranges: NH\u2083 < 35 \u00b5mol/L, Lidocaine < 10 \u00b5mol/L, "
        "Hematocrit 0.36\u20130.44.</p>",
        unsafe_allow_html=True,
    )

    presets_info = {
        "Standard Adult": {
            "desc": "A 45-year-old adult (70 kg) with **moderate liver failure**. "
                    "Ammonia is 2.5\u00d7 normal, indicating significant but not "
                    "life-threatening hepatic dysfunction. This is the most common "
                    "presentation for patients who might benefit from BAL support "
                    "while awaiting transplant.",
            "severity": "SEVERE",
            "sev_color": AMBER,
        },
        "Severe Case": {
            "desc": "A 55-year-old adult (85 kg) with **fulminant hepatic failure**. "
                    "Ammonia is 5.7\u00d7 normal\u2014at this level the patient is at "
                    "risk of cerebral edema and coma. Requires aggressive treatment "
                    "with extended duration and fresh hepatocyte cartridge. Lidocaine "
                    "is also highly elevated, indicating near-total loss of CYP450 "
                    "metabolic capacity.",
            "severity": "CRITICAL",
            "sev_color": RED,
        },
        "Pediatric Patient": {
            "desc": "A 10-year-old child (35 kg) with **acute liver failure**. "
                    "Blood flow is scaled down to 75 mL/min (half of adult) to match "
                    "the smaller blood volume (~2.5 L vs 5 L). Plasma flow target is "
                    "also reduced to 20 mL/min. Pediatric patients are more sensitive "
                    "to ammonia neurotoxicity, making timely clearance especially critical.",
            "severity": "SEVERE",
            "sev_color": AMBER,
        },
        "Mild Case": {
            "desc": "A 38-year-old adult (65 kg) with **early-stage liver failure**. "
                    "Ammonia is only mildly elevated (1.7\u00d7 normal). This patient "
                    "may recover with supportive care alone, but BAL treatment can "
                    "accelerate toxin clearance and reduce the risk of progression. "
                    "Shorter treatment duration (45 min) is sufficient.",
            "severity": "MILD",
            "sev_color": GREEN,
        },
        "Custom": {
            "desc": "Start from Standard Adult defaults and modify any parameter "
                    "through the Patient Condition and Bioreactor Config panels. "
                    "Use this to explore edge cases or match specific clinical data.",
            "severity": "VARIES",
            "sev_color": GRAY,
        },
    }

    for name, vals in PRESETS.items():
        info = presets_info[name]
        sev_c = info["sev_color"]
        st.markdown(
            f"<div style='background:#1e293b;border-radius:10px;padding:14px 18px;"
            f"margin-bottom:10px;border-left:4px solid {sev_c}'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center'>"
            f"<span style='font-weight:700;font-size:14px;color:#e2e8f0'>{name}</span>"
            f"<span style='font-size:11px;font-weight:600;color:{sev_c};"
            f"background:{sev_c}18;padding:2px 8px;border-radius:8px;"
            f"border:1px solid {sev_c}40'>{info['severity']}</span>"
            f"</div>"
            f"<div style='font-size:12px;color:#94a3b8;margin-top:8px;line-height:1.5'>"
            f"{info['desc']}</div>"
            f"<div style='display:flex;gap:16px;margin-top:8px;font-size:11px;color:#64748b'>"
            f"<span>NH\u2083 <b style=\"color:#e2e8f0\">{vals['NH3']:.0f}</b></span>"
            f"<span>Lido <b style=\"color:#e2e8f0\">{vals['lido']:.0f}</b></span>"
            f"<span>Urea <b style=\"color:#e2e8f0\">{vals['urea']:.1f}</b></span>"
            f"<span>Q <b style=\"color:#e2e8f0\">{vals['Q_blood']:.0f}</b></span>"
            f"<span>Hct <b style=\"color:#e2e8f0\">{vals['Hct']:.2f}</b></span>"
            f"<span>Flow <b style=\"color:#e2e8f0\">{vals['Q_target']:.0f}</b></span>"
            f"<span>Dur <b style=\"color:#e2e8f0\">{vals['duration']}</b> min</span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def render_sidebar():
    _init_defaults()

    with st.sidebar:
        st.markdown(
            f"<h2 style='color:{NAVY};margin-bottom:0'>Simulation Setup</h2>",
            unsafe_allow_html=True)
        st.caption("Select a preset, then fine-tune via the config panels.")

        # ---- Preset selector ----
        def _on_preset():
            p = PRESETS[st.session_state._preset]
            for k in ("NH3", "lido", "urea", "Q_blood", "Hct"):
                if k in p:
                    st.session_state[f"_pt_{k}"] = p[k]
            for k in ("Q_target", "duration"):
                if k in p:
                    st.session_state[f"_s_{k}"] = p[k]

        pc1, pc2 = st.columns([5, 1])
        with pc1:
            st.selectbox("Patient Preset", list(PRESETS.keys()),
                          key="_preset", on_change=_on_preset)
        with pc2:
            st.markdown("<div style='height:25px'></div>", unsafe_allow_html=True)
            if st.button("\u2139\ufe0f", key="_open_preset_info", help="View preset definitions"):
                _preset_info_dialog()

        st.markdown("---")

        # ---- Patient Condition card ----
        _nh3 = st.session_state["_pt_NH3"]
        _lido = st.session_state["_pt_lido"]
        _hct = st.session_state["_pt_Hct"]
        _qb = st.session_state["_pt_Q_blood"]
        st.markdown(
            f'<div class="cfg-btn">'
            f'<div class="cfg-icon">\U0001fa78</div>'
            f'<div class="cfg-body">'
            f'<div class="cfg-title">Patient Condition</div>'
            f'<div class="cfg-sub">NH\u2083 {_nh3:.0f} \u00b7 Lido {_lido:.0f} \u00b7 '
            f'Hct {_hct:.2f} \u00b7 Q {_qb:.0f}</div>'
            f'</div>'
            f'<div class="cfg-arrow">\u203a</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Edit Patient Condition", key="_open_pt", use_container_width=True):
            _patient_dialog()

        # ---- Bioreactor Sizing card ----
        _v1 = st.session_state["_bio_V_CV1"]
        _v2 = st.session_state["_bio_V_CV2"]
        _am = st.session_state["_bio_A_m"]
        _k1 = st.session_state["_bio_k1_NH3"]
        st.markdown(
            f'<div class="cfg-btn">'
            f'<div class="cfg-icon">\u2699\ufe0f</div>'
            f'<div class="cfg-body">'
            f'<div class="cfg-title">Bioreactor Config</div>'
            f'<div class="cfg-sub">CV1 {_v1:.0f} \u00b7 CV2 {_v2:.0f} \u00b7 '
            f'A_m {_am:,.0f} cm\u00b2 \u00b7 k\u2081 {_k1}</div>'
            f'</div>'
            f'<div class="cfg-arrow">\u203a</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Edit Bioreactor Config", key="_open_bio", use_container_width=True):
            _bioreactor_dialog()

        st.markdown("---")

        # ---- Treatment settings (always visible — just 2 sliders) ----
        st.markdown(f"**Treatment Settings**")
        # init from preset if needed
        for k, v in [("Q_target", 30.0), ("duration", 60)]:
            if f"_s_{k}" not in st.session_state:
                st.session_state[f"_s_{k}"] = v

        q_target = st.slider("Plasma Flow Target (mL/min)", 10.0, 100.0,
                              key="_s_Q_target", step=5.0)
        duration = st.slider("Duration (min)", 10, 360,
                              key="_s_duration", step=5)

        st.markdown("---")
        adaptive = st.toggle("Adaptive Control", value=False,
                             help="Auto-optimize parameters based on severity assessment.")

        run_clicked = st.button("Run Simulation", type="primary", use_container_width=True)

    # Assemble params from session state
    params = {
        # Patient condition
        "NH3": st.session_state["_pt_NH3"],
        "lido": st.session_state["_pt_lido"],
        "urea": st.session_state["_pt_urea"],
        "Q_blood": st.session_state["_pt_Q_blood"],
        "Hct": st.session_state["_pt_Hct"],
        # Treatment
        "Q_target": q_target,
        "duration": duration,
        # Bioreactor sizing
        "V_CV1": st.session_state["_bio_V_CV1"],
        "V_CV2": st.session_state["_bio_V_CV2"],
        "A_m": st.session_state["_bio_A_m"],
        "P_m_NH3": st.session_state["_bio_P_m_NH3"],
        "P_m_urea": st.session_state["_bio_P_m_urea"],
        "P_m_lido": st.session_state["_bio_P_m_lido"],
        "P_m_MEGX": st.session_state["_bio_P_m_MEGX"],
        "P_m_GX": st.session_state["_bio_P_m_GX"],
        "k1_NH3": st.session_state["_bio_k1_NH3"],
        "k1_lido": st.session_state["_bio_k1_lido"],
        "k2_MEGX": st.session_state["_bio_k2_MEGX"],
        "k_decay": st.session_state["_bio_k_decay"],
    }
    return params, adaptive, run_clicked


# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------
def run_simulation(params, adaptive):
    """Run simulation with safe constant mutation."""

    # Save originals
    orig_sep = copy.deepcopy(constants.SEPARATOR_INPUTS)
    orig_pump = copy.deepcopy(constants.PUMP_THRESHOLDS)
    orig_kin = copy.deepcopy(constants.HEPATOCYTE_KINETICS)
    orig_vol = copy.deepcopy(constants.BIOREACTOR_VOLUMES)
    orig_mem = copy.deepcopy(constants.MEMBRANE_TRANSPORT)
    orig_bio_thresh = copy.deepcopy(constants.BIOREACTOR_THRESHOLDS)

    severity = None
    adjustments = None
    duration = params["duration"]

    try:
        # Apply patient parameters
        constants.SEPARATOR_INPUTS["C_NH3_in_nominal"] = params["NH3"]
        constants.SEPARATOR_INPUTS["C_lido_in_nominal"] = params["lido"]
        constants.SEPARATOR_INPUTS["C_urea_in_nominal"] = params["urea"]
        constants.SEPARATOR_INPUTS["Q_blood_nominal"] = params["Q_blood"]
        constants.SEPARATOR_INPUTS["Hct_in_nominal"] = params["Hct"]
        constants.PUMP_THRESHOLDS["Q_target"] = params["Q_target"]

        # Apply bioreactor sizing
        constants.BIOREACTOR_VOLUMES["V_CV1"] = params["V_CV1"]
        constants.BIOREACTOR_VOLUMES["V_CV2"] = params["V_CV2"]
        constants.MEMBRANE_TRANSPORT["A_m"] = params["A_m"]
        constants.MEMBRANE_TRANSPORT["P_m_NH3"] = params["P_m_NH3"]
        constants.MEMBRANE_TRANSPORT["P_m_urea"] = params["P_m_urea"]
        constants.MEMBRANE_TRANSPORT["P_m_lido"] = params["P_m_lido"]
        constants.MEMBRANE_TRANSPORT["P_m_MEGX"] = params["P_m_MEGX"]
        constants.MEMBRANE_TRANSPORT["P_m_GX"] = params["P_m_GX"]
        constants.HEPATOCYTE_KINETICS["k1_NH3_base"] = params["k1_NH3"]
        constants.HEPATOCYTE_KINETICS["k1_lido_base"] = params["k1_lido"]
        constants.HEPATOCYTE_KINETICS["k2_MEGX_base"] = params["k2_MEGX"]
        constants.BIOREACTOR_THRESHOLDS["k_cell_decay"] = params["k_decay"]

        if adaptive:
            ctrl = AdaptiveBALController()
            severity = ctrl.assess_severity(params["NH3"], params["lido"])
            adjustments = ctrl.calculate_adjustments(severity, params["NH3"], params["lido"])
            duration = ctrl.apply_adjustments(adjustments)

        sim = SimulationEngine(dt=1.0)
        steps = int(duration / sim.dt)
        for _ in range(steps):
            sim.step()

        # Build dataframe
        records = []
        for h in sim.history:
            row = {"time": h["time"]}
            for mod_key in ("separator", "pump", "bioreactor", "sampler", "mixer", "return_monitor"):
                prefix = {
                    "separator": "sep", "pump": "pump", "bioreactor": "bio",
                    "sampler": "samp", "mixer": "mix", "return_monitor": "mon",
                }[mod_key]
                for k, v in h[mod_key].items():
                    if isinstance(v, (int, float, bool, np.integer, np.floating)):
                        row[f"{prefix}_{k}"] = v
            records.append(row)
        df = pd.DataFrame(records)

        result = {
            "df": df,
            "final": sim.history[-1],
            "module_states": sim.get_module_states(),
            "params": params,
            "severity": severity,
            "adjustments": adjustments,
            "duration": duration,
        }
        return result

    finally:
        # Restore constants
        constants.SEPARATOR_INPUTS.update(orig_sep)
        constants.PUMP_THRESHOLDS.update(orig_pump)
        constants.HEPATOCYTE_KINETICS.update(orig_kin)
        constants.BIOREACTOR_VOLUMES.update(orig_vol)
        constants.MEMBRANE_TRANSPORT.update(orig_mem)
        constants.BIOREACTOR_THRESHOLDS.update(orig_bio_thresh)


# ---------------------------------------------------------------------------
# Metrics row
# ---------------------------------------------------------------------------
def render_metrics(r):
    bio = r["final"]["bioreactor"]
    mon = r["final"]["return_monitor"]
    p = r["params"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Final NH\u2083", f"{bio['C_NH3']:.1f} \u00b5mol/L",
                   f"{bio['C_NH3'] - p['NH3']:.1f}", delta_color="inverse")
    with c2:
        st.metric("Final Lidocaine", f"{bio['C_lido']:.1f} \u00b5mol/L",
                   f"{bio['C_lido'] - p['lido']:.1f}", delta_color="inverse")
    with c3:
        st.metric("Cell Viability", f"{bio['cell_viability']*100:.1f}%")
    with c4:
        if mon["treatment_success"]:
            st.success("TREATMENT SUCCESSFUL", icon="\u2705")
        else:
            st.error("TREATMENT INCOMPLETE", icon="\u26a0\ufe0f")

    # Secondary row
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric("NH\u2083 Clearance", f"{bio['NH3_clearance']*100:.1f}%")
    with c6:
        st.metric("Lido Clearance", f"{bio['lido_clearance']*100:.1f}%")
    with c7:
        approved = mon["return_approved"]
        st.metric("Return Approved", "Yes" if approved else "No")
    with c8:
        st.metric("Violations", mon["violation_count"])


# ---------------------------------------------------------------------------
# Plotly helpers
# ---------------------------------------------------------------------------
_PLOTLY_LAYOUT = dict(
    template="plotly_white",
    height=460,
    margin=dict(l=60, r=30, t=60, b=55),
    font=dict(size=12, family="Inter, system-ui, sans-serif"),
    legend=dict(
        orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
        bgcolor="rgba(255,255,255,0.8)", bordercolor="#e2e8f0", borderwidth=1,
        font=dict(size=11),
    ),
    title=dict(font=dict(size=15, color=NAVY), x=0.5, xanchor="center"),
)

# Plotly modebar config: show PNG download, hide logo
_PLOTLY_CONFIG = dict(
    displayModeBar=True,
    displaylogo=False,
    toImageButtonOptions=dict(format="png", filename="bal_chart", scale=2),
    modeBarButtonsToAdd=["toImage"],
    modeBarButtonsToRemove=["lasso2d", "select2d"],
)

def _fig_layout(fig, **kw):
    merged = {**_PLOTLY_LAYOUT, **kw}
    # For subplots: push legend further down and increase bottom margin
    has_subplots = getattr(fig, "_grid_ref", None) is not None
    if has_subplots:
        leg = {**_PLOTLY_LAYOUT["legend"], **merged.get("legend", {})}
        leg["y"] = -0.22
        merged["legend"] = leg
        m = dict(**merged.get("margin", _PLOTLY_LAYOUT["margin"]))
        m["b"] = max(m.get("b", 55), 90)
        m["t"] = max(m.get("t", 60), 70)
        merged["margin"] = m
    fig.update_layout(merged)
    # Style subplot titles
    for ann in fig.layout.annotations:
        ann.font = dict(size=12, color=NAVY)
    return fig

def _show_chart(fig):
    """Render a plotly chart with PNG export enabled."""
    st.plotly_chart(fig, use_container_width=True, config=_PLOTLY_CONFIG)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
def render_plots(r):
    df = r["df"]
    t = df["time"]

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Toxin Clearance",
        "Two-Compartment Model",
        "System Performance",
        "Flow & Pressure",
        "Efficiency Analysis",
        "Final Design Comparison",
    ])

    # ---- Tab 1: Toxin Clearance ----
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_NH3"], name="NH\u2083",
                                 line=dict(color=NAVY, width=2.5)))
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_lido"], name="Lidocaine",
                                 line=dict(color=INDIGO, width=2.5)))
        fig.add_hline(y=50, line_dash="dash", line_color=RED, line_width=1,
                      annotation_text="NH\u2083 safe limit (50)",
                      annotation_position="top left",
                      annotation_font_size=10, annotation_font_color=RED)
        fig.add_hline(y=10, line_dash="dot", line_color=AMBER, line_width=1,
                      annotation_text="Lido safe limit (10)",
                      annotation_position="bottom left",
                      annotation_font_size=10, annotation_font_color=AMBER)
        _fig_layout(fig, xaxis_title="Time (min)",
                    yaxis_title="Concentration (\u00b5mol/L)",
                    title="Toxin Clearance Over Treatment Duration")
        _show_chart(fig)

    # ---- Tab 2: Two-Compartment Model ----
    with tab2:
        fig = make_subplots(rows=2, cols=2, horizontal_spacing=0.12,
                            vertical_spacing=0.18,
                            subplot_titles=[
                                "NH\u2083 — CV1 vs CV2",
                                "Urea — CV1 vs CV2",
                                "Lido \u2192 MEGX \u2192 GX (CYP450 Pathway)",
                                "MEGX & GX Compartment Detail",
                            ])
        # NH3
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_NH3_CV1"], name="NH\u2083 CV1",
                                 line=dict(color=NAVY, width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_NH3_CV2"], name="NH\u2083 CV2",
                                 line=dict(color=TEAL, width=2, dash="dash")), row=1, col=1)
        fig.update_yaxes(title_text="\u00b5mol/L", row=1, col=1)

        # Urea
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_urea_CV1"], name="Urea CV1",
                                 line=dict(color=NAVY, width=2)), row=1, col=2)
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_urea_CV2"], name="Urea CV2",
                                 line=dict(color=TEAL, width=2, dash="dash")), row=1, col=2)
        fig.update_yaxes(title_text="mmol/L", row=1, col=2)

        # Lido → MEGX → GX pathway (outlet = CV1 values)
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_lido"], name="Lidocaine (out)",
                                 line=dict(color=INDIGO, width=2.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_MEGX_CV1"], name="MEGX (CV1)",
                                 line=dict(color=AMBER, width=2)), row=2, col=1)
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_GX_CV1"], name="GX (CV1)",
                                 line=dict(color=GREEN, width=2, dash="dash")), row=2, col=1)
        fig.update_yaxes(title_text="\u00b5mol/L", row=2, col=1)

        # MEGX & GX compartment detail
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_MEGX_CV1"], name="MEGX CV1",
                                 line=dict(color=AMBER, width=2)), row=2, col=2)
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_MEGX_CV2"], name="MEGX CV2",
                                 line=dict(color=AMBER, width=1.5, dash="dot")), row=2, col=2)
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_GX_CV1"], name="GX CV1",
                                 line=dict(color=GREEN, width=2)), row=2, col=2)
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_GX_CV2"], name="GX CV2",
                                 line=dict(color=GREEN, width=1.5, dash="dot")), row=2, col=2)
        fig.update_yaxes(title_text="\u00b5mol/L", row=2, col=2)

        for row in (1, 2):
            for col in (1, 2):
                fig.update_xaxes(title_text="Time (min)", row=row, col=col)

        _fig_layout(fig, height=650, title="Two-Compartment Mass Balance (10 Coupled ODEs)")
        _show_chart(fig)
        st.caption(
            "CV1 = Plasma \u2022 CV2 = Hepatocyte \u2022 "
            "Membrane: polysulfone, P_m \u00d7 A_m \u00d7 \u0394C \u2022 "
            "**Urea cycle:** 2 NH\u2083 \u2192 1 Urea \u2022 "
            "**CYP450 pathway:** Lidocaine \u2192 MEGX (N-deethylation) \u2192 GX (N-dealkylation)"
        )

    # ---- Tab 3: System Performance ----
    with tab3:
        fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                            subplot_titles=["Cell Viability", "Clearance Rates"])
        # Viability
        fig.add_trace(go.Scatter(x=t, y=df["bio_cell_viability"] * 100,
                                 name="Viability", line=dict(color=GREEN, width=2.5)),
                      row=1, col=1)
        fig.add_hline(y=80, line_dash="dash", line_color=AMBER, line_width=1,
                      annotation_text="Normal (80%)", annotation_position="bottom left",
                      annotation_font_size=9, annotation_font_color=AMBER,
                      row=1, col=1)
        fig.add_hline(y=60, line_dash="dot", line_color=RED, line_width=1,
                      annotation_text="Degraded (60%)", annotation_position="bottom left",
                      annotation_font_size=9, annotation_font_color=RED,
                      row=1, col=1)
        fig.update_yaxes(title_text="Viability (%)", row=1, col=1)

        # Clearance
        fig.add_trace(go.Scatter(x=t, y=df["bio_NH3_clearance"] * 100,
                                 name="NH\u2083 Clearance", line=dict(color=NAVY, width=2)),
                      row=1, col=2)
        fig.add_trace(go.Scatter(x=t, y=df["bio_lido_clearance"] * 100,
                                 name="Lido Clearance", line=dict(color=INDIGO, width=2, dash="dash")),
                      row=1, col=2)
        fig.update_yaxes(title_text="Clearance (%)", row=1, col=2)
        fig.update_xaxes(title_text="Time (min)", row=1, col=1)
        fig.update_xaxes(title_text="Time (min)", row=1, col=2)
        _fig_layout(fig, title="Bioreactor Performance Metrics")
        _show_chart(fig)

    # ---- Tab 4: Flow & Pressure ----
    with tab4:
        fig = make_subplots(rows=2, cols=2, horizontal_spacing=0.12,
                            vertical_spacing=0.18,
                            subplot_titles=["Separator Flows", "Pump Output Pressure",
                                            "Mixer Output", "Hematocrit"])
        # Separator flows
        fig.add_trace(go.Scatter(x=t, y=df["sep_Q_plasma"], name="Q_plasma",
                                 line=dict(color=NAVY, width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=t, y=df["sep_Q_cells"], name="Q_cells",
                                 line=dict(color=TEAL, width=2)), row=1, col=1)
        fig.update_yaxes(title_text="mL/min", row=1, col=1)

        # Pump pressure
        fig.add_trace(go.Scatter(x=t, y=df["pump_P_plasma"], name="P_pump_out",
                                 line=dict(color=INDIGO, width=2)), row=1, col=2)
        fig.update_yaxes(title_text="mmHg", row=1, col=2)

        # Mixer output flow
        fig.add_trace(go.Scatter(x=t, y=df["mix_Q_blood"], name="Q_blood out",
                                 line=dict(color=NAVY, width=2)), row=2, col=1)
        fig.update_yaxes(title_text="mL/min", row=2, col=1)

        # Hematocrit
        fig.add_trace(go.Scatter(x=t, y=df["mix_Hct_out"], name="Hct_out",
                                 line=dict(color=GREEN, width=2)), row=2, col=2)
        fig.add_hline(y=0.32, line_dash="dash", line_color=GRAY, line_width=1,
                      annotation_text="Target (0.32)", annotation_position="bottom left",
                      annotation_font_size=9, annotation_font_color=GRAY,
                      row=2, col=2)
        fig.update_yaxes(title_text="Fraction", row=2, col=2)

        for row in (1, 2):
            for col in (1, 2):
                fig.update_xaxes(title_text="Time (min)", row=row, col=col)

        _fig_layout(fig, height=650, title="Hydraulic Parameters Across the Circuit")
        _show_chart(fig)

    # ---- Tab 5: Efficiency Analysis ----
    with tab5:
        # Compute derived efficiency metrics
        inlet_nh3 = r["params"]["NH3"]
        inlet_lido = r["params"]["lido"]

        # 1. Overall Treatment Efficiency (weighted average of clearances)
        nh3_cl = df["bio_NH3_clearance"] * 100
        lido_cl = df["bio_lido_clearance"] * 100
        # Weight NH3 heavier (clinical priority) — 60/40 split
        overall_eff = 0.6 * nh3_cl + 0.4 * lido_cl

        # 2. Membrane Transfer Efficiency
        #    = (C_CV1 - C_CV2) / C_CV1 — how well the membrane maintains the
        #    concentration gradient needed for hepatocyte metabolism.
        #    High = membrane keeping up (CV2 << CV1), Low = membrane bottleneck
        cv1_nh3 = df["bio_C_NH3_CV1"]
        cv2_nh3 = df["bio_C_NH3_CV2"]
        mem_eff_nh3 = ((cv1_nh3 - cv2_nh3) / cv1_nh3.clip(lower=0.01)) * 100
        mem_eff_nh3 = mem_eff_nh3.clip(0, 100)

        cv1_urea = df["bio_C_urea_CV1"]
        cv2_urea = df["bio_C_urea_CV2"]
        # For urea, gradient is CV2→CV1 (produced in CV2, diffuses out)
        mem_eff_urea = ((cv2_urea - cv1_urea) / cv2_urea.clip(lower=0.01)) * 100
        mem_eff_urea = mem_eff_urea.clip(0, 100)

        # 3. Bioreactor Utilization
        #    = (viability × C_CV2) / C_CV2_initial — fraction of max metabolic
        #    capacity being used. Drops as both viability decays AND substrate
        #    is depleted (less toxin left to metabolize).
        cv2_nh3_initial = cv2_nh3.iloc[0] if cv2_nh3.iloc[0] > 0 else 1.0
        utilization_nh3 = (df["bio_cell_viability"] * cv2_nh3 / cv2_nh3_initial) * 100
        utilization_nh3 = utilization_nh3.clip(0, 100)

        fig = make_subplots(
            rows=2, cols=2,
            horizontal_spacing=0.12,
            vertical_spacing=0.18,
            subplot_titles=[
                "Overall Treatment Efficiency",
                "Membrane Transfer Efficiency",
                "Bioreactor Utilization",
                "Removal Rate (instantaneous)",
            ],
        )

        # Plot 1: Overall efficiency
        fig.add_trace(go.Scatter(
            x=t, y=overall_eff, name="Overall Efficiency",
            line=dict(color=NAVY, width=2.5),
            fill="tozeroy", fillcolor="rgba(30,58,95,0.1)",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=t, y=nh3_cl, name="NH\u2083 Clearance",
            line=dict(color=RED, width=1.5, dash="dot"),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=t, y=lido_cl, name="Lido Clearance",
            line=dict(color=INDIGO, width=1.5, dash="dot"),
        ), row=1, col=1)
        fig.update_yaxes(title_text="%", row=1, col=1)

        # Plot 2: Membrane transfer efficiency
        fig.add_trace(go.Scatter(
            x=t, y=mem_eff_nh3, name="NH\u2083 Gradient Util.",
            line=dict(color=TEAL, width=2.5),
        ), row=1, col=2)
        fig.add_trace(go.Scatter(
            x=t, y=mem_eff_urea, name="Urea Gradient Util.",
            line=dict(color=AMBER, width=2, dash="dash"),
        ), row=1, col=2)
        fig.update_yaxes(title_text="%", row=1, col=2)

        # Plot 3: Bioreactor utilization
        fig.add_trace(go.Scatter(
            x=t, y=utilization_nh3, name="Metabolic Utilization",
            line=dict(color=GREEN, width=2.5),
            fill="tozeroy", fillcolor="rgba(16,185,129,0.1)",
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=t, y=df["bio_cell_viability"] * 100, name="Viability",
            line=dict(color=GRAY, width=1.5, dash="dot"),
        ), row=2, col=1)
        fig.update_yaxes(title_text="%", row=2, col=1)

        # Plot 4: Instantaneous removal rate (delta per minute)
        nh3_removal = -df["bio_C_NH3"].diff().fillna(0)  # positive = removal
        lido_removal = -df["bio_C_lido"].diff().fillna(0)
        fig.add_trace(go.Scatter(
            x=t, y=nh3_removal, name="NH\u2083 removal",
            line=dict(color=NAVY, width=2),
        ), row=2, col=2)
        fig.add_trace(go.Scatter(
            x=t, y=lido_removal, name="Lido removal",
            line=dict(color=INDIGO, width=2, dash="dash"),
        ), row=2, col=2)
        fig.update_yaxes(title_text="\u00b5mol/L/min", row=2, col=2)

        for row in (1, 2):
            for col in (1, 2):
                fig.update_xaxes(title_text="Time (min)", row=row, col=col)

        _fig_layout(fig, height=650, title="Efficiency & Utilization Analysis")
        _show_chart(fig)

        st.caption(
            "**Overall Efficiency** = 0.6 \u00d7 NH\u2083 clearance + 0.4 \u00d7 Lido clearance (weighted by clinical priority)  \u2022  "
            "**Membrane Transfer** = (\u0394C across membrane) / C\u2081 \u2014 how well the membrane maintains the driving force for metabolism  \u2022  "
            "**Utilization** = (viability \u00d7 C\u2082) / C\u2082\u2080 \u2014 fraction of max metabolic capacity in use (drops as toxins are cleared and cells age)  \u2022  "
            "**Removal Rate** = instantaneous concentration drop per minute"
        )

    # ---- Tab 6: Final Design Comparison ----
    with tab6:
        fg = _FINAL_DOC_GEOMETRY
        cur_p = r["params"]
        n_units = 4        # 4 total units
        n_parallel = 2     # 2 units per stage
        n_stages = 2       # 2 stages in series

        st.markdown(
            f"Comparing the **current simulation geometry** against the "
            f"**final design document**: {n_units} cylindrical cartridges "
            f"(35\u00d720 cm each) operating **in parallel**. Patient blood "
            f"(150 mL/min) is split equally \u2014 each unit receives "
            f"{fg['Q_target']:.0f} mL/min of plasma. Since both units are "
            f"identical, one simulation gives per-unit clearance; combined "
            f"system throughput is {n_units}\u00d7."
        )

        # System architecture diagram — 2 stages × 2 parallel (CSS flexbox)
        _unit_box = (
            "background:#1e3a5f;padding:6px 16px;border-radius:6px;"
            "color:#e2e8f0;font-weight:600;font-size:13px"
        )
        _arrow = "font-size:22px;color:#475569;line-height:1"
        _stage_label = "font-size:10px;color:#475569"
        _row = "display:flex;justify-content:center;align-items:center;gap:8px"
        st.markdown(
            f"<div style='background:#1e293b;border-radius:10px;padding:18px 20px;"
            f"margin:6px 0 10px;font-size:13px;color:#94a3b8;'>"

            # Title
            f"<div style='text-align:center;margin-bottom:10px'>"
            f"<span style='color:#e2e8f0;font-weight:600'>System Architecture</span>"
            f"<span style='color:#475569;font-size:11px'> &mdash; "
            f"{n_units} units: {n_parallel}\u00d7 parallel \u00d7 {n_stages} stages in series</span></div>"

            # Separator row
            f"<div style='{_row};margin-bottom:4px'>"
            f"Patient Blood (150 mL/min) \u2192 <b>Separator</b> \u2192 "
            f"Plasma ({n_parallel}\u00d7{fg['Q_target']:.0f} = 150 mL/min)</div>"

            # Fan-out arrows for stage 1
            f"<div style='{_row}'>"
            f"<span style='{_arrow}'>\u2198</span>"
            f"<span style='width:80px'></span>"
            f"<span style='{_arrow}'>\u2199</span></div>"

            # Stage 1 units
            f"<div style='{_row}'>"
            f"<span style='{_unit_box}'>Unit A</span>"
            f"<span style='{_unit_box}'>Unit B</span>"
            f"<span style='{_stage_label};margin-left:12px'>\u2190 Stage 1 ({fg['Q_target']:.0f} mL/min each)</span></div>"

            # Fan-in arrows from stage 1
            f"<div style='{_row}'>"
            f"<span style='{_arrow}'>\u2199</span>"
            f"<span style='width:80px'></span>"
            f"<span style='{_arrow}'>\u2198</span></div>"

            # Merge + re-split
            f"<div style='{_row};margin:2px 0'>"
            f"<span style='color:#64748b;font-size:11px'>Merge (150 mL/min) \u2192 Re-split</span></div>"

            # Fan-out arrows for stage 2
            f"<div style='{_row}'>"
            f"<span style='{_arrow}'>\u2198</span>"
            f"<span style='width:80px'></span>"
            f"<span style='{_arrow}'>\u2199</span></div>"

            # Stage 2 units
            f"<div style='{_row}'>"
            f"<span style='{_unit_box}'>Unit C</span>"
            f"<span style='{_unit_box}'>Unit D</span>"
            f"<span style='{_stage_label};margin-left:12px'>\u2190 Stage 2 ({fg['Q_target']:.0f} mL/min each)</span></div>"

            # Fan-in arrows from stage 2
            f"<div style='{_row}'>"
            f"<span style='{_arrow}'>\u2199</span>"
            f"<span style='width:80px'></span>"
            f"<span style='{_arrow}'>\u2198</span></div>"

            # Mixer
            f"<div style='{_row};margin-top:4px'>"
            f"<b>Mixer</b> \u2192 Patient Return (150 mL/min)</div>"

            # Specs
            f"<div style='text-align:center;margin-top:8px;font-size:9px;color:#475569'>"
            f"Each unit: 35\u00d720 cm &bull; 7.15 L &bull; 314 cm\u00b2 &bull; "
            f"3.6\u00d710\u2079 cells &bull; {fg['V_CV1']/fg['Q_target']:.1f} min residence time</div>"

            f"</div>",
            unsafe_allow_html=True,
        )

        # Parameter comparison table
        with st.expander("Parameter Comparison Table", expanded=False):
            st.markdown(
                "| Parameter | Current (Sidebar) | Final Design (per unit) | Final Design (system) |\n"
                "|---|---|---|---|\n"
                f"| CV1 Volume | {cur_p['V_CV1']:.0f} mL | {fg['V_CV1']:,.0f} mL | {n_units*fg['V_CV1']:,.0f} mL |\n"
                f"| CV2 Volume | {cur_p['V_CV2']:.0f} mL | {fg['V_CV2']:,.0f} mL | {n_units*fg['V_CV2']:,.0f} mL |\n"
                f"| Total Volume | {cur_p['V_CV1']+cur_p['V_CV2']:.0f} mL | {fg['V_CV1']+fg['V_CV2']:,.0f} mL | {n_units*(fg['V_CV1']+fg['V_CV2']):,.0f} mL |\n"
                f"| Membrane Area | {cur_p['A_m']:,.0f} cm\u00b2 | {fg['A_m']:.0f} cm\u00b2 | {n_units*fg['A_m']:.0f} cm\u00b2 |\n"
                f"| Membrane Type | Flat Disc | Flat Disc | \u2014 |\n"
                f"| P_m NH\u2083 | {cur_p['P_m_NH3']} cm/min | {fg['P_m_NH3']} cm/min | \u2014 |\n"
                f"| P_m Lido | {cur_p['P_m_lido']} cm/min | {fg['P_m_lido']} cm/min | \u2014 |\n"
                f"| Flow/Unit | {cur_p['Q_target']:.0f} mL/min | {fg['Q_target']:.0f} mL/min | {n_parallel*fg['Q_target']:.0f} mL/min |\n"
                f"| Residence Time | {cur_p['V_CV1']/max(cur_p['Q_target'],1):.1f} min | {fg['V_CV1']/fg['Q_target']:.1f} min | {n_stages*fg['V_CV1']/fg['Q_target']:.1f} min (2 passes) |\n"
                f"| KoA (NH\u2083) | {cur_p['P_m_NH3']*cur_p['A_m']:.0f} cm\u00b3/min | {fg['P_m_NH3']*fg['A_m']:.1f} cm\u00b3/min | {n_units*fg['P_m_NH3']*fg['A_m']:.1f} cm\u00b3/min |\n"
                f"| Hematocrit | {cur_p['Hct']:.2f} | {fg['Hct']:.2f} | \u2014 |\n"
                f"| Cell Count | 5\u00d710\u2078 | 3.6\u00d710\u2079 | {n_units*3.6e9:.1e} |\n"
                f"| Configuration | Single unit | 1 cartridge | {n_parallel}\u00d7 parallel \u00d7 {n_stages} stages |\n"
                f"| Units | 1 | 1 | {n_units} total |"
            )

        # Run the final design simulation (one unit)
        if "final_design_df" not in st.session_state or st.session_state.get("_fd_hash") != id(r):
            with st.spinner("Running final design simulation (per unit)..."):
                st.session_state.final_design_df = _run_final_design_sim(r)
                st.session_state._fd_hash = id(r)

        df_fd = st.session_state.final_design_df
        t_fd = df_fd["time"]

        # ---- Main comparison charts ----
        fig = make_subplots(rows=2, cols=2, horizontal_spacing=0.12,
                            vertical_spacing=0.18,
                            subplot_titles=[
                                "NH\u2083 Outlet (\u00b5mol/L)",
                                "Lidocaine Outlet (\u00b5mol/L)",
                                "NH\u2083 Clearance (%)",
                                "Cell Viability (%)",
                            ])

        # NH3
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_NH3"], name="Current",
                                 line=dict(color=NAVY, width=2.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=t_fd, y=df_fd["bio_C_NH3"],
                                 name=f"Final ({n_units} units)",
                                 line=dict(color=RED, width=2.5, dash="dash")), row=1, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color=GRAY, line_width=1,
                      annotation_text="Safe limit (50)", annotation_position="bottom left",
                      annotation_font_size=9, annotation_font_color=GRAY, row=1, col=1)
        fig.update_yaxes(title_text="\u00b5mol/L", row=1, col=1)

        # Lido
        fig.add_trace(go.Scatter(x=t, y=df["bio_C_lido"], name="Current",
                                 line=dict(color=NAVY, width=2.5),
                                 showlegend=False), row=1, col=2)
        fig.add_trace(go.Scatter(x=t_fd, y=df_fd["bio_C_lido"],
                                 name=f"Final ({n_units} units)",
                                 line=dict(color=RED, width=2.5, dash="dash"),
                                 showlegend=False), row=1, col=2)
        fig.add_hline(y=15, line_dash="dot", line_color=GRAY, line_width=1,
                      annotation_text="Safe limit (15)", annotation_position="bottom left",
                      annotation_font_size=9, annotation_font_color=GRAY, row=1, col=2)
        fig.update_yaxes(title_text="\u00b5mol/L", row=1, col=2)

        # NH3 Clearance
        fig.add_trace(go.Scatter(x=t, y=df["bio_NH3_clearance"]*100, name="Current",
                                 line=dict(color=NAVY, width=2.5),
                                 showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=t_fd, y=df_fd["bio_NH3_clearance"]*100,
                                 name=f"Final ({n_units} units)",
                                 line=dict(color=RED, width=2.5, dash="dash"),
                                 showlegend=False), row=2, col=1)
        fig.update_yaxes(title_text="%", row=2, col=1)

        # Viability
        fig.add_trace(go.Scatter(x=t, y=df["bio_cell_viability"]*100, name="Current",
                                 line=dict(color=NAVY, width=2.5),
                                 showlegend=False), row=2, col=2)
        fig.add_trace(go.Scatter(x=t_fd, y=df_fd["bio_cell_viability"]*100,
                                 name=f"Final ({n_units} units)",
                                 line=dict(color=RED, width=2.5, dash="dash"),
                                 showlegend=False), row=2, col=2)
        fig.update_yaxes(title_text="%", row=2, col=2)

        for row in (1, 2):
            for col in (1, 2):
                fig.update_xaxes(title_text="Time (min)", row=row, col=col)

        _fig_layout(fig, height=650,
                    title=f"Current (solid) vs Final Design \u2014 {n_units} Units Parallel (dashed)")
        _show_chart(fig)

        # Two-compartment detail for final design
        st.markdown(f"#### Final Design \u2014 Per-Unit Two-Compartment Detail")
        fig2 = make_subplots(rows=1, cols=3, horizontal_spacing=0.1,
                             subplot_titles=[
                                 "NH\u2083 CV1 vs CV2",
                                 "Urea CV1 vs CV2",
                                 "Lido \u2192 MEGX \u2192 GX",
                             ])
        fig2.add_trace(go.Scatter(x=t_fd, y=df_fd["bio_C_NH3_CV1"], name="NH\u2083 CV1",
                                  line=dict(color=NAVY, width=2)), row=1, col=1)
        fig2.add_trace(go.Scatter(x=t_fd, y=df_fd["bio_C_NH3_CV2"], name="NH\u2083 CV2",
                                  line=dict(color=TEAL, width=2, dash="dash")), row=1, col=1)
        fig2.update_yaxes(title_text="\u00b5mol/L", row=1, col=1)

        fig2.add_trace(go.Scatter(x=t_fd, y=df_fd["bio_C_urea_CV1"], name="Urea CV1",
                                  line=dict(color=NAVY, width=2)), row=1, col=2)
        fig2.add_trace(go.Scatter(x=t_fd, y=df_fd["bio_C_urea_CV2"], name="Urea CV2",
                                  line=dict(color=TEAL, width=2, dash="dash")), row=1, col=2)
        fig2.update_yaxes(title_text="mmol/L", row=1, col=2)

        fig2.add_trace(go.Scatter(x=t_fd, y=df_fd["bio_C_lido"], name="Lido (out)",
                                  line=dict(color=INDIGO, width=2)), row=1, col=3)
        if "bio_C_MEGX_CV1" in df_fd.columns:
            fig2.add_trace(go.Scatter(x=t_fd, y=df_fd["bio_C_MEGX_CV1"], name="MEGX",
                                      line=dict(color=AMBER, width=2)), row=1, col=3)
        if "bio_C_GX_CV1" in df_fd.columns:
            fig2.add_trace(go.Scatter(x=t_fd, y=df_fd["bio_C_GX_CV1"], name="GX",
                                      line=dict(color=GREEN, width=2, dash="dash")), row=1, col=3)
        fig2.update_yaxes(title_text="\u00b5mol/L", row=1, col=3)

        for col in (1, 2, 3):
            fig2.update_xaxes(title_text="Time (min)", row=1, col=col)
        _fig_layout(fig2, height=400,
                    title=f"Per-Unit Detail (35\u00d720 cm, 314 cm\u00b2 flat disc, {fg['Q_target']:.0f} mL/min)")
        _show_chart(fig2)

        # Summary metrics — current vs stage 1 vs stage 2 (combined system)
        st.markdown(f"#### End-of-Treatment Comparison (t = {r['duration']} min)")
        c1, c2, c3 = st.columns(3)
        bio_cur = r["final"]["bioreactor"]
        fd_last = df_fd.iloc[-1]
        fd_nh3_cl = fd_last.get("bio_NH3_clearance", 0) * 100
        fd_lido_cl = fd_last.get("bio_lido_clearance", 0) * 100
        # Stage 1 outlet (from s1_ prefixed columns)
        s1_nh3 = fd_last.get("s1_bio_C_NH3", cur_p["NH3"])
        s1_lido = fd_last.get("s1_bio_C_lido", cur_p["lido"])
        s1_nh3_cl = (cur_p["NH3"] - s1_nh3) / cur_p["NH3"] * 100 if cur_p["NH3"] > 0 else 0

        with c1:
            st.markdown(
                f"**Current Geometry**\n\n"
                f"| Metric | Value |\n|---|---|\n"
                f"| Config | 1 unit |\n"
                f"| NH\u2083 outlet | {bio_cur['C_NH3']:.1f} \u00b5mol/L |\n"
                f"| Lido outlet | {bio_cur['C_lido']:.1f} \u00b5mol/L |\n"
                f"| NH\u2083 clearance | {bio_cur['NH3_clearance']*100:.1f}% |\n"
                f"| Lido clearance | {bio_cur['lido_clearance']*100:.1f}% |\n"
                f"| Cell viability | {bio_cur['cell_viability']*100:.1f}% |\n"
                f"| KoA NH\u2083 | {cur_p['P_m_NH3']*cur_p['A_m']:.0f} cm\u00b3/min |"
            )
        with c2:
            st.markdown(
                f"**Final Design \u2014 After Stage 1**\n\n"
                f"| Metric | Value |\n|---|---|\n"
                f"| Config | {n_parallel}\u00d7 parallel |\n"
                f"| NH\u2083 outlet | {s1_nh3:.1f} \u00b5mol/L |\n"
                f"| Lido outlet | {s1_lido:.1f} \u00b5mol/L |\n"
                f"| NH\u2083 clearance | {s1_nh3_cl:.1f}% |\n"
                f"| Res. time | {fg['V_CV1']/fg['Q_target']:.1f} min |\n"
                f"| Flow/unit | {fg['Q_target']:.0f} mL/min |\n"
                f"| KoA/unit | {fg['P_m_NH3']*fg['A_m']:.1f} cm\u00b3/min |"
            )
        with c3:
            st.markdown(
                f"**Final Design \u2014 After Stage 2 (patient-facing)**\n\n"
                f"| Metric | Value |\n|---|---|\n"
                f"| Config | {n_parallel}\u00d7\u00d7{n_stages} stages |\n"
                f"| NH\u2083 outlet | {fd_last['bio_C_NH3']:.1f} \u00b5mol/L |\n"
                f"| Lido outlet | {fd_last['bio_C_lido']:.1f} \u00b5mol/L |\n"
                f"| NH\u2083 clearance | {fd_nh3_cl:.1f}% |\n"
                f"| Lido clearance | {fd_lido_cl:.1f}% |\n"
                f"| Total volume | {n_units*(fg['V_CV1']+fg['V_CV2'])/1000:.1f} L |\n"
                f"| Total cells | {n_units*3.6e9:.1e} |"
            )

        # Engineering insight callout
        koa_cur = cur_p["P_m_NH3"] * cur_p["A_m"]
        koa_fd = fg["P_m_NH3"] * fg["A_m"]
        st.markdown(
            f"<div style='background:#1e293b;border-left:4px solid {AMBER};border-radius:8px;"
            f"padding:12px 16px;margin-top:10px;font-size:13px;color:#94a3b8;line-height:1.6'>"
            f"<span style='color:{AMBER};font-weight:700'>Engineering Insight:</span> "
            f"The flat-disc design has a KoA of {koa_fd:.1f} cm\u00b3/min per unit "
            f"({n_units*koa_fd:.1f} combined) vs {koa_cur:.0f} for the current sidebar config. "
            f"The flat-disc design uses a {fg['V_CV1']/fg['Q_target']:.0f}-minute residence time "
            f"per unit to compensate for the smaller membrane area. The 2-stage series "
            f"configuration provides two sequential treatment passes, improving overall "
            f"clearance beyond what a single pass achieves. To further improve performance, "
            f"the team could consider stacked membrane discs or a corrugated membrane surface "
            f"to increase A_m within the same cartridge footprint."
            f"</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Final document geometry parameters (flat-disc cylindrical cartridge)
# ---------------------------------------------------------------------------
_FINAL_DOC_GEOMETRY = {
    "V_CV1": 3570.0,       # mL — plasma compartment (one unit)
    "V_CV2": 3570.0,       # mL — hepatocyte compartment
    "A_m": 314.0,          # cm² — flat disc (π × 10²)
    "P_m_NH3": 0.006,      # cm/min — same
    "P_m_urea": 0.006,     # cm/min — same
    "P_m_lido": 0.003,     # cm/min — updated from document
    "P_m_MEGX": 0.0048,    # cm/min — kept
    "P_m_GX": 0.0044,      # cm/min — kept
    "k1_NH3": 1.0,         # /min — same
    "k1_lido": 0.85,       # /min — same
    "k_decay": 0.0001,     # /min — same
    "Q_target": 75.0,      # mL/min — per unit (150 ÷ 2 parallel per stage)
    "Hct": 0.40,           # fraction — updated
    "sep_eff": 0.98,        # separation efficiency
    "cell_count": 3.6e9,   # cells per unit
}


def _apply_final_design_constants(p, fg):
    """Apply final design geometry to constants. Returns nothing."""
    constants.SEPARATOR_INPUTS["C_NH3_in_nominal"] = p["NH3"]
    constants.SEPARATOR_INPUTS["C_lido_in_nominal"] = p["lido"]
    constants.SEPARATOR_INPUTS["C_urea_in_nominal"] = p["urea"]
    constants.SEPARATOR_INPUTS["Q_blood_nominal"] = p["Q_blood"]
    constants.SEPARATOR_INPUTS["Hct_in_nominal"] = fg["Hct"]
    constants.BIOREACTOR_VOLUMES["V_CV1"] = fg["V_CV1"]
    constants.BIOREACTOR_VOLUMES["V_CV2"] = fg["V_CV2"]
    constants.MEMBRANE_TRANSPORT["A_m"] = fg["A_m"]
    constants.MEMBRANE_TRANSPORT["P_m_NH3"] = fg["P_m_NH3"]
    constants.MEMBRANE_TRANSPORT["P_m_urea"] = fg["P_m_urea"]
    constants.MEMBRANE_TRANSPORT["P_m_lido"] = fg["P_m_lido"]
    constants.MEMBRANE_TRANSPORT["P_m_MEGX"] = fg["P_m_MEGX"]
    constants.MEMBRANE_TRANSPORT["P_m_GX"] = fg["P_m_GX"]
    constants.HEPATOCYTE_KINETICS["k1_NH3_base"] = fg["k1_NH3"]
    constants.HEPATOCYTE_KINETICS["k1_lido_base"] = fg["k1_lido"]
    constants.BIOREACTOR_THRESHOLDS["k_cell_decay"] = fg["k_decay"]
    constants.PUMP_THRESHOLDS["Q_target"] = fg["Q_target"]


def _run_final_design_sim(r):
    """Run 2-stage series simulation (2×2 config: 2 parallel per stage, 2 stages).

    Stage 1: Patient plasma → bioreactor unit at 75 mL/min
    Stage 2: Stage 1 outlet → fresh bioreactor unit at 75 mL/min
    Both stages run concurrently for the full treatment duration.
    The combined output reflects two sequential passes.
    """
    p = r["params"]
    fg = _FINAL_DOC_GEOMETRY

    orig_sep = copy.deepcopy(constants.SEPARATOR_INPUTS)
    orig_pump = copy.deepcopy(constants.PUMP_THRESHOLDS)
    orig_kin = copy.deepcopy(constants.HEPATOCYTE_KINETICS)
    orig_vol = copy.deepcopy(constants.BIOREACTOR_VOLUMES)
    orig_mem = copy.deepcopy(constants.MEMBRANE_TRANSPORT)
    orig_bio_thresh = copy.deepcopy(constants.BIOREACTOR_THRESHOLDS)

    try:
        duration = int(r["duration"])

        # --- Stage 1: patient plasma at original concentrations ---
        _apply_final_design_constants(p, fg)
        sim1 = SimulationEngine(dt=1.0)
        for _ in range(duration):
            sim1.step()

        # --- Stage 2: feed stage-1 outlet into a second bioreactor ---
        # Get stage-1 final outlet concentrations (steady-state inlet for stage 2)
        s1_final = sim1.history[-1]["bioreactor"]
        _apply_final_design_constants(p, fg)
        # Override inlet concentrations with stage 1 outlet
        constants.SEPARATOR_INPUTS["C_NH3_in_nominal"] = s1_final["C_NH3"]
        constants.SEPARATOR_INPUTS["C_lido_in_nominal"] = s1_final["C_lido"]
        constants.SEPARATOR_INPUTS["C_urea_in_nominal"] = s1_final["C_urea"]

        sim2 = SimulationEngine(dt=1.0)
        for _ in range(duration):
            sim2.step()

        # Build combined dataframe — report stage 2 outputs (final patient-facing)
        # but include stage 1 data for comparison
        records = []
        for i, h2 in enumerate(sim2.history):
            h1 = sim1.history[i] if i < len(sim1.history) else sim1.history[-1]
            row = {"time": h2["time"]}
            # Stage 2 (final) bioreactor outputs
            for k, v in h2["bioreactor"].items():
                if isinstance(v, (int, float, bool, np.integer, np.floating)):
                    row[f"bio_{k}"] = v
            # Stage 1 bioreactor outputs for reference
            for k, v in h1["bioreactor"].items():
                if isinstance(v, (int, float, bool, np.integer, np.floating)):
                    row[f"s1_bio_{k}"] = v
            # Return monitor from stage 2
            for k, v in h2["return_monitor"].items():
                if isinstance(v, (int, float, bool, np.integer, np.floating)):
                    row[f"mon_{k}"] = v
            # Recalculate clearance relative to original patient inlet
            if p["NH3"] > 0:
                row["bio_NH3_clearance"] = (p["NH3"] - h2["bioreactor"]["C_NH3"]) / p["NH3"]
            if p["lido"] > 0:
                row["bio_lido_clearance"] = (p["lido"] - h2["bioreactor"]["C_lido"]) / p["lido"]
            records.append(row)
        return pd.DataFrame(records)

    finally:
        constants.SEPARATOR_INPUTS.update(orig_sep)
        constants.PUMP_THRESHOLDS.update(orig_pump)
        constants.HEPATOCYTE_KINETICS.update(orig_kin)
        constants.BIOREACTOR_VOLUMES.update(orig_vol)
        constants.MEMBRANE_TRANSPORT.update(orig_mem)
        constants.BIOREACTOR_THRESHOLDS.update(orig_bio_thresh)


# ---------------------------------------------------------------------------
# Animated system schematic (HTML/CSS/SVG)
# ---------------------------------------------------------------------------
def render_schematic(r):
    """Render an animated BAL circuit schematic using HTML/CSS/SVG."""

    frames = []
    for h in r["df"].to_dict("records"):
        frames.append({
            "t": round(h.get("time", 0), 1),
            "sep_Q_plasma": round(h.get("sep_Q_plasma", 0), 1),
            "sep_Q_cells": round(h.get("sep_Q_cells", 0), 1),
            "sep_state": int(h.get("sep_alarm_code", 0)),
            "pump_Q": round(h.get("pump_Q_plasma", 0), 1),
            "pump_state": int(h.get("pump_alarm_code", 0)),
            "bio_nh3": round(h.get("bio_C_NH3", 0), 1),
            "bio_lido": round(h.get("bio_C_lido", 0), 1),
            "bio_nh3_cv1": round(h.get("bio_C_NH3_CV1", 0), 1),
            "bio_nh3_cv2": round(h.get("bio_C_NH3_CV2", 0), 1),
            "bio_urea_cv1": round(h.get("bio_C_urea_CV1", 0), 1),
            "bio_urea_cv2": round(h.get("bio_C_urea_CV2", 0), 1),
            "bio_lido_cv2": round(h.get("bio_C_lido_CV2", 0) if "bio_C_lido_CV2" in h else 0, 1),
            "bio_megx_cv1": round(h.get("bio_C_MEGX_CV1", 0), 1),
            "bio_megx_cv2": round(h.get("bio_C_MEGX_CV2", 0), 1),
            "bio_gx_cv1": round(h.get("bio_C_GX_CV1", 0), 1),
            "bio_gx_cv2": round(h.get("bio_C_GX_CV2", 0), 1),
            "bio_viability": round(h.get("bio_cell_viability", 1), 3),
            "bio_clearance": round(h.get("bio_NH3_clearance", 0), 3),
            "bio_lido_cl": round(h.get("bio_lido_clearance", 0), 3),
            "bio_state": int(h.get("bio_alarm_code", 0)),
            "mix_Q": round(h.get("mix_Q_blood", 0), 1),
            "mix_Hct": round(h.get("mix_Hct_out", 0), 3),
            "mix_state": int(h.get("mix_alarm_code", 0)),
            "mon_nh3": round(h.get("mon_C_NH3", 0), 1),
            "mon_approved": bool(h.get("mon_return_approved", False)),
            "mon_success": bool(h.get("mon_treatment_success", False)),
            "mon_state": int(h.get("mon_alarm_code", 0)),
        })

    data_json = json.dumps(frames)
    inlet_nh3 = r["params"]["NH3"]
    v_cv1 = r["params"]["V_CV1"]
    v_cv2 = r["params"]["V_CV2"]

    from schematic import build_schematic_html
    html = build_schematic_html(data_json, inlet_nh3, v_cv1, v_cv2)
    components.html(html, height=620, scrolling=False)


def render_reactor_diagram(r):
    """Render the bioreactor cutaway with reaction visualization."""
    # Reuse the same frame data built by render_schematic
    frames = []
    for h in r["df"].to_dict("records"):
        frames.append({
            "t": round(h.get("time", 0), 1),
            "pump_Q": round(h.get("pump_Q_plasma", 0), 1),
            "bio_nh3": round(h.get("bio_C_NH3", 0), 1),
            "bio_lido": round(h.get("bio_C_lido", 0), 1),
            "bio_nh3_cv1": round(h.get("bio_C_NH3_CV1", 0), 1),
            "bio_nh3_cv2": round(h.get("bio_C_NH3_CV2", 0), 1),
            "bio_urea_cv1": round(h.get("bio_C_urea_CV1", 0), 1),
            "bio_urea_cv2": round(h.get("bio_C_urea_CV2", 0), 1),
            "bio_lido_cv2": round(h.get("bio_C_lido_CV2", 0) if "bio_C_lido_CV2" in h else 0, 1),
            "bio_megx_cv1": round(h.get("bio_C_MEGX_CV1", 0), 1),
            "bio_megx_cv2": round(h.get("bio_C_MEGX_CV2", 0), 1),
            "bio_gx_cv1": round(h.get("bio_C_GX_CV1", 0), 1),
            "bio_gx_cv2": round(h.get("bio_C_GX_CV2", 0), 1),
            "bio_viability": round(h.get("bio_cell_viability", 1), 3),
            "bio_clearance": round(h.get("bio_NH3_clearance", 0), 3),
            "bio_lido_cl": round(h.get("bio_lido_clearance", 0), 3),
        })

    data_json = json.dumps(frames)
    from reactor_diagram import build_reactor_html
    html = build_reactor_html(
        data_json,
        r["params"]["NH3"], r["params"]["lido"],
        r["params"]["V_CV1"], r["params"]["V_CV2"],
        r["params"]["A_m"],
    )
    components.html(html, height=520, scrolling=False)


# ---------------------------------------------------------------------------
# Module status pipeline
# ---------------------------------------------------------------------------
_ALARM_COLORS = {
    0: (GREEN, "#ecfdf5"),
    1: (AMBER, "#fffbeb"),
    2: (RED, "#fef2f2"),
    3: (RED, "#fef2f2"),
}

_MODULE_ORDER = [
    ("Plasma Separator", "separator"),
    ("Plasma Pump", "pump"),
    ("Bioreactor", "bioreactor"),
    ("Sampler", "sampler"),
    ("Mixer", "mixer"),
    ("Return Monitor", "return_monitor"),
]


def render_module_status(r):
    st.markdown(f"<h3 style='color:{NAVY}'>System Module Status</h3>", unsafe_allow_html=True)

    # Build HTML pipeline
    cards_html = '<div style="display:flex;align-items:stretch;gap:4px;flex-wrap:wrap;">'

    for i, (label, key) in enumerate(_MODULE_ORDER):
        alarm = r["final"][key].get("alarm_code", 0)
        state_name = r["final"][key].get("state_name", "UNKNOWN")
        border_c, bg_c = _ALARM_COLORS.get(alarm, _ALARM_COLORS[0])

        cards_html += f"""
        <div style="flex:1;min-width:110px;border-left:4px solid {border_c};
                     background:{bg_c};border-radius:6px;padding:10px 6px;text-align:center;">
            <div class="mod-name">{label}</div>
            <div class="mod-state" style="color:{border_c}">{state_name.replace('_',' ')}</div>
        </div>"""

        if i < len(_MODULE_ORDER) - 1:
            cards_html += '<div class="flow-arrow">\u2192</div>'

    cards_html += "</div>"

    # Flow label
    flow_label = (
        f'<div style="display:flex;justify-content:space-between;padding:4px 8px;'
        f'color:{GRAY};font-size:0.75rem;margin-top:2px;">'
        f'<span>Patient Blood In \u2192</span><span>\u2192 Treated Blood Return</span></div>'
    )
    st.markdown(flow_label + cards_html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Treatment summary
# ---------------------------------------------------------------------------
def render_summary(r):
    with st.expander("Treatment Summary & Details"):
        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown("**Input Parameters**")
            p = r["params"]
            st.markdown(
                f"| Parameter | Value |\n|---|---|\n"
                f"| NH\u2083 | {p['NH3']} \u00b5mol/L |\n"
                f"| Lidocaine | {p['lido']} \u00b5mol/L |\n"
                f"| Urea | {p['urea']} mmol/L |\n"
                f"| Blood Flow | {p['Q_blood']} mL/min |\n"
                f"| Hematocrit | {p['Hct']} |\n"
                f"| Plasma Flow Target | {p['Q_target']} mL/min |\n"
                f"| Duration | {r['duration']} min |"
            )
            st.markdown("**Bioreactor Sizing**")
            st.markdown(
                f"| Parameter | Value |\n|---|---|\n"
                f"| CV1 Volume | {p['V_CV1']} mL |\n"
                f"| CV2 Volume | {p['V_CV2']} mL |\n"
                f"| Membrane Area | {p['A_m']:,.0f} cm\u00b2 |\n"
                f"| P_m NH\u2083 | {p['P_m_NH3']} cm/min |\n"
                f"| P_m Urea | {p['P_m_urea']} cm/min |\n"
                f"| P_m Lido | {p['P_m_lido']} cm/min |\n"
                f"| P_m MEGX | {p['P_m_MEGX']} cm/min |\n"
                f"| P_m GX | {p['P_m_GX']} cm/min |\n"
                f"| k\u2081 NH\u2083 | {p['k1_NH3']} /min |\n"
                f"| k\u2081 Lido | {p['k1_lido']} /min |\n"
                f"| k\u2082 MEGX | {p['k2_MEGX']} /min |\n"
                f"| k_decay | {p['k_decay']} /min |"
            )

        with col_r:
            st.markdown("**Outcome**")
            bio = r["final"]["bioreactor"]
            mon = r["final"]["return_monitor"]
            st.markdown(
                f"| Metric | Value |\n|---|---|\n"
                f"| Final NH\u2083 | {bio['C_NH3']:.1f} \u00b5mol/L |\n"
                f"| Final Lidocaine | {bio['C_lido']:.1f} \u00b5mol/L |\n"
                f"| NH\u2083 Clearance | {bio['NH3_clearance']*100:.1f}% |\n"
                f"| Lido Clearance | {bio['lido_clearance']*100:.1f}% |\n"
                f"| Cell Viability | {bio['cell_viability']*100:.1f}% |\n"
                f"| Return Approved | {'Yes' if mon['return_approved'] else 'No'} |\n"
                f"| Treatment Success | {'Yes' if mon['treatment_success'] else 'No'} |"
            )

        if r["severity"]:
            st.markdown("---")
            st.markdown("**Adaptive Controller Adjustments**")
            adj = r["adjustments"]
            items = [f"- Severity: **{r['severity'].upper()}**",
                     f"- Flow rate: 30 \u2192 **{adj['Q_plasma']} mL/min**",
                     f"- Duration: {r['params']['duration']} \u2192 **{r['duration']} min**"]
            if adj.get("fresh_cartridge"):
                items.append(f"- Fresh hepatocyte cartridge installed (k\u2081 \u00d7{adj['k1_multiplier']:.1f})")
            if adj.get("temperature_boost", 0) > 0:
                items.append(f"- Temperature boost: +{adj['temperature_boost']}\u00b0C")
            st.markdown("\n".join(items))

        st.markdown("---")
        st.markdown("**Core Mass Balance Equations (Two-Compartment Bioreactor)**")
        st.latex(r"\frac{dC_{NH_3}^{CV1}}{dt} = \frac{Q}{V_1}\left(C_{NH_3}^{in} - C_{NH_3}^{CV1}\right) - \frac{P_m \cdot A_m}{V_1}\left(C_{NH_3}^{CV1} - C_{NH_3}^{CV2}\right)")
        st.latex(r"\frac{dC_{NH_3}^{CV2}}{dt} = \frac{P_m \cdot A_m}{V_2}\left(C_{NH_3}^{CV1} - C_{NH_3}^{CV2}\right) - k_1 \cdot C_{NH_3}^{CV2}")
        st.latex(r"\frac{dC_{urea}^{CV2}}{dt} = \frac{1}{2}\,k_1 \cdot C_{NH_3}^{CV2} - \frac{P_m \cdot A_m}{V_2}\left(C_{urea}^{CV2} - C_{urea}^{CV1}\right)")
        st.caption("2 NH\u2083 \u2192 1 Urea (urea cycle) \u2022 1 Lidocaine \u2192 1 MEGX (CYP450)")


# ---------------------------------------------------------------------------
# Scenario explainer
# ---------------------------------------------------------------------------
def render_explainer(r):
    """Generate a plain-English explanation of what happened in this simulation."""
    p = r["params"]
    bio = r["final"]["bioreactor"]
    mon = r["final"]["return_monitor"]
    dur = r["duration"]
    success = mon["treatment_success"]

    nh3_in, nh3_out = p["NH3"], bio["C_NH3"]
    lido_in, lido_out = p["lido"], bio["C_lido"]
    viab = bio["cell_viability"] * 100
    nh3_cl = bio["NH3_clearance"] * 100
    lido_cl = bio["lido_clearance"] * 100

    # Classify severity for narrative
    if nh3_in >= 150:
        severity_word = "critically elevated"
    elif nh3_in >= 80:
        severity_word = "severely elevated"
    elif nh3_in >= 35:
        severity_word = "moderately elevated"
    else:
        severity_word = "mildly elevated"

    # Build the narrative
    lines = []

    lines.append(f"### What happened in this simulation")
    lines.append("")
    lines.append(
        f"A patient presented with **{severity_word} ammonia** ({nh3_in:.0f} \u00b5mol/L, "
        f"normal < 35) and **lidocaine at {lido_in:.0f} \u00b5mol/L** (normal < 10), "
        f"indicating acute hepatic failure where the liver can no longer adequately "
        f"clear toxins from the blood."
    )

    lines.append("")
    lines.append("#### The treatment process")
    lines.append(
        f"The patient's blood was circulated through the BAL device at "
        f"{p['Q_blood']:.0f} mL/min for **{dur} minutes**. The plasma separator "
        f"first split the blood into plasma and cellular components (RBCs, WBCs, "
        f"platelets). Only the plasma\u2014carrying the dissolved toxins\u2014was "
        f"pumped through the bioreactor at {p['Q_target']:.0f} mL/min. "
        f"The cellular components bypassed the bioreactor and were recombined with "
        f"the treated plasma in the mixer before returning to the patient."
    )

    lines.append("")
    lines.append("#### Inside the bioreactor")
    lines.append(
        f"The bioreactor contains two compartments separated by a polysulfone "
        f"membrane ({p['A_m']:,.0f} cm\u00b2 surface area):\n\n"
        f"- **CV1 (Plasma side, {p['V_CV1']:.0f} mL):** Toxic plasma flows through "
        f"this compartment. Ammonia and lidocaine diffuse across the membrane into CV2 "
        f"driven by the concentration gradient.\n"
        f"- **CV2 (Hepatocyte side, {p['V_CV2']:.0f} mL):** Contains ~5\u00d710\u2078 "
        f"viable hepatocytes (liver cells) that metabolize the toxins. Ammonia is "
        f"converted to urea via the **urea cycle** (2 NH\u2083 \u2192 1 Urea), and "
        f"lidocaine is metabolized through a two-step **CYP450 pathway**: first "
        f"N-deethylation to MEGX (1 Lido \u2192 1 MEGX), then N-dealkylation to GX "
        f"(1 MEGX \u2192 1 GX). All products diffuse back across the membrane.\n\n"
        f"This is modeled by **10 coupled ordinary differential equations** (forward "
        f"Euler integration, 1-minute time steps) tracking concentrations of NH\u2083, "
        f"urea, lidocaine, and MEGX in both compartments simultaneously."
    )

    lines.append("")
    lines.append("#### Results")

    if success:
        lines.append(
            f"After {dur} minutes of treatment, ammonia dropped from "
            f"**{nh3_in:.0f} \u2192 {nh3_out:.1f} \u00b5mol/L** "
            f"({nh3_cl:.1f}% clearance) and lidocaine from "
            f"**{lido_in:.0f} \u2192 {lido_out:.1f} \u00b5mol/L** "
            f"({lido_cl:.1f}% clearance). Both are now below clinical safety "
            f"thresholds (NH\u2083 < 50, Lido < 12). The hepatocytes maintained "
            f"**{viab:.1f}% viability** throughout treatment, indicating the cell "
            f"cartridge is still functional for potential re-use. "
            f"The return monitor confirmed zero safety violations and **approved "
            f"the treated blood for return to the patient**."
        )
    else:
        issues = []
        if nh3_out >= 50:
            issues.append(f"ammonia remains at {nh3_out:.1f} \u00b5mol/L (target < 50)")
        if lido_out >= 12:
            issues.append(f"lidocaine remains at {lido_out:.1f} \u00b5mol/L (target < 12)")
        if mon["violation_count"] > 0:
            issues.append(f"{mon['violation_count']} safety violation(s) detected")
        issue_text = " and ".join(issues) if issues else "thresholds not met"
        lines.append(
            f"After {dur} minutes, ammonia dropped from "
            f"**{nh3_in:.0f} \u2192 {nh3_out:.1f} \u00b5mol/L** "
            f"({nh3_cl:.1f}% clearance) and lidocaine from "
            f"**{lido_in:.0f} \u2192 {lido_out:.1f} \u00b5mol/L** "
            f"({lido_cl:.1f}% clearance). However, treatment is **incomplete** "
            f"because {issue_text}. "
            f"The hepatocytes maintained {viab:.1f}% viability. "
            f"**Recommended next steps:** extend treatment duration, increase "
            f"plasma flow rate, or install a fresh hepatocyte cartridge to boost "
            f"metabolic capacity."
        )

    # Adaptive controller note
    if r["severity"]:
        adj = r["adjustments"]
        lines.append("")
        lines.append("#### Adaptive controller")
        lines.append(
            f"The adaptive controller classified this patient as "
            f"**{r['severity'].upper()}** severity and automatically adjusted: "
            f"flow rate to {adj['Q_plasma']} mL/min"
            + (f", installed a fresh hepatocyte cartridge "
               f"({adj['k1_multiplier']:.1f}\u00d7 metabolic boost)"
               if adj.get("fresh_cartridge") else "")
            + (f", applied a +{adj['temperature_boost']}\u00b0C temperature boost"
               if adj.get("temperature_boost", 0) > 0 else "")
            + f", and extended treatment to {dur} minutes."
        )

    lines.append("")
    lines.append("#### Key engineering takeaway")
    lines.append(
        f"The two-compartment mass balance model shows that toxin clearance is "
        f"governed by three factors: **(1)** membrane transport rate "
        f"(P_m \u00d7 A_m \u00d7 \u0394C), **(2)** hepatocyte metabolic rate "
        f"(k\u2081 \u00d7 viability \u00d7 C_CV2), and **(3)** plasma residence "
        f"time (V/Q). The system reaches steady state when the rate of toxin "
        f"entering CV1 equals the rate being metabolized in CV2\u2014which is why "
        f"simply extending treatment duration beyond ~20 minutes yields diminishing "
        f"returns. To further reduce outlet concentrations, you need to increase "
        f"membrane area, boost hepatocyte activity (fresh cartridge), or reduce inlet "
        f"flow to increase residence time."
    )

    st.markdown("\n".join(lines))


# ---------------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------------
def render_downloads(r):
    col1, col2 = st.columns(2)
    with col1:
        csv = r["df"].to_csv(index=False)
        st.download_button("Download Results CSV", csv,
                           "bal_simulation_results.csv", "text/csv",
                           use_container_width=True)
    with col2:
        # Build a JSON-safe version (convert numpy types)
        json_data = json.dumps({
            "params": r["params"],
            "severity": r["severity"],
            "duration": r["duration"],
            "final_nh3": float(r["final"]["bioreactor"]["C_NH3"]),
            "final_lido": float(r["final"]["bioreactor"]["C_lido"]),
            "cell_viability": float(r["final"]["bioreactor"]["cell_viability"]),
            "treatment_success": bool(r["final"]["return_monitor"]["treatment_success"]),
        }, indent=2)
        st.download_button("Download Summary JSON", json_data,
                           "bal_summary.json", "application/json",
                           use_container_width=True)


# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------
@st.dialog("About the BAL Digital Twin", width="large")
def _about_dialog():
    st.markdown(
        f"<p style='color:{GRAY};margin-top:-8px'>"
        "Senior Capstone Project — University of Georgia, College of Engineering</p>",
        unsafe_allow_html=True,
    )

    st.markdown("""
Acute hepatic failure has limited treatment options beyond liver transplantation,
which is constrained by donor shortages and time pressure (50-80% mortality).
This digital twin simulates an extracorporeal BAL device that processes patient
blood through a flat-disc membrane bioreactor containing viable hepatocytes.

**System Pipeline:**
Plasma Separator \u2192 Pump Control \u2192 Bioreactor \u2192 Sampler \u2192 Mixer \u2192 Return Monitor
    """)

    st.markdown("---")

    tc1, tc2 = st.columns(2)
    with tc1:
        st.markdown("**Team**")
        st.markdown(
            "- Namit Gandavadi\n"
            "- Sabrina Yurconic\n"
            "- Anna Bourne\n"
            "- Ivy Lin\n"
            "- Grace Treon"
        )
    with tc2:
        st.markdown("**Advisors**")
        st.markdown(
            "- **Advisor/Client:** Dr. James Kastner\n"
            "- **Mentor:** Dr. Anjan Panneer Selvam"
        )
        st.markdown("")
        st.markdown("**Institution**")
        st.markdown("University of Georgia, College of Engineering")

    st.markdown("---")
    st.markdown("**Key Design Parameters**")
    st.markdown(
        "| Parameter | Per Unit | System (4 units) |\n"
        "|---|---|---|\n"
        "| Cartridge | 35\u00d720 cm cylinder | 4 cartridges |\n"
        "| Membrane | 314 cm\u00b2 flat disc | 1,256 cm\u00b2 total |\n"
        "| Volume | 7.15 L (3.57 L/compartment) | 28.6 L total |\n"
        "| Hepatocytes | 3.6\u00d710\u2079 cells | 1.44\u00d710\u00b9\u2070 total |\n"
        "| Plasma Flow | 75 mL/min | 150 mL/min (2\u00d72 config) |\n"
        "| Configuration | \u2014 | 2\u00d7 parallel \u00d7 2 stages in series |"
    )


# ---------------------------------------------------------------------------
# Welcome state
# ---------------------------------------------------------------------------
def render_welcome():
    st.markdown(
        f"""
        <div style="text-align:center;padding:60px 20px;background:{CARD};
                    border-radius:12px;margin:20px 0;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
            <div style="font-size:3rem;margin-bottom:12px;">\U0001f9ec</div>
            <h3 style="color:{NAVY};margin:0">Configure & Run</h3>
            <p style="color:{GRAY};max-width:500px;margin:8px auto 0;">
                Select a patient preset in the sidebar, adjust parameters as needed,
                and click <strong>Run Simulation</strong> to begin treatment analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    inject_css()

    # Header with about icon
    hdr1, hdr2 = st.columns([20, 1])
    with hdr1:
        st.markdown(
            f"""
            <div style="text-align:center;padding:0.8rem 0 0.2rem;">
                <h1 style="color:{NAVY};margin:0;font-size:2rem;">Bioartificial Liver Digital Twin</h1>
                <p style="color:{GRAY};margin:4px 0 0;font-size:1.05rem;">
                    Treatment Simulation & Monitoring Dashboard
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with hdr2:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("\u2139\ufe0f", key="_open_about", help="About & Team"):
            _about_dialog()

    params, adaptive, run_clicked = render_sidebar()

    if run_clicked:
        with st.spinner("Running simulation..."):
            result = run_simulation(params, adaptive)
            st.session_state.sim_result = result

    if "sim_result" in st.session_state:
        r = st.session_state.sim_result
        render_metrics(r)
        st.markdown("---")
        with st.expander("Live System Schematic", expanded=True):
            render_schematic(r)
        with st.expander("Reactor Cutaway — Bioreactor Internals", expanded=True):
            render_reactor_diagram(r)
        st.markdown("---")
        render_plots(r)
        st.markdown("---")
        render_explainer(r)
        st.markdown("---")
        render_module_status(r)
        st.markdown("---")
        render_summary(r)
        render_downloads(r)
    else:
        render_welcome()



if __name__ == "__main__":
    main()
