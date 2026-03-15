# Closed-Loop Orchestrator Implementation Plan (TDD)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python orchestrator that autonomously loops: fetch Monomer results → consult Elnora or BayBE → compile transfer_array → submit workflow → repeat until convergence. Includes a GP-based growth simulator for testing without the real robot.

**Architecture:** Single orchestrator script using Anthropic API tool_use. Each tool is a standalone function in `scripts/tools/`. Mock layer in monomer_client switches between simulator and real MCP via `SIMULATION_MODE` env var. GP surrogate trained on 10 real Round 1 data points generates synthetic growth rates for new conditions.

**Tech Stack:** Python 3.10+, anthropic SDK, BayBE, scikit-learn (GP), scipy (stats/sampling), pandas, numpy, requests

**Key Reference Files:**
- Round 1 data: `data/PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ_growth.csv`
- Round 1 conditions: `data/PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ_plate_condition_map.csv`
- BayBE optimizer: `scripts/baybe_opt.py`
- Agent (cannibalize): `scripts/agent.py`
- Monomer MCP spec: `monomer-bio-hackathon/CLAUDE.md`
- Reagent compatibility: `Notion/Reagent-Compatibility-Guide.md`
- Elnora project ID: `82d10329-f194-44e8-be72-e2a65bb94a7c`

---

### Task 1: Project Structure & Analyzer

**Files:**
- Create: `scripts/tools/__init__.py`
- Create: `scripts/tools/analyzer.py`
- Create: `tests/test_analyzer.py`

**Step 1: Create package and write the failing test**

```bash
mkdir -p scripts/tools tests
touch scripts/tools/__init__.py
```

Create `tests/test_analyzer.py`:

```python
"""Tests for growth data analyzer."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

DATA_DIR = Path(__file__).parent.parent / "data"
GROWTH_CSV = str(DATA_DIR / "PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ_growth.csv")


def test_analyze_returns_ranked_conditions():
    from tools.analyzer import analyze_results
    result = analyze_results(GROWTH_CSV)
    assert "ranked_conditions" in result
    assert result["n_conditions"] == 10
    # Best should be HB-1 with highest growth rate
    assert result["best_growth_rate"] > 1.5


def test_analyze_best_condition_is_hb1():
    from tools.analyzer import analyze_results
    result = analyze_results(GROWTH_CSV)
    assert "HB-1" in result["best_condition"]


def test_analyze_computes_se():
    from tools.analyzer import analyze_results
    result = analyze_results(GROWTH_CSV)
    assert result["best_se"] > 0
    assert result["best_se"] < 1.0  # sanity check


def test_analyze_convergence_false_on_first_round():
    from tools.analyzer import analyze_results
    result = analyze_results(GROWTH_CSV, previous_best_rate=0.0)
    assert result["converged"] is False


def test_analyze_convergence_true_when_same():
    from tools.analyzer import analyze_results
    result = analyze_results(GROWTH_CSV, previous_best_rate=1.616)
    # Same rate with SE overlap → converged
    assert result["converged"] is True


def test_analyze_missing_file():
    from tools.analyzer import analyze_results
    result = analyze_results("/nonexistent/file.csv")
    assert "error" in result
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_analyzer.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.analyzer'`

**Step 3: Write minimal implementation**

Create `scripts/tools/analyzer.py`:

```python
"""Analyze Monomer growth data: rank conditions, compute CI, check convergence."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def analyze_results(current_round_csv: str, previous_best_rate: float = 0.0) -> dict:
    """Parse growth CSV, rank by growth rate, compute confidence intervals."""
    growth_path = Path(current_round_csv)
    if not growth_path.exists():
        return {"error": f"File not found: {current_round_csv}"}

    df = pd.read_csv(growth_path)

    required = ["well", "condition_id", "growth_rate_per_hr", "max_absorbance_OD600"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return {"error": f"Missing columns: {missing}"}

    ranked = df.sort_values("growth_rate_per_hr", ascending=False).reset_index(drop=True)
    ranked["rank"] = range(1, len(ranked) + 1)

    best = ranked.iloc[0]
    best_rate = float(best["growth_rate_per_hr"])
    best_condition = str(best["condition_id"])

    # Compute SE from replicates file if available
    rep_path = growth_path.parent / growth_path.name.replace("_growth.csv", "_replicates.csv")
    best_se = 0.05
    if rep_path.exists():
        rep_df = pd.read_csv(rep_path)
        if "variance_growth_rate_per_hr" in rep_df.columns:
            condition_prefix = best_condition.split("_")[0]
            best_rep = rep_df[rep_df["condition_id"].str.startswith(condition_prefix)]
            if not best_rep.empty:
                var_val = best_rep["variance_growth_rate_per_hr"].iloc[0]
                n = best_rep["n_replicates"].iloc[0] if "n_replicates" in best_rep.columns else 1
                if pd.notna(var_val) and n > 0:
                    best_se = float(np.sqrt(var_val) / np.sqrt(n))

    converged = False
    if previous_best_rate > 0 and best_se > 0:
        ci_curr = (best_rate - 1.96 * best_se, best_rate + 1.96 * best_se)
        ci_prev = (previous_best_rate - 1.96 * best_se, previous_best_rate + 1.96 * best_se)
        converged = ci_curr[0] <= ci_prev[1] and ci_prev[0] <= ci_curr[1]

    summary_rows = []
    for _, row in ranked.iterrows():
        summary_rows.append({
            "rank": int(row["rank"]),
            "condition": str(row["condition_id"]),
            "well": str(row["well"]),
            "growth_rate": round(float(row["growth_rate_per_hr"]), 4),
            "max_od600": round(float(row["max_absorbance_OD600"]), 4),
        })

    return {
        "n_conditions": len(ranked),
        "best_condition": best_condition,
        "best_growth_rate": round(best_rate, 4),
        "best_se": round(best_se, 4),
        "converged": converged,
        "previous_best_rate": previous_best_rate,
        "ranked_conditions": summary_rows,
    }
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_analyzer.py -v
```

Expected: 6 passed

**Step 5: Commit**

```bash
git add scripts/tools/__init__.py scripts/tools/analyzer.py tests/test_analyzer.py
git commit -m "feat: analyzer tool with TDD — parse growth CSV, rank, compute CI"
```

---

### Task 2: Validators (Convergence + Precipitation)

**Files:**
- Create: `scripts/tools/validators.py`
- Create: `tests/test_validators.py`

**Step 1: Write the failing test**

Create `tests/test_validators.py`:

