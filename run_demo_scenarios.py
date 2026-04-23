"""Run all 7 demo scenarios with and without adaptive control.

Exercises the same code path as the Streamlit dashboard (2-stage
series-parallel) without the UI. Prints a pass/fail report.
"""

from __future__ import annotations

import copy
import sys
import traceback

import numpy as np

import config.constants as constants
from adaptive_controller import AdaptiveBALController
from simulation.engine import SimulationEngine


BIO_DEFAULTS = {
    "V_CV1": 3570.0, "V_CV2": 3570.0, "A_m": 314.0,
    "P_m_NH3": 0.12, "P_m_urea": 0.12, "P_m_lido": 0.10,
    "P_m_MEGX": 0.09, "P_m_GX": 0.085,
    "k1_NH3": 1.0, "k1_lido": 0.85, "k2_MEGX": 0.50, "k_decay": 0.0001,
}

SCENARIOS = [
    {
        "name": "Drug-Induced ALF",
        "NH3": 200.0, "lido": 27.0, "urea": 3.5,
        "Q_blood": 155.0, "Hct": 0.34, "duration": 240,  # 4 hr
    },
    {
        "name": "Near Recovery",
        "NH3": 48.0, "lido": 11.0, "urea": 4.8,
        "Q_blood": 140.0, "Hct": 0.35, "duration": 180,  # 3 hr
    },
    {
        "name": "High Flow Adult",
        "NH3": 80.0, "lido": 16.0, "urea": 6.0,
        "Q_blood": 190.0, "Hct": 0.42, "duration": 180,  # 3 hr
    },
    {
        "name": "Anemic Patient",
        "NH3": 110.0, "lido": 19.0, "urea": 4.5,
        "Q_blood": 140.0, "Hct": 0.22, "duration": 120,  # 2 hr
    },
    {
        "name": "Severe Acute Failure",
        "NH3": 350.0, "lido": 28.0, "urea": 2.8,
        "Q_blood": 160.0, "Hct": 0.28, "duration": 360,  # 6 hr
    },
    {
        "name": "Mild Dysfunction",
        "NH3": 55.0, "lido": 12.0, "urea": 3.2,
        "Q_blood": 120.0, "Hct": 0.38, "duration": 240,  # 4 hr
    },
    {
        "name": "Normal Baseline",
        "NH3": 90.0, "lido": 21.0, "urea": 5.0,
        "Q_blood": 150.0, "Hct": 0.32, "duration": 120,  # 2 hr
    },
]


def build_params(sc):
    p = dict(BIO_DEFAULTS)
    p.update({
        "NH3": sc["NH3"], "lido": sc["lido"], "urea": sc["urea"],
        "Q_blood": sc["Q_blood"], "Hct": sc["Hct"],
        "Q_target": 75.0, "duration": sc["duration"],
    })
    return p


def apply_constants(params):
    constants.SEPARATOR_INPUTS["C_NH3_in_nominal"] = params["NH3"]
    constants.SEPARATOR_INPUTS["C_lido_in_nominal"] = params["lido"]
    constants.SEPARATOR_INPUTS["C_urea_in_nominal"] = params["urea"]
    constants.SEPARATOR_INPUTS["Q_blood_nominal"] = params["Q_blood"]
    constants.SEPARATOR_INPUTS["Hct_in_nominal"] = params["Hct"]
    constants.PUMP_THRESHOLDS["Q_target"] = params["Q_target"]
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


