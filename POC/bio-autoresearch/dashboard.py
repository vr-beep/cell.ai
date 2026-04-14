"""
Bio-autoresearch live dashboard.
Reads results.jsonl and auto-refreshes.

Usage: streamlit run POC/bio-autoresearch/dashboard.py
"""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

RESULTS_FILE = Path(__file__).parent / "results.jsonl"
REFRESH_INTERVAL = 5  # seconds
TARGET_RATE = 4.4  # published max for V. natriegens


def load_results() -> list[dict]:
    if not RESULTS_FILE.exists():
        return []
    rounds = []
    for line in RESULTS_FILE.read_text().strip().split("\n"):
        if line.strip():
            try:
                rounds.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rounds


st.set_page_config(page_title="Bio-Autoresearch", layout="wide", page_icon="🧬")

st.title("Bio-Autoresearch: Autonomous Media Optimization")
st.caption("AI agent + Elnora literature search + GP simulator trained on real wet-lab data")

results = load_results()

if not results:
    st.info("Waiting for first round... Run `python POC/bio-autoresearch/autoresearch.py`")
    time.sleep(REFRESH_INTERVAL)
    st.rerun()
else:
    # Metrics row
    best_round = max(results, key=lambda r: r["best_rate"])
    latest = results[-1]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Best Growth Rate", f"{best_round['best_rate']:.4f} h⁻¹",
                f"Round {best_round['round']}")
    col2.metric("Current Round", latest["round"])
    col3.metric("Total Recipes Tested",
                sum(r["n_recipes"] for r in results))
    col4.metric("Target", f"{TARGET_RATE} h⁻¹",
                f"{(best_round['best_rate']/TARGET_RATE*100):.0f}% achieved")

    # Two columns: chart + reasoning
    left, right = st.columns([2, 1])

    with left:
        # Panel 1: Growth Rate Over Rounds
        st.subheader("Growth Rate Over Rounds")
        chart_data = pd.DataFrame([
            {"Round": r["round"], "Best Rate (h⁻¹)": r["best_rate"]}
            for r in results
        ])

        # Running best
        chart_data["Overall Best"] = chart_data["Best Rate (h⁻¹)"].cummax()
        chart_data["Target"] = TARGET_RATE

        st.line_chart(
            chart_data.set_index("Round")[["Best Rate (h⁻¹)", "Overall Best", "Target"]],
            color=["#1f77b4", "#2ca02c", "#ff7f0e"],
        )

        # Panel 3: Search Space Exploration
        st.subheader("Search Space Exploration")
        all_recipes = []
        for r in results:
            for res in r.get("all_results", []):
                recipe = res["recipe"]
                all_recipes.append({
                    "NaCl (g/L)": recipe["nacl_g_l"],
                    "Glucose (g/L)": recipe["glucose_g_l"],
                    "YE (g/L)": recipe["yeast_extract_g_l"],
                    "Growth Rate": res["mean_growth_rate"],
                    "Round": r["round"],
                })
        if all_recipes:
            scatter_df = pd.DataFrame(all_recipes)
            st.scatter_chart(
                scatter_df,
                x="NaCl (g/L)",
                y="Glucose (g/L)",
                color="Growth Rate",
                size="Round",
            )

    with right:
        # Panel 2: Agent Reasoning
        st.subheader("Agent Reasoning")

        st.markdown(f"**Round {latest['round']} hypothesis:**")
        st.info(latest.get("hypothesis", "—"))

        if latest.get("elnora_question"):
            st.markdown("**Elnora query:**")
            st.warning(latest["elnora_question"])

        if latest.get("elnora_context"):
            with st.expander("Elnora response"):
                st.markdown(latest["elnora_context"][:1000])

        st.markdown(f"**Best recipe this round:**")
        bp = latest["best_recipe"]
        st.code(
            f"NaCl:    {bp['nacl_g_l']} g/L\n"
            f"Glucose: {bp['glucose_g_l']} g/L\n"
            f"YE:      {bp['yeast_extract_g_l']} g/L\n"
            f"Rate:    {latest['best_rate']:.4f} h⁻¹"
        )

    # Panel 4: Results Log
    st.subheader("Experiment Log")
    log_rows = []
    for r in results:
        log_rows.append({
            "Round": r["round"],
            "Best Rate": f"{r['best_rate']:.4f}",
            "Recipe": f"NaCl={r['best_recipe']['nacl_g_l']}, Glc={r['best_recipe']['glucose_g_l']}, YE={r['best_recipe']['yeast_extract_g_l']}",
            "Hypothesis": r.get("hypothesis", "—")[:100],
            "Duration": f"{r.get('duration_s', 0)}s",
        })
    st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)

    # Auto-refresh
    time.sleep(REFRESH_INTERVAL)
    st.rerun()