```python
"""Tests for validators — convergence check and precipitation rules."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_convergence_overlapping_ci():
    from tools.validators import check_convergence
    result = check_convergence(
        current_best_rate=1.62, current_best_se=0.05,
        previous_best_rate=1.60, previous_best_se=0.05,
    )
    assert result["converged"] is True


def test_convergence_non_overlapping_ci():
    from tools.validators import check_convergence
    result = check_convergence(
        current_best_rate=2.0, current_best_se=0.05,
        previous_best_rate=1.0, previous_best_se=0.05,
    )
    assert result["converged"] is False


def test_convergence_improvement_pct():
    from tools.validators import check_convergence
    result = check_convergence(
        current_best_rate=1.8, current_best_se=0.05,
        previous_best_rate=1.5, previous_best_se=0.05,
    )
    assert result["improvement_pct"] > 0
    assert "CONTINUE" in result["recommendation"]


def test_convergence_stop_recommendation():
    from tools.validators import check_convergence
    result = check_convergence(
        current_best_rate=1.62, current_best_se=0.1,
        previous_best_rate=1.60, previous_best_se=0.1,
    )
    assert "STOP" in result["recommendation"]
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_validators.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `scripts/tools/validators.py`:

```python
"""Validation tools — convergence check, precipitation rules."""
from __future__ import annotations


PRECIPITATION_RULES = [
    {"pair": ("CaCl2", "K2HPO4"), "action": "NEVER", "fix": "Use KH2PO4"},
    {"pair": ("CaCl2", "Novel Bio"), "action": "NEVER", "fix": "No CaCl2 with Novel Bio"},
    {"pair": ("MgSO4", "K2HPO4"), "action": "CONDITIONAL", "fix": "Add >=12.5mM citrate or use KH2PO4"},
    {"pair": ("FeSO4", "K2HPO4"), "action": "NEVER", "fix": "Use KH2PO4 at low iron"},
]


def check_convergence(
    current_best_rate: float,
    current_best_se: float,
    previous_best_rate: float,
    previous_best_se: float,
) -> dict:
    """Check if 95% CIs overlap between rounds."""
    ci_current = (
        current_best_rate - 1.96 * current_best_se,
        current_best_rate + 1.96 * current_best_se,
    )
    ci_previous = (
        previous_best_rate - 1.96 * previous_best_se,
        previous_best_rate + 1.96 * previous_best_se,
    )

    overlap = ci_current[0] <= ci_previous[1] and ci_previous[0] <= ci_current[1]

    improvement_pct = (
        ((current_best_rate - previous_best_rate) / previous_best_rate * 100)
        if previous_best_rate > 0 else float("inf")
    )

    return {
        "converged": overlap,
        "current_ci": [round(ci_current[0], 4), round(ci_current[1], 4)],
        "previous_ci": [round(ci_previous[0], 4), round(ci_previous[1], 4)],
        "improvement_pct": round(improvement_pct, 2),
        "recommendation": "STOP — converged" if overlap else "CONTINUE — improvement detected",
    }
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_validators.py -v
```

Expected: 4 passed

**Step 5: Commit**

```bash
git add scripts/tools/validators.py tests/test_validators.py
git commit -m "feat: validators — convergence check with CI overlap"
```

---

### Task 3: Growth Simulator

**Files:**
- Create: `scripts/tools/growth_simulator.py`
- Create: `tests/test_growth_simulator.py`

**Step 1: Write the failing tests**

Create `tests/test_growth_simulator.py`:

```python
"""Tests for GP-based growth simulator."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

DATA_DIR = Path(__file__).parent.parent / "data"


def test_simulator_initializes_with_round1_data():
    from tools.growth_simulator import GrowthSimulator
    sim = GrowthSimulator(data_dir=DATA_DIR)
    assert sim._gp is not None, "GP should be fitted on Round 1 data"


def test_different_conditions_give_different_rates():
    from tools.growth_simulator import GrowthSimulator
    sim = GrowthSimulator(data_dir=DATA_DIR)

    # HB-1 like condition (high tryptone, some glutamate)
    cond_a = {"base_media_vol": 110, "yeast_extract": 14, "tryptone": 26,
              "mops": 0, "na_l_glut": 10, "kh2po4": 0, "glucose": 0}
    # Very different condition
    cond_b = {"base_media_vol": 130, "yeast_extract": 0, "tryptone": 0,
              "mops": 18, "na_l_glut": 0, "kh2po4": 10, "glucose": 18}

    rate_a = sim.predict_growth_rate(cond_a)
    rate_b = sim.predict_growth_rate(cond_b)

    assert rate_a > 0
    assert rate_b > 0
    assert abs(rate_a - rate_b) > 0.01, f"Rates should differ: {rate_a} vs {rate_b}"


def test_workflow_lifecycle():
    from tools.growth_simulator import GrowthSimulator, DELAY_SECONDS
    sim = GrowthSimulator(data_dir=DATA_DIR)

    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "B2", "volume": 110},
        {"src_plate": "reagent", "src_well": "A1", "dst_plate": "experiment",
         "dst_well": "B2", "volume": 14},
    ]

    result = sim.instantiate_workflow(transfers, ["B2"], "TEST_PLATE_1")
    wf_id = result["workflow_id"]
    assert wf_id

    # Initially in_progress
    status = sim.get_workflow_instance_details(wf_id)
    assert status["status"] == "in_progress"

    # Wait for completion
    time.sleep(DELAY_SECONDS + 1)
    status = sim.get_workflow_instance_details(wf_id)
    assert status["status"] == "completed"

    # Results available
    obs = sim.get_plate_observations("TEST_PLATE_1")
    assert len(obs["observations"]) > 0
    assert obs["observations"][0]["growth_rate_per_hr"] > 0


def test_simulator_generates_od600_timeseries():
    from tools.growth_simulator import GrowthSimulator
    sim = GrowthSimulator(data_dir=DATA_DIR)

    ts = sim._generate_od600_timeseries(growth_rate=1.5, n_points=9)
    assert len(ts) == 9
    assert all("time_hr" in p and "od600" in p for p in ts)
    # OD should generally increase over time
    assert ts[-1]["od600"] > ts[0]["od600"]


def test_simulator_refits_gp_after_new_data():
    from tools.growth_simulator import GrowthSimulator, DELAY_SECONDS
    sim = GrowthSimulator(data_dir=DATA_DIR)

    n_before = len(sim._history)

    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "C3", "volume": 110},
    ]
    result = sim.instantiate_workflow(transfers, ["C3"], "REFIT_PLATE")
    time.sleep(DELAY_SECONDS + 1)
    sim.get_workflow_instance_details(result["workflow_id"])

    assert len(sim._history) > n_before, "History should grow after new data"


def test_extrapolation_returns_baseline_with_noise():
    from tools.growth_simulator import GrowthSimulator
    sim = GrowthSimulator(data_dir=DATA_DIR)

    # Extreme condition far from training data
    cond_extreme = {"base_media_vol": 180, "yeast_extract": 0, "tryptone": 0,
                    "mops": 0, "na_l_glut": 0, "kh2po4": 0, "glucose": 0}

    rates = [sim.predict_growth_rate(cond_extreme) for _ in range(10)]
    # Should be around baseline (~1.0) with large noise, not extreme values
    mean_rate = sum(rates) / len(rates)
    assert 0.3 < mean_rate < 2.0, f"Extrapolation should stay reasonable: {mean_rate}"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_growth_simulator.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `scripts/tools/growth_simulator.py`:

```python
"""Growth simulator — GP surrogate trained on real Round 1 data.

