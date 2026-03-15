"""
Cell.ai — Closed-Loop Media Optimization Dashboard

Streamlit dashboard for the Cell.ai hackathon demo.
Visualizes growth data, orchestrator activity, and BayBE proposals.
"""

from __future__ import annotations

import json
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
BO_DIR = Path(__file__).parent / "bo_outputs"
WORKFLOWS_DIR = Path(__file__).parent / "workflows"
STATE_FILE = DATA_DIR / "orchestrator_state.json"

# 96-well plate layout
ROWS = list("ABCDEFGH")
COLS = list(range(1, 13))

st.set_page_config(
    page_title="Cell.ai — Media Optimization",
    page_icon="🧫",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------
@st.cache_data(ttl=30)
def discover_plates() -> list[str]:
    """Find all plate IDs with growth data."""
    plates = []
    for f in sorted(DATA_DIR.glob("*_growth.csv")):
        plate_id = f.stem.replace("_growth", "")
        plates.append(plate_id)
    return plates


@st.cache_data(ttl=10)
def load_growth(plate_id: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{plate_id}_growth.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


@st.cache_data(ttl=10)
def load_plate_map(plate_id: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{plate_id}_plate_condition_map.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


@st.cache_data(ttl=10)
def load_replicates(plate_id: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{plate_id}_replicates.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


@st.cache_data(ttl=10)
def load_timeseries(plate_id: str) -> pd.DataFrame | None:
    path = DATA_DIR / f"{plate_id}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df["observation_timestamp"] = pd.to_datetime(df["observation_timestamp"])
    # Deduplicate: one row per (well, timestamp)
    df = df.drop_duplicates(subset=["well", "observation_timestamp"])
    df = df.sort_values(["well", "observation_timestamp"])
    # Compute hours since first observation
    t0 = df["observation_timestamp"].min()
    df["hours"] = (df["observation_timestamp"] - t0).dt.total_seconds() / 3600
    return df[["well", "observation_timestamp", "hours", "absorbance_OD600"]].copy()


@st.cache_data(ttl=10)
def load_bo_proposals() -> pd.DataFrame | None:
    path = BO_DIR / "next_round_plate_condition_map.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


def load_orchestrator_state() -> dict | None:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return None


# ---------------------------------------------------------------------------
# Plate heatmap
# ---------------------------------------------------------------------------
def plate_heatmap(growth_df: pd.DataFrame, metric: str = "growth_rate_per_hr") -> go.Figure:
    """Render a 96-well plate heatmap colored by metric."""
    # Build 8x12 grid
    grid = np.full((8, 12), np.nan)
    labels = [["" for _ in range(12)] for _ in range(8)]

    for _, row in growth_df.iterrows():
        well = str(row["well"])
        m = re.match(r"([A-H])(\d+)", well)
        if not m:
            continue
        r = ord(m.group(1)) - ord("A")
        c = int(m.group(2)) - 1
        val = row.get(metric, np.nan)
        grid[r][c] = val
        cond = str(row.get("condition_id", ""))
        labels[r][c] = f"{well}<br>{cond}<br>{val:.3f}" if pd.notna(val) else well

    colorscale = "YlGn" if "growth" in metric else "Blues"
    fig = go.Figure(data=go.Heatmap(
        z=grid,
        x=[str(c) for c in COLS],
        y=ROWS,
        text=labels,
        hoverinfo="text",
        colorscale=colorscale,
        colorbar=dict(title=metric.replace("_", " ").title()),
        zmin=0,
    ))
    fig.update_layout(
        title=f"96-Well Plate — {metric.replace('_', ' ').title()}",
        yaxis=dict(autorange="reversed"),
        height=350,
        margin=dict(l=40, r=40, t=50, b=30),
    )
    return fig


# ---------------------------------------------------------------------------
# Growth curves
# ---------------------------------------------------------------------------
def growth_curves(ts_df: pd.DataFrame, growth_df: pd.DataFrame | None = None) -> go.Figure:
    """Plot OD600 timeseries per well, colored by condition."""
    # Merge condition info if available
    if growth_df is not None:
        well_cond = growth_df[["well", "condition_id"]].drop_duplicates()
        ts_df = ts_df.merge(well_cond, on="well", how="left")
        color_col = "condition_id"
    else:
        ts_df = ts_df.copy()
        color_col = "well"

    fig = px.line(
        ts_df,
        x="hours",
        y="absorbance_OD600",
        color=color_col,
        line_group="well",
        labels={"hours": "Time (hours)", "absorbance_OD600": "OD600"},
        title="Growth Curves",
    )
    fig.update_layout(height=400, margin=dict(l=40, r=40, t=50, b=30))
    return fig


# ---------------------------------------------------------------------------
# Condition ranking bar chart
# ---------------------------------------------------------------------------
def ranking_chart(growth_df: pd.DataFrame) -> go.Figure:
    ranked = growth_df.sort_values("growth_rate_per_hr", ascending=True).copy()
    ranked["label"] = ranked["well"] + " — " + ranked["condition_id"].astype(str)

    fig = px.bar(
        ranked,
        x="growth_rate_per_hr",
        y="label",
        orientation="h",
        color="growth_rate_per_hr",
        color_continuous_scale="YlGn",
        labels={"growth_rate_per_hr": "Growth Rate (/hr)", "label": ""},
        title="Conditions Ranked by Growth Rate",
    )
    fig.update_layout(
        height=max(300, len(ranked) * 30),
        margin=dict(l=40, r=40, t=50, b=30),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Media composition radar/parallel
# ---------------------------------------------------------------------------
def composition_chart(plate_map: pd.DataFrame) -> go.Figure:
    """Parallel coordinates of media composition."""
    reagent_cols = [c for c in plate_map.columns
                    if c not in ("well", "condition", "base_media", "cells", "total", "water")]
    if not reagent_cols:
        return go.Figure()

    df = plate_map.copy()
    # Map base_media to numeric for coloring
    bases = df["base_media"].unique().tolist()
    df["base_idx"] = df["base_media"].map({b: i for i, b in enumerate(bases)})

    dims = [dict(label=c.replace("_", " ").title(), values=df[c]) for c in reagent_cols]
    fig = go.Figure(data=go.Parcoords(
        line=dict(color=df["base_idx"], colorscale="Viridis",
                  showscale=True, cmin=0, cmax=max(1, len(bases) - 1)),
        dimensions=dims,
    ))
    fig.update_layout(
        title="Media Composition (µL volumes)",
        height=400,
        margin=dict(l=80, r=80, t=50, b=30),
    )
    return fig


# ---------------------------------------------------------------------------
# Orchestrator log viewer
# ---------------------------------------------------------------------------
def render_orchestrator_log(state: dict):
    """Render orchestrator messages as a chat-like log."""
    messages = state.get("messages", [])
    ts = state.get("timestamp", "")

    st.caption(f"State saved: {ts} | Messages: {len(messages)}")

    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "user":
            if isinstance(content, str):
                with st.chat_message("user", avatar="🧑‍🔬"):
                    st.markdown(content[:2000])
            elif isinstance(content, list):
                # Tool results
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        with st.chat_message("user", avatar="🔧"):
                            try:
                                parsed = json.loads(item.get("content", "{}"))
                                st.json(parsed, expanded=False)
                            except (json.JSONDecodeError, TypeError):
                                st.code(str(item.get("content", ""))[:1000])
        elif role == "assistant":
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            with st.chat_message("assistant", avatar="🤖"):
                                st.markdown(block.get("text", "")[:3000])
                        elif block.get("type") == "tool_use":
                            with st.chat_message("assistant", avatar="⚙️"):
                                st.markdown(f"**Tool call:** `{block.get('name')}`")
                                st.json(block.get("input", {}), expanded=False)
            elif isinstance(content, str):
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(content[:2000])


# ---------------------------------------------------------------------------
# BayBE proposals viewer
# ---------------------------------------------------------------------------
def render_proposals(proposals_df: pd.DataFrame):
    """Show BayBE next-round proposals with predicted growth rates."""
    df = proposals_df.sort_values("predicted_growth_rate_per_hr", ascending=False).copy()

    fig = px.bar(
        df,
        x="condition",
        y="predicted_growth_rate_per_hr",
        color="base_media",
        title="BayBE Proposals — Predicted Growth Rate",
        labels={"predicted_growth_rate_per_hr": "Predicted Growth Rate (/hr)", "condition": ""},
    )
    fig.update_layout(height=350, margin=dict(l=40, r=40, t=50, b=30))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def sidebar():
    st.sidebar.image(
        "https://img.icons8.com/color/96/test-tube.png",
        width=60,
    )
    st.sidebar.title("Cell.ai")
    st.sidebar.caption("AI-Driven Media Optimization for V. natriegens")
    st.sidebar.divider()

    plates = discover_plates()
    if not plates:
        st.sidebar.warning("No plate data found in data/")
        return None

    plate_id = st.sidebar.selectbox(
        "Select Plate",
        plates,
        format_func=lambda x: f"{x[:12]}..." if len(x) > 12 else x,
    )

    st.sidebar.divider()
    st.sidebar.subheader("Quick Stats")

    growth = load_growth(plate_id)
    if growth is not None:
        best = growth.loc[growth["growth_rate_per_hr"].idxmax()]
        st.sidebar.metric("Best Growth Rate", f"{best['growth_rate_per_hr']:.3f} /hr")
        st.sidebar.metric("Best Condition", str(best["condition_id"]))
        st.sidebar.metric("Wells Measured", len(growth))
        st.sidebar.metric("Max OD600", f"{growth['max_absorbance_OD600'].max():.3f}")

    st.sidebar.divider()
    st.sidebar.subheader("Orchestrator")
    state = load_orchestrator_state()
    if state:
        n_msgs = len(state.get("messages", []))
        st.sidebar.metric("Messages", n_msgs)
        st.sidebar.caption(f"Last save: {state.get('timestamp', 'N/A')}")
    else:
        st.sidebar.caption("No orchestrator state")

    return plate_id


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------
def main():
    plate_id = sidebar()
    if plate_id is None:
        st.title("Cell.ai")
        st.info("No plate data found. Place CSV files in the `data/` directory.")
        return

    # Header
    st.title("🧫 Cell.ai — Media Optimization Dashboard")
    st.caption(f"Plate: `{plate_id}` | Organism: *V. natriegens* | Target: maximize growth rate")

    # Load all data
    growth = load_growth(plate_id)
    plate_map = load_plate_map(plate_id)
    ts_data = load_timeseries(plate_id)
    proposals = load_bo_proposals()

    # Tab layout
    tab_plate, tab_curves, tab_ranking, tab_composition, tab_proposals, tab_orchestrator = st.tabs([
        "🧪 Plate View",
        "📈 Growth Curves",
        "🏆 Rankings",
        "🧬 Media Composition",
        "🎯 BayBE Proposals",
        "🤖 Orchestrator Log",
    ])

    # --- Tab 1: Plate heatmap ---
    with tab_plate:
        if growth is not None:
            col1, col2 = st.columns(2)
            with col1:
                fig = plate_heatmap(growth, "growth_rate_per_hr")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = plate_heatmap(growth, "max_absorbance_OD600")
                st.plotly_chart(fig, use_container_width=True)

            with st.expander("Raw growth data"):
                st.dataframe(growth, use_container_width=True, hide_index=True)
        else:
            st.warning("No growth data available for this plate.")

    # --- Tab 2: Growth curves ---
    with tab_curves:
        if ts_data is not None:
            fig = growth_curves(ts_data, growth)
            st.plotly_chart(fig, use_container_width=True)

            st.caption(f"{ts_data['well'].nunique()} wells, {ts_data.groupby('well').size().iloc[0]} timepoints each")
        else:
            st.warning("No timeseries data. Run `monitor_data_processing.py` first.")

    # --- Tab 3: Rankings ---
    with tab_ranking:
        if growth is not None:
            fig = ranking_chart(growth)
            st.plotly_chart(fig, use_container_width=True)

            # Replicates table
            reps = load_replicates(plate_id)
            if reps is not None:
                st.subheader("Replicate Statistics")
                st.dataframe(reps, use_container_width=True, hide_index=True)
        else:
            st.warning("No growth data available.")

    # --- Tab 4: Media composition ---
    with tab_composition:
        if plate_map is not None:
            fig = composition_chart(plate_map)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Plate Condition Map")
            st.dataframe(plate_map, use_container_width=True, hide_index=True)
        else:
            st.warning("No plate condition map available.")

    # --- Tab 5: BayBE proposals ---
    with tab_proposals:
        if proposals is not None:
            render_proposals(proposals)
        else:
            st.info("No BayBE proposals yet. Run optimization first.")
            st.code("python scripts/orchestrator.py --plate-id <PLATE_ID>")

    # --- Tab 6: Orchestrator log ---
    with tab_orchestrator:
        state = load_orchestrator_state()
        if state:
            render_orchestrator_log(state)
        else:
            st.info("No orchestrator state. Start the loop to see activity here.")

        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col2:
            st.button("✅ Approve Next Step", use_container_width=True, disabled=True,
                       help="Approval is handled in the terminal when orchestrator is running")
        with col3:
            st.button("🛑 Stop Orchestrator", use_container_width=True, disabled=True,
                       help="Kill the orchestrator process manually (Ctrl+C)")


if __name__ == "__main__":
    main()