def run_scenario(params, adaptive):
    """Mirror of app.run_simulation — 2 stages in series, no Streamlit."""
    orig = {
        "sep": copy.deepcopy(constants.SEPARATOR_INPUTS),
        "pump": copy.deepcopy(constants.PUMP_THRESHOLDS),
        "kin": copy.deepcopy(constants.HEPATOCYTE_KINETICS),
        "vol": copy.deepcopy(constants.BIOREACTOR_VOLUMES),
        "mem": copy.deepcopy(constants.MEMBRANE_TRANSPORT),
        "bio": copy.deepcopy(constants.BIOREACTOR_THRESHOLDS),
    }

    try:
        duration = params["duration"]
        severity = None

        apply_constants(params)

        if adaptive:
            ctrl = AdaptiveBALController()
            severity = ctrl.assess_severity(params["NH3"], params["lido"])
            adj = ctrl.calculate_adjustments(severity, params["NH3"], params["lido"])
            duration = ctrl.apply_adjustments(adj)

        steps = int(duration)

        apply_constants(params)
        sim1 = SimulationEngine(dt=1.0)
        for _ in range(steps):
            sim1.step()

        s1_final = sim1.history[-1]["bioreactor"]
        apply_constants(params)
        constants.SEPARATOR_INPUTS["C_NH3_in_nominal"] = s1_final["C_NH3"]
        constants.SEPARATOR_INPUTS["C_lido_in_nominal"] = s1_final["C_lido"]
        constants.SEPARATOR_INPUTS["C_urea_in_nominal"] = s1_final["C_urea"]

        sim2 = SimulationEngine(dt=1.0)
        for _ in range(steps):
            sim2.step()

        bio2 = sim2.history[-1]["bioreactor"]
        sep1 = sim1.history[-1]["separator"]
        pump1 = sim1.history[-1]["pump"]
        mon2 = sim2.history[-1]["return_monitor"]

        final = {
            "NH3_out": bio2["C_NH3"],
            "lido_out": bio2["C_lido"],
            "urea_out": bio2["C_urea"],
            "viability": bio2.get("cell_viability", bio2.get("viability", None)),
            "Q_plasma": sep1.get("Q_plasma", None),
            "Hct_post": sep1.get("Hct_post", None),
            "pump_Q": pump1.get("Q_current", pump1.get("Q_plasma", None)),
            "monitor_state": mon2.get("state", None),
            "duration_used": duration,
            "severity": severity,
        }

        nh3_clear = (params["NH3"] - final["NH3_out"]) / params["NH3"] if params["NH3"] else 0
        lido_clear = (params["lido"] - final["lido_out"]) / params["lido"] if params["lido"] else 0
        final["NH3_clearance"] = nh3_clear
        final["lido_clearance"] = lido_clear

        # Sanity checks
        issues = []
        if not np.isfinite(final["NH3_out"]):
            issues.append("NH3_out is NaN/Inf")
        if not np.isfinite(final["lido_out"]):
            issues.append("lido_out is NaN/Inf")
        if final["NH3_out"] < 0:
            issues.append(f"NH3 went negative ({final['NH3_out']:.3f})")
        if final["lido_out"] < 0:
            issues.append(f"Lido went negative ({final['lido_out']:.3f})")
        if final["NH3_out"] > params["NH3"] * 1.01:
            issues.append(f"NH3 increased ({params['NH3']:.1f} → {final['NH3_out']:.1f})")
        if final["lido_out"] > params["lido"] * 1.01:
            issues.append(f"Lido increased ({params['lido']:.1f} → {final['lido_out']:.1f})")
        if final["viability"] is not None and (final["viability"] < 0 or final["viability"] > 1.01):
            issues.append(f"Viability out of [0,1] ({final['viability']:.3f})")

        final["issues"] = issues
        final["ok"] = len(issues) == 0
        return final

    finally:
        constants.SEPARATOR_INPUTS.update(orig["sep"])
        constants.PUMP_THRESHOLDS.update(orig["pump"])
        constants.HEPATOCYTE_KINETICS.update(orig["kin"])
        constants.BIOREACTOR_VOLUMES.update(orig["vol"])
        constants.MEMBRANE_TRANSPORT.update(orig["mem"])
        constants.BIOREACTOR_THRESHOLDS.update(orig["bio"])


def main():
    n_total = 0
    n_ok = 0
    errors = []

    for sc in SCENARIOS:
        for adaptive in (False, True):
            n_total += 1
            tag = "adaptive" if adaptive else "manual   "
            label = f"{sc['name']:<24s} [{tag}]"
            try:
                params = build_params(sc)
                r = run_scenario(params, adaptive)
                dur = r["duration_used"]
                status = "PASS" if r["ok"] else "WARN"
                if r["ok"]:
                    n_ok += 1
                print(
                    f"  {status:4s} {label}  "
                    f"dur={int(dur):>4d}min  "
                    f"NH3 {sc['NH3']:>5.1f}->{r['NH3_out']:>5.1f} ({r['NH3_clearance']*100:>5.1f}%)  "
                    f"Lido {sc['lido']:>4.1f}->{r['lido_out']:>4.1f} ({r['lido_clearance']*100:>5.1f}%)  "
                    f"viab={r['viability']:.3f}  "
                    f"mon={r['monitor_state']}"
                )
                if r["issues"]:
                    for issue in r["issues"]:
                        print(f"       - {issue}")
            except Exception as e:
                errors.append((label, str(e)))
                print(f"  FAIL {label}  EXCEPTION: {e}")
                traceback.print_exc()

    print()
    print("=" * 72)
    print(f"Result: {n_ok}/{n_total} scenarios passed cleanly")
    if errors:
        print(f"Exceptions in {len(errors)} runs:")
        for lbl, msg in errors:
            print(f"  - {lbl}: {msg}")
        return 1
    return 0 if n_ok == n_total else 2


if __name__ == "__main__":
    sys.exit(main())