Predicts growth rates for new conditions, adds biological noise,
generates synthetic OD600 time-series, manages workflow state with
configurable delay for testing polling logic.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.preprocessing import StandardScaler

REAGENT_COLS = [
    "base_media_vol", "yeast_extract", "tryptone",
    "mops", "na_l_glut", "kh2po4", "glucose",
]
NOISE_STD = 0.08
DELAY_SECONDS = 5


@dataclass
class SimulatedWorkflow:
    workflow_id: str
    plate_barcode: str
    conditions: list[dict]
    monitoring_wells: list[str]
    submitted_at: float
    delay: float = DELAY_SECONDS
    status: str = "in_progress"

    @property
    def is_complete(self) -> bool:
        return (time.time() - self.submitted_at) >= self.delay


class GrowthSimulator:
    """GP surrogate trained on real data, generates synthetic growth results."""

    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
        self.data_dir = Path(data_dir)
        self._gp = None
        self._scaler = StandardScaler()
        self._vol_cols: list[str] = []
        self._history: pd.DataFrame = pd.DataFrame()
        self._workflows: dict[str, SimulatedWorkflow] = {}
        self._plates: dict[str, list[dict]] = {}
        self._rng = np.random.default_rng(42)
        self._fit_gp()

    def _fit_gp(self) -> None:
        """Train GP on all available historical data."""
        growth_files = sorted(self.data_dir.glob("*_growth.csv"))

        all_rows = []
        for gf in growth_files:
            prefix = gf.name.replace("_growth.csv", "")
            mf = self.data_dir / f"{prefix}_plate_condition_map.csv"
            if not mf.exists():
                continue
            growth = pd.read_csv(gf)
            maps = pd.read_csv(mf)
            merged = growth[["well", "growth_rate_per_hr"]].merge(maps, on="well", how="inner")
            all_rows.append(merged)

        if not all_rows:
            return

        df = pd.concat(all_rows, ignore_index=True)
        self._history = df

        self._vol_cols = [c for c in REAGENT_COLS if c in df.columns]
        X = df[self._vol_cols].fillna(0).values.astype(float)
        y = df["growth_rate_per_hr"].values.astype(float)

        if len(X) < 2:
            return

        self._scaler.fit(X)
        X_scaled = self._scaler.transform(X)

        kernel = ConstantKernel(1.0) * Matern(nu=2.5) + WhiteKernel(noise_level=0.01)
        self._gp = GaussianProcessRegressor(
            kernel=kernel, n_restarts_optimizer=5,
            normalize_y=True, random_state=42,
        )
        self._gp.fit(X_scaled, y)

    def predict_growth_rate(self, condition: dict) -> float:
        """Predict growth rate for a single condition using GP + noise."""
        if self._gp is None:
            return 0.8 + self._rng.normal(0, NOISE_STD)

        x = np.array([[condition.get(c, 0.0) for c in self._vol_cols]])
        x_scaled = self._scaler.transform(x)

        # Check extrapolation distance
        X_train = self._scaler.transform(
            self._history[self._vol_cols].fillna(0).values
        )
        min_dist = float(np.min(np.linalg.norm(X_train - x_scaled, axis=1)))

        if min_dist > 2.0:
            return 1.0 + self._rng.normal(0, NOISE_STD * 3)

        mu, _ = self._gp.predict(x_scaled, return_std=True)
        rate = float(mu[0]) + self._rng.normal(0, NOISE_STD)
        return max(0.1, rate)

    def _generate_od600_timeseries(self, growth_rate: float, n_points: int = 9) -> list[dict]:
        """Generate synthetic OD600 logistic growth curve."""
        times_hr = np.linspace(0, 1.5, n_points)
        od_max = 0.3 + self._rng.uniform(0, 0.3)
        od_0 = 0.08 + self._rng.normal(0, 0.01)

        od_values = od_max / (1 + ((od_max - od_0) / max(od_0, 0.01)) * np.exp(-growth_rate * times_hr))
        od_values += self._rng.normal(0, 0.005, n_points)
        od_values = np.clip(od_values, 0.05, 1.0)

        return [
            {"time_hr": round(float(t), 4), "od600": round(float(od), 4)}
            for t, od in zip(times_hr, od_values)
        ]

    def instantiate_workflow(self, transfer_array: list[dict],
                             monitoring_wells: list[str],
                             plate_barcode: str, **kwargs) -> dict:
        wf_id = str(uuid.uuid4())[:8]
        conditions = self._parse_conditions(transfer_array)
        wf = SimulatedWorkflow(
            workflow_id=wf_id, plate_barcode=plate_barcode,
            conditions=conditions, monitoring_wells=monitoring_wells,
            submitted_at=time.time(),
        )
        self._workflows[wf_id] = wf
        return {"workflow_id": wf_id, "status": "pending_approval"}

    def get_workflow_instance_details(self, workflow_id: str) -> dict:
        wf = self._workflows.get(workflow_id)
        if wf is None:
            return {"error": f"Unknown workflow: {workflow_id}"}
        if wf.is_complete and wf.status == "in_progress":
            wf.status = "completed"
            self._generate_results(wf)
        return {"workflow_id": workflow_id, "status": wf.status}

    def get_plate_observations(self, plate_barcode: str) -> dict:
        results = self._plates.get(plate_barcode, [])
        if not results:
            return {"plate": plate_barcode, "observations": [], "status": "no_data"}
        return {"plate": plate_barcode, "observations": results}

    def list_culture_plates(self) -> dict:
        return {"plates": list(self._plates.keys())}

    def _parse_conditions(self, transfer_array: list[dict]) -> list[dict]:
        wells: dict[str, dict] = {}
        for t in transfer_array:
            dst = t.get("dst_well", "")
            if t.get("dst_plate") != "experiment":
                continue
            if dst not in wells:
                wells[dst] = {c: 0.0 for c in self._vol_cols}
            src_well = t.get("src_well", "")
            vol = float(t.get("volume", 0))
            # Map known source wells to reagent columns
            well_to_col = {
                "D1": "base_media_vol", "D2": "base_media_vol",
                "D3": "base_media_vol", "D4": "base_media_vol",
                "A1": "yeast_extract", "A2": "tryptone",
                "A3": "mops", "A4": "na_l_glut",
                "B1": "kh2po4", "B2": "glucose",
            }
            col = well_to_col.get(src_well)
            if col and col in wells[dst]:
                wells[dst][col] += vol
        return [{"well": w, **cond} for w, cond in wells.items()]

    def _generate_results(self, wf: SimulatedWorkflow) -> None:
        results = []
        for cond in wf.conditions:
            rate = self.predict_growth_rate(cond)
            timeseries = self._generate_od600_timeseries(rate)
            results.append({
                "well": cond["well"],
                "growth_rate_per_hr": round(rate, 4),
                "max_absorbance_OD600": round(max(p["od600"] for p in timeseries), 4),
                "timeseries": timeseries,
                "condition_id": f"sim_{cond['well']}",
            })
        self._plates[wf.plate_barcode] = results

        # Refit GP with new data
        new_rows = []
        for r in results:
            row = {c: 0.0 for c in self._vol_cols}
            matching = [c for c in wf.conditions if c["well"] == r["well"]]
            if matching:
                row.update({k: v for k, v in matching[0].items() if k in self._vol_cols})
            row["growth_rate_per_hr"] = r["growth_rate_per_hr"]
            row["well"] = r["well"]
            new_rows.append(row)

        if new_rows and self._gp is not None:
            new_df = pd.DataFrame(new_rows)
            self._history = pd.concat([self._history, new_df], ignore_index=True)
            self._fit_gp()
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_growth_simulator.py -v
```

Expected: 6 passed (note: `test_workflow_lifecycle` and `test_simulator_refits` take ~6s each due to sleep)

**Step 5: Commit**

```bash
git add scripts/tools/growth_simulator.py tests/test_growth_simulator.py
git commit -m "feat: growth simulator — GP surrogate with workflow lifecycle"
```

---

### Task 4: Monomer Client (with SIMULATION_MODE)

**Files:**
- Create: `scripts/tools/monomer_client.py`
- Create: `tests/test_monomer_client.py`

**Step 1: Write the failing test**

Create `tests/test_monomer_client.py`:

```python
"""Tests for Monomer client — simulation mode."""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
os.environ["SIMULATION_MODE"] = "1"

