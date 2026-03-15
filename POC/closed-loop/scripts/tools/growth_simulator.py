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
        if self._history.empty:
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

        df = self._history
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