DATA_DIR = Path(__file__).parent.parent / "data"
PLATE_ID = "PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ"


def test_fetch_results_from_local_csv():
    from tools.monomer_client import fetch_results
    result = fetch_results(PLATE_ID)
    assert result["source"] in ("local_csv", "simulator")
    assert result["n_wells"] == 10
    assert result["results"][0]["growth_rate"] > 1.5  # best is HB-1


def test_submit_in_simulation_mode():
    from tools.monomer_client import monomer_submit
    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "B2", "volume": 110},
    ]
    result = monomer_submit(
        transfer_array_json=json.dumps(transfers),
        monitoring_wells=["B2"],
        plate_barcode="SIM_TEST_PLATE",
        round_label="test_round",
    )
    assert "workflow_id" in result or "status" in result


def test_wait_for_workflow_completes():
    from tools.monomer_client import monomer_submit, wait_for_workflow
    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "B2", "volume": 110},
    ]
    submit_result = monomer_submit(
        transfer_array_json=json.dumps(transfers),
        monitoring_wells=["B2"],
        plate_barcode="WAIT_TEST_PLATE",
    )
    wf_id = submit_result.get("workflow_id", "")
    if wf_id:
        status = wait_for_workflow(wf_id, timeout=15, poll_interval=1.0)
        assert status.get("status") == "completed"


def test_fetch_simulated_results_after_workflow():
    from tools.monomer_client import monomer_submit, wait_for_workflow, fetch_results
    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "C4", "volume": 110},
        {"src_plate": "reagent", "src_well": "A1", "dst_plate": "experiment",
         "dst_well": "C4", "volume": 20},
    ]
    submit_result = monomer_submit(
        transfer_array_json=json.dumps(transfers),
        monitoring_wells=["C4"],
        plate_barcode="FETCH_SIM_PLATE",
    )
    wf_id = submit_result.get("workflow_id", "")
    if wf_id:
        wait_for_workflow(wf_id, timeout=15)
        result = fetch_results("FETCH_SIM_PLATE")
        assert result.get("n_wells", 0) > 0
        assert result["results"][0]["growth_rate"] > 0
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/viachealavrudenko/Cell.ai && SIMULATION_MODE=1 python -m pytest tests/test_monomer_client.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `scripts/tools/monomer_client.py`:

```python
"""Monomer MCP client — fetch results and submit workflows.

Set SIMULATION_MODE=1 to use GP-based growth simulator instead of real Monomer.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).parent.parent.parent / "data"

SIMULATION_MODE = os.environ.get("SIMULATION_MODE", "0") == "1"
AUTOPLAT_URL = "http://192.168.68.60:8080/mcp"
MONITOR_URL = "https://backend-staging.monomerbio.com/mcp"
MONITOR_TOKEN = os.environ.get("MONOMER_TOKEN", "")

_simulator = None


def _get_simulator():
    global _simulator
    if _simulator is None:
        from tools.growth_simulator import GrowthSimulator
        _simulator = GrowthSimulator(data_dir=DATA_DIR)
    return _simulator


def _mcp_call(url: str, method: str, params: dict, token: str = "") -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": method, "arguments": params},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"MCP error: {data['error']}")
    return data.get("result", {})


def fetch_results(plate_id: str) -> dict:
    """Fetch growth rate results for a plate."""
    # Try local CSV first
    growth_csv = DATA_DIR / f"{plate_id}_growth.csv"
    if growth_csv.exists():
        df = pd.read_csv(growth_csv)
        results = []
        for _, row in df.iterrows():
            results.append({
                "well": row["well"],
                "condition": row["condition_id"],
                "growth_rate": round(float(row["growth_rate_per_hr"]), 4),
                "max_od600": round(float(row["max_absorbance_OD600"]), 4),
            })
        results.sort(key=lambda x: x["growth_rate"], reverse=True)
        return {"plate_id": plate_id, "source": "local_csv",
                "n_wells": len(results), "results": results}

    # Simulation mode
    if SIMULATION_MODE:
        sim = _get_simulator()
        obs = sim.get_plate_observations(plate_id)
        if obs.get("observations"):
            results = [
                {"well": w["well"], "condition": w["condition_id"],
                 "growth_rate": w["growth_rate_per_hr"],
                 "max_od600": w["max_absorbance_OD600"]}
                for w in obs["observations"]
            ]
            results.sort(key=lambda x: x["growth_rate"], reverse=True)
            return {"plate_id": plate_id, "source": "simulator",
                    "n_wells": len(results), "results": results}
        return {"plate_id": plate_id, "source": "simulator", "status": "no_data"}

    # Real Monomer MCP
    try:
        data = _mcp_call(MONITOR_URL, "get_plate_observations",
                         {"plate_name": plate_id}, token=MONITOR_TOKEN)
        return {"plate_id": plate_id, "source": "monomer_mcp", "raw": data}
    except Exception as e:
        return {"error": f"Cannot fetch results for {plate_id}: {e}"}


def monomer_submit(transfer_array_json: str, monitoring_wells: list[str],
                   plate_barcode: str, round_label: str = "") -> dict:
    """Submit a workflow."""
    transfers = json.loads(transfer_array_json) if isinstance(transfer_array_json, str) else transfer_array_json

    if SIMULATION_MODE:
        sim = _get_simulator()
        result = sim.instantiate_workflow(transfers, monitoring_wells, plate_barcode)
        return {"status": "submitted_to_simulator", **result}

    # Save locally + try MCP
    output_dir = DATA_DIR.parent / "workflows"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"workflow_{round_label or 'next'}.json"
    with open(output_file, "w") as f:
        json.dump({"transfer_array": transfers, "monitoring_wells": monitoring_wells,
                    "plate_barcode": plate_barcode}, f, indent=2)

    try:
        result = _mcp_call(AUTOPLAT_URL, "instantiate_workflow", {
            "definition_name": "hackathon_closed_loop",
            "plate_barcode": plate_barcode,
            "extra_inputs": {
                "transfer_array": json.dumps(transfers),
                "monitoring_wells": json.dumps(monitoring_wells),
            },
            "reason": round_label,
        })
        return {"status": "submitted", "workflow_file": str(output_file), "mcp_result": result}
    except Exception as e:
        return {"status": "saved_locally", "workflow_file": str(output_file), "mcp_error": str(e)}


def wait_for_workflow(workflow_id: str, timeout: int = 30, poll_interval: float = 1.0) -> dict:
    """Poll workflow status until complete or timeout."""
    if SIMULATION_MODE:
        sim = _get_simulator()
        start = time.time()
        while time.time() - start < timeout:
            status = sim.get_workflow_instance_details(workflow_id)
            if status.get("status") == "completed":
                return status
            time.sleep(poll_interval)
        return {"error": "timeout", "workflow_id": workflow_id}

    start = time.time()
    while time.time() - start < timeout:
        try:
            result = _mcp_call(AUTOPLAT_URL, "get_workflow_instance_details",
                               {"workflow_id": workflow_id})
            if result.get("status") in ("completed", "failed"):
                return result
        except Exception:
            pass
        time.sleep(poll_interval)
    return {"error": "timeout", "workflow_id": workflow_id}
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/viachealavrudenko/Cell.ai && SIMULATION_MODE=1 python -m pytest tests/test_monomer_client.py -v
```

Expected: 4 passed (some take ~6s due to workflow delay)

**Step 5: Commit**

```bash
git add scripts/tools/monomer_client.py tests/test_monomer_client.py
git commit -m "feat: monomer client with SIMULATION_MODE switch"
```

---

### Task 5: Elnora Client

**Files:**
- Create: `scripts/tools/elnora_client.py`
- Create: `tests/test_elnora_client.py`

**Step 1: Write the failing test**

Create `tests/test_elnora_client.py`:

```python
"""Tests for Elnora client — tests CLI wrapper structure (no live calls in CI)."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_elnora_design_builds_correct_prompt():
    """Verify the prompt template is well-formed."""
    from tools.elnora_client import elnora_design

    with patch("tools.elnora_client._create_task") as mock_create, \
         patch("tools.elnora_client._get_messages") as mock_msgs:
        mock_create.return_value = {"id": "fake-uuid"}
        mock_msgs.return_value = [
            {"role": "assistant", "content": "Proposed conditions: ..."}
        ]

        result = elnora_design(
            results_summary="| HB-1 | 1.616 |",
            round_number=2,
            n_conditions=10,
        )

        assert result["task_id"] == "fake-uuid"
        assert result["round"] == 2
        assert len(result["elnora_response"]) > 0

        # Verify prompt contains key elements
        call_args = mock_create.call_args
        prompt = call_args[0][1]  # second positional arg = message
        assert "V. natriegens" in prompt
        assert "10 conditions" in prompt
        assert "Round 2" in prompt


def test_elnora_validate_builds_correct_prompt():
    from tools.elnora_client import elnora_validate

    with patch("tools.elnora_client._create_task") as mock_create, \
         patch("tools.elnora_client._get_messages") as mock_msgs:
        mock_create.return_value = {"id": "fake-uuid-2"}
        mock_msgs.return_value = [
            {"role": "assistant", "content": "ALL CLEAR"}
        ]

        result = elnora_validate("| HB-R2-1 | YE 7 | Tryp 15 | Glut 60 |")

        assert result["task_id"] == "fake-uuid-2"
        assert "ALL CLEAR" in result["validation_result"]
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_elnora_client.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `scripts/tools/elnora_client.py`:

```python
"""Elnora AI client — wraps elnora CLI for experiment design and validation."""
from __future__ import annotations

import json
import subprocess

ELNORA_PROJECT_ID = "82d10329-f194-44e8-be72-e2a65bb94a7c"
ELNORA_CLI = "elnora"


def _run_elnora(args: list[str], timeout: int = 180) -> str:
    result = subprocess.run(
        [ELNORA_CLI] + args, capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"elnora CLI error: {result.stderr}")
    return result.stdout


def _create_task(title: str, message: str) -> dict:
    output = _run_elnora([
        "tasks", "create",
        "--project", ELNORA_PROJECT_ID,
        "--title", title,
        "--message", message,
    ])
    return json.loads(output)


def _send_message(task_id: str, message: str) -> dict:
    output = _run_elnora(["tasks", "send", task_id, "--message", message])
    return json.loads(output)


def _get_messages(task_id: str) -> list[dict]:
    output = _run_elnora(["tasks", "messages", task_id])
    data = json.loads(output)
    return data.get("items", [])


def elnora_design(
    results_summary: str,
    round_number: int,
    n_conditions: int = 10,
    specific_question: str = "",
) -> dict:
    prompt = f"""We are optimizing V. natriegens growth media on a Monomer Bio workcell.

## Current Results (Round {round_number - 1})
{results_summary}

## Constraints
- {n_conditions} conditions for Round {round_number}
- 200 uL final volume (180 uL reagent + 20 uL cells)
- Min pipettable volume: 5 uL
- Available bases: Semi-Defined, High Buffer Defined
- Available stocks: Tryptone 100mg/mL, YE 100mg/mL, NaCl 5M, Glucose 100mg/mL, MOPS 1M, KH2PO4 1M, Na L-Glutamate 1M, MgSO4 1M

## Task
Propose {n_conditions} conditions (final concentrations only) to maximize growth rate.
Focus on EXPLOIT: tighten ranges around the best performers.

{specific_question}

Format as a markdown table: Condition | Base Media | Component1 | Component2 | Component3"""

    task_data = _create_task(f"Round {round_number} experiment design", prompt)
    task_id = task_data.get("id", "")
    messages = _get_messages(task_id)

    assistant_reply = ""
    for msg in messages:
        if msg.get("role") == "assistant":
            assistant_reply = msg.get("content", "")

    return {"task_id": task_id, "elnora_response": assistant_reply, "round": round_number}


def elnora_validate(conditions_table: str) -> dict:
    prompt = f"""Please validate these proposed V. natriegens media conditions.

## Proposed Conditions
{conditions_table}

## Check for:
1. Precipitation risks (divalent cations + phosphate)
2. Osmolarity concerns (high NaCl + high glucose)
3. Known inhibition thresholds for any component
4. pH buffering adequacy
5. Biologically unreasonable concentrations

For each issue, specify which condition and what to change.
If all safe, say "ALL CLEAR"."""

    task_data = _create_task("Condition validation check", prompt)
    task_id = task_data.get("id", "")
    messages = _get_messages(task_id)

    assistant_reply = ""
    for msg in messages:
        if msg.get("role") == "assistant":
            assistant_reply = msg.get("content", "")

    return {"task_id": task_id, "validation_result": assistant_reply}
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_elnora_client.py -v
```

Expected: 2 passed

**Step 5: Commit**

```bash
git add scripts/tools/elnora_client.py tests/test_elnora_client.py
git commit -m "feat: elnora client — design and validate via CLI with mocked tests"
```

---

### Task 6: BayBE Tools

**Files:**
- Create: `scripts/tools/baybe_tools.py`
- Create: `tests/test_baybe_tools.py`

**Step 1: Write the failing test**

Create `tests/test_baybe_tools.py`:

```python
"""Tests for BayBE optimization tool."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_baybe_propose_returns_conditions():
    from tools.baybe_tools import baybe_propose
    result = baybe_propose(n_proposals=5, round_number=2)
    assert "proposed_conditions" in result
    assert len(result["proposed_conditions"]) == 5
    assert result["n_historical_conditions"] > 0


def test_baybe_conditions_have_required_fields():
    from tools.baybe_tools import baybe_propose
    result = baybe_propose(n_proposals=3, round_number=2)
    for cond in result["proposed_conditions"]:
        assert "base_media" in cond
        assert "base_media_vol" in cond
        assert "predicted_growth_rate_per_hr" in cond


def test_baybe_predicted_rates_are_positive():
    from tools.baybe_tools import baybe_propose
    result = baybe_propose(n_proposals=5)
    for cond in result["proposed_conditions"]:
        rate = cond.get("predicted_growth_rate_per_hr", 0)
        # NaN is acceptable if GP can't predict, but non-NaN should be positive
        if rate == rate:  # not NaN
            assert rate > 0, f"Predicted rate should be positive: {rate}"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_baybe_tools.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `scripts/tools/baybe_tools.py`:

```python
"""BayBE optimization tool — wraps baybe_opt.py for the orchestrator."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from baybe_opt import GrowthRatePredictor, load_history, propose_conditions, format_output

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def baybe_propose(n_proposals: int = 10, round_number: int | None = None) -> dict:
    """Run BayBE optimization and return proposed conditions."""
    try:
        history = load_history(str(DATA_DIR))
    except FileNotFoundError as e:
        return {"error": str(e)}

    n_unique = len(history)
    n_media = history["base_media"].nunique()
    rate_range = (float(history["mean_growth_rate_per_hr"].min()),
                  float(history["mean_growth_rate_per_hr"].max()))

    proposals = propose_conditions(history, n_proposals=n_proposals)

    predictor = GrowthRatePredictor()
    if len(history) >= 2:
        predictor.fit(history)
        predicted = predictor.predict(proposals)
    else:
        predicted = np.full(len(proposals), np.nan)

    output_df = format_output(proposals, predicted, round_num=round_number)
    conditions = output_df.to_dict(orient="records")

    return {
        "n_proposals": len(conditions),
        "n_historical_conditions": n_unique,
        "n_media_types": n_media,
        "historical_rate_range": rate_range,
        "proposed_conditions": conditions,
    }
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_baybe_tools.py -v
```

Expected: 3 passed

**Step 5: Commit**

```bash
git add scripts/tools/baybe_tools.py tests/test_baybe_tools.py
git commit -m "feat: baybe tool — wraps baybe_opt for orchestrator"
```

---

### Task 7: Protocol Compiler

**Files:**
- Create: `scripts/tools/compiler.py`
- Create: `tests/test_compiler.py`

**Step 1: Write the failing test**

Create `tests/test_compiler.py`:

```python
"""Tests for protocol compiler — conditions to transfer_array."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_compile_single_condition():
    from tools.compiler import compile_protocol
    conditions = [
        {"base_media": "High Buffer Defined Media", "base_media_vol": 110,
         "yeast_extract": 14, "tryptone": 26, "na_l_glut": 10},
    ]
    result = compile_protocol(json.dumps(conditions), ["B2"])
    assert result["n_transfers"] > 0
    assert len(result["errors"]) == 0
    assert result["well_summaries"][0]["well"] == "B2"


def test_compile_total_volume_is_200():
    from tools.compiler import compile_protocol
    conditions = [
        {"base_media": "High Buffer Defined Media", "base_media_vol": 110,
         "yeast_extract": 14, "tryptone": 26, "na_l_glut": 10},
    ]
    result = compile_protocol(json.dumps(conditions), ["B2"])
    total = result["well_summaries"][0]["total"]
    assert abs(total - 200) < 1.0, f"Total should be 200, got {total}"


def test_compile_includes_cell_seeding():
    from tools.compiler import compile_protocol
    conditions = [
        {"base_media": "High Buffer Defined Media", "base_media_vol": 110,
         "yeast_extract": 14, "tryptone": 26},
    ]
    result = compile_protocol(json.dumps(conditions), ["B2"])
    cell_transfers = [t for t in result["transfer_array"]
                      if t["src_plate"] == "cell_culture_stock"]
    assert len(cell_transfers) == 1
    assert cell_transfers[0]["volume"] == 20
    assert cell_transfers[0]["new_tip"] == "always"


def test_compile_too_many_conditions_errors():
    from tools.compiler import compile_protocol
    conditions = [{"base_media_vol": 110} for _ in range(5)]
    result = compile_protocol(json.dumps(conditions), ["B2", "B3"])
    assert "error" in result


def test_compile_multiple_conditions():
    from tools.compiler import compile_protocol
    conditions = [
        {"base_media": "High Buffer Defined Media", "base_media_vol": 110,
         "yeast_extract": 14, "tryptone": 26, "na_l_glut": 10},
        {"base_media": "Semi-Defined Media", "base_media_vol": 125,
         "yeast_extract": 20, "tryptone": 14, "mops": 7},
    ]
    result = compile_protocol(json.dumps(conditions), ["B2", "B3"])
    assert result["n_transfers"] > 0
    assert len(result["well_summaries"]) == 2
    assert len(result["errors"]) == 0
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_compiler.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `scripts/tools/compiler.py`:

```python
"""Compile conditions (final concentrations) into Monomer transfer_array JSON."""
from __future__ import annotations

import json
from typing import Any

TOTAL_VOL_UL = 200
CELL_VOL_UL = 20
REAGENT_VOL_UL = TOTAL_VOL_UL - CELL_VOL_UL
MIN_PIPETTE_UL = 5
MAX_TRANSFERS = 40

STOCKS = {
    "yeast_extract": {"src_well": "A1"},
    "tryptone":      {"src_well": "A2"},
    "mops":          {"src_well": "A3"},
    "na_l_glut":     {"src_well": "A4"},
    "kh2po4":        {"src_well": "B1"},
    "glucose":       {"src_well": "B2"},
    "nacl":          {"src_well": "B3"},
    "mgso4":         {"src_well": "B4"},
    "water":         {"src_well": "C1"},
}

BASE_MEDIA_WELLS = {
    "Semi-Defined Media":         "D1",
    "High Buffer Defined Media":  "D2",
    "Prepared LBv2 Media":        "D3",
    "Novel Bio NBxCyclone Media": "D4",
}

CELL_SOURCE_WELL = "A1"


def compile_protocol(conditions_json: str, wells: list[str]) -> dict:
    conditions = json.loads(conditions_json) if isinstance(conditions_json, str) else conditions_json

    if len(conditions) > len(wells):
        return {"error": f"More conditions ({len(conditions)}) than wells ({len(wells)})"}

    all_transfers: list[dict[str, Any]] = []
    well_summaries: list[dict] = []

    for i, cond in enumerate(conditions):
        dst_well = wells[i]
        base_media = cond.get("base_media", "High Buffer Defined Media")
        base_vol = float(cond.get("base_media_vol", 110))

        transfers_for_well: list[dict[str, Any]] = []
        reagent_vol_total = base_vol

        # Base media
        transfers_for_well.append({
            "src_plate": "reagent",
            "src_well": BASE_MEDIA_WELLS.get(base_media, "D1"),
            "dst_plate": "experiment", "dst_well": dst_well,
            "volume": round(base_vol, 1), "new_tip": "once", "blow_out": True,
        })

        # Reagent spikes (values assumed in µL)
        for reagent_name, stock_info in STOCKS.items():
            if reagent_name == "water":
                continue
            val = cond.get(reagent_name, 0)
            if val is None or float(val) <= 0:
                continue
            vol = float(val)
            if vol < MIN_PIPETTE_UL:
                continue
            transfers_for_well.append({
                "src_plate": "reagent",
                "src_well": stock_info["src_well"],
                "dst_plate": "experiment", "dst_well": dst_well,
                "volume": round(vol, 1), "new_tip": "once", "blow_out": True,
            })
            reagent_vol_total += vol

        # Water fill
        water_vol = REAGENT_VOL_UL - reagent_vol_total
        if water_vol >= MIN_PIPETTE_UL:
            transfers_for_well.append({
                "src_plate": "reagent",
                "src_well": STOCKS["water"]["src_well"],
                "dst_plate": "experiment", "dst_well": dst_well,
                "volume": round(water_vol, 1), "new_tip": "once", "blow_out": True,
            })
        elif water_vol < 0:
            water_vol = 0

        # Cell seeding
        transfers_for_well.append({
            "src_plate": "cell_culture_stock",
            "src_well": CELL_SOURCE_WELL,
            "dst_plate": "experiment", "dst_well": dst_well,
            "volume": CELL_VOL_UL, "new_tip": "always", "blow_out": False,
            "post_mix_volume": 40, "post_mix_reps": 5,
        })

        all_transfers.extend(transfers_for_well)
        well_summaries.append({
            "well": dst_well, "base_media": base_media,
            "reagent_vol": round(reagent_vol_total, 1),
            "water_vol": round(max(0, water_vol), 1),
            "total": round(reagent_vol_total + max(0, water_vol) + CELL_VOL_UL, 1),
        })

    errors = []
    if len(all_transfers) > MAX_TRANSFERS:
        errors.append(f"Too many transfers: {len(all_transfers)} > {MAX_TRANSFERS}")
    for ws in well_summaries:
        if abs(ws["total"] - TOTAL_VOL_UL) > 1.0:
            errors.append(f"Well {ws['well']}: total={ws['total']} (expected {TOTAL_VOL_UL})")

    return {
        "transfer_array": all_transfers,
        "n_transfers": len(all_transfers),
        "well_summaries": well_summaries,
        "errors": errors,
    }
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_compiler.py -v
```

Expected: 5 passed

**Step 5: Commit**

```bash
git add scripts/tools/compiler.py tests/test_compiler.py
git commit -m "feat: protocol compiler — conditions to transfer_array with TDD"
```

---

### Task 8: Orchestrator Main Loop

**Files:**
- Create: `scripts/orchestrator.py`
- Create: `tests/test_orchestrator.py`

**Depends on:** Tasks 1-7

**Step 1: Write the failing test**

Create `tests/test_orchestrator.py`:

```python
"""Tests for orchestrator — tool dispatch and structure."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_get_tools_returns_valid_schema():
    from orchestrator import get_tools
    tools = get_tools()
    assert len(tools) >= 7
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool


def test_execute_tool_analyze():
    from orchestrator import execute_tool
    result_json = execute_tool("analyze_results", {
        "current_round_csv": "data/PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ_growth.csv"
    })
    result = json.loads(result_json)
    assert "best_growth_rate" in result
    assert result["best_growth_rate"] > 1.5


def test_execute_tool_convergence():
    from orchestrator import execute_tool
    result_json = execute_tool("check_convergence", {
        "current_best_rate": 1.62,
        "current_best_se": 0.05,
        "previous_best_rate": 1.60,
        "previous_best_se": 0.05,
    })
    result = json.loads(result_json)
    assert "converged" in result


def test_execute_unknown_tool():
    from orchestrator import execute_tool
    result_json = execute_tool("nonexistent_tool", {})
    result = json.loads(result_json)
    assert "error" in result
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_orchestrator.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write the orchestrator**

Create `scripts/orchestrator.py` — full code from the design doc (Task 1 in the original plan). The complete file is in `docs/plans/2026-03-15-closed-loop-orchestrator-implementation.md` Task 1 Step 3. Copy that code exactly.

**Step 4: Run test to verify it passes**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_orchestrator.py -v
```

Expected: 4 passed

**Step 5: Commit**

```bash
git add scripts/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: orchestrator main loop with Anthropic tool_use"
```

---

### Task 9: Integration Test — Full Simulated Loop

**Files:**
- Create: `tests/test_integration_loop.py`

**Depends on:** Tasks 1-8

**Step 1: Write integration test**

Create `tests/test_integration_loop.py`:

```python
"""Integration test: full simulated closed loop without Anthropic API.

Tests the tool chain: fetch → analyze → baybe → compile → submit → wait → fetch.
Does NOT test LLM orchestration (that requires API key).
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
os.environ["SIMULATION_MODE"] = "1"

PLATE_ID = "PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ"


def test_full_tool_chain():
    """Run the complete tool chain without the LLM orchestrator."""
    from tools.monomer_client import fetch_results, monomer_submit, wait_for_workflow
    from tools.analyzer import analyze_results
    from tools.baybe_tools import baybe_propose
    from tools.compiler import compile_protocol
    from tools.validators import check_convergence

    # Step 1: Fetch Round 1 results
    r1 = fetch_results(PLATE_ID)
    assert r1["n_wells"] == 10
    best_r1 = r1["results"][0]["growth_rate"]
    assert best_r1 > 1.5

    # Step 2: Analyze
    analysis = analyze_results(f"data/{PLATE_ID}_growth.csv")
    assert analysis["best_growth_rate"] > 1.5

    # Step 3: BayBE proposes Round 2
    proposals = baybe_propose(n_proposals=5, round_number=2)
    assert len(proposals["proposed_conditions"]) == 5

    # Step 4: Compile to transfer_array
    wells = ["B2", "B3", "B4", "B5", "B6"]
    protocol = compile_protocol(
        json.dumps(proposals["proposed_conditions"]),
        wells,
    )
    assert len(protocol["errors"]) == 0
    assert protocol["n_transfers"] > 0

    # Step 5: Submit to simulator
    submit = monomer_submit(
        transfer_array_json=json.dumps(protocol["transfer_array"]),
        monitoring_wells=wells,
        plate_barcode="SIM_R2_PLATE",
        round_label="round_2",
    )
    wf_id = submit.get("workflow_id")
    assert wf_id

    # Step 6: Wait for completion
    status = wait_for_workflow(wf_id, timeout=15)
    assert status["status"] == "completed"

    # Step 7: Fetch simulated results
    r2 = fetch_results("SIM_R2_PLATE")
    assert r2["n_wells"] > 0
    best_r2 = r2["results"][0]["growth_rate"]
    assert best_r2 > 0

    # Step 8: Check convergence
    conv = check_convergence(
        current_best_rate=best_r2, current_best_se=0.1,
        previous_best_rate=best_r1, previous_best_se=0.1,
    )
    assert "converged" in conv
    print(f"\nRound 1 best: {best_r1}/hr → Round 2 best: {best_r2}/hr")
    print(f"Converged: {conv['converged']} ({conv['recommendation']})")
```

**Step 2: Run integration test**

```bash
cd /Users/viachealavrudenko/Cell.ai && SIMULATION_MODE=1 python -m pytest tests/test_integration_loop.py -v -s
```

Expected: 1 passed with output showing Round 1 → Round 2 rates and convergence status.

**Step 3: Commit**

```bash
git add tests/test_integration_loop.py
git commit -m "test: integration test — full simulated closed loop tool chain"
```

---

### Task 10 (V1.5): Random Screen Tool

**Files:**
- Create: `scripts/tools/random_screen.py`
- Create: `tests/test_random_screen.py`

**Step 1: Write the failing test**

Create `tests/test_random_screen.py`:

```python
"""Tests for random screening tool."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_lhs_returns_correct_count():
    from tools.random_screen import latin_hypercube_screen
    result = latin_hypercube_screen(n_conditions=10)
    assert result["n_conditions"] == 10
    assert result["method"] == "latin_hypercube"


def test_lhs_conditions_have_valid_volumes():
    from tools.random_screen import latin_hypercube_screen
    result = latin_hypercube_screen(n_conditions=5)
    for cond in result["conditions"]:
        assert cond["total"] == 200
        assert cond["cells"] == 20
        assert cond["water"] >= 0


def test_lhs_respects_fixed_base_media():
    from tools.random_screen import latin_hypercube_screen
    result = latin_hypercube_screen(n_conditions=5, base_media="Semi-Defined Media")
    for cond in result["conditions"]:
        assert cond["base_media"] == "Semi-Defined Media"
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_random_screen.py -v
```

**Step 3: Write minimal implementation**

Create `scripts/tools/random_screen.py`:

```python
"""Random screening — LHS sampling for initial exploration."""
from __future__ import annotations

import numpy as np
from scipy.stats import qmc

RANDOM_SEED = 42
TOTAL_VOL_UL = 200
CELL_VOL_UL = 20
REAGENT_VOL_UL = TOTAL_VOL_UL - CELL_VOL_UL

DEFAULT_RANGES = {
    "base_media_vol": (100, 160),
    "yeast_extract": (0, 30),
    "tryptone": (0, 30),
    "mops": (0, 20),
    "na_l_glut": (0, 15),
    "kh2po4": (0, 10),
    "glucose": (0, 20),
}

BASE_MEDIA_OPTIONS = ["Semi-Defined Media", "High Buffer Defined Media"]


def latin_hypercube_screen(
    n_conditions: int = 10,
    factor_ranges: dict | None = None,
    base_media: str | None = None,
) -> dict:
    ranges = factor_ranges or DEFAULT_RANGES
    factors = list(ranges.keys())
    n_dim = len(factors)

    sampler = qmc.LatinHypercube(d=n_dim, seed=RANDOM_SEED)
    raw = sampler.random(n=n_conditions * 3)

    bounds_low = np.array([ranges[f][0] for f in factors])
    bounds_high = np.array([ranges[f][1] for f in factors])
    scaled = qmc.scale(raw, bounds_low, bounds_high)

    rng = np.random.default_rng(RANDOM_SEED)
    conditions = []

    for row in scaled:
        c = {f: round(float(v), 1) for f, v in zip(factors, row)}
        vol_sum = sum(c.values())
        if vol_sum > REAGENT_VOL_UL:
            continue
        c["base_media"] = base_media or rng.choice(BASE_MEDIA_OPTIONS)
        c["water"] = round(REAGENT_VOL_UL - vol_sum, 1)
        c["cells"] = CELL_VOL_UL
        c["total"] = TOTAL_VOL_UL
        conditions.append(c)
        if len(conditions) >= n_conditions:
            break

    return {"n_conditions": len(conditions), "method": "latin_hypercube", "conditions": conditions}
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -m pytest tests/test_random_screen.py -v
```

Expected: 3 passed

**Step 5: Commit**

```bash
git add scripts/tools/random_screen.py tests/test_random_screen.py
git commit -m "feat: random screen tool — LHS sampling for initial exploration"
```
