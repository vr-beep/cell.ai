# Elnora Q3: Experimental Strategy for Media Optimization

**Task ID:** `3507ec1a-0ad7-4150-85ab-7b352b7cd444`
**Date:** 2026-03-14
**Project:** Cell.ai - V.natriegens Media Optimization

## Question

Is a DOE appropriate or a different strategy given the limitations of the experimental setup? What experimental design strategy do you recommend and why?

## Elnora Response

I highly recommend **Strategy G (Hybrid: space-filling design for round 1, then BayBE for rounds 2-3)**.

Given your severe budget constraint (max 30 experiments) and the vast search space (343 combinations), traditional DOE will fall short, and pure random sampling wastes resources. Bayesian Optimization (BO) is perfectly suited for this, but BO models require an initial dataset to build their first internal map (surrogate model) of the landscape.

Here is exactly how I recommend structuring your 24-hour campaign to maximize your chances of finding the optimal media.

### 1. Strategy: Round 1 vs. Subsequent Rounds
**Yes, Round 1 must use a different strategy.**
*   **Round 1 (Initialization):** Use **Latin Hypercube Sampling (LHS)** or a **D-optimal design** to select 10 highly diverse, space-filling conditions. If you start BayBE with zero data, it essentially guesses randomly. A space-filling design ensures your initial Gaussian Process (GP) model understands the boundaries and general topography of your 3-parameter space.
*   **Rounds 2 & 3 (Optimization):** Hand complete control over to **BayBE**. Feed the Round 1 results into the model, and let it propose the next batch of 10. It will naturally balance exploring uncertain regions and exploiting high-performing regions.

### 2. Optimal Batch Size Per Round
**10 conditions per round.**
Since your plate layout allows 10 conditions (+1 LBv2 control) with 4 wells each (3 reps + 1 blank), running exactly 10 conditions per round is the most efficient use of your hardware. BayBE natively supports "batch optimization" (proposing multiple points at once) using batch acquisition functions.

### 3. Allocation Across Rounds
With a 30-experiment budget, use a **10-10-10 split**:
*   **Round 1 (10 exp):** Pure exploration (LHS). Maps the global landscape.
*   **Round 2 (10 exp):** BayBE (Balanced). The model will likely test a mix of predicted peaks and highly uncertain areas.
*   **Round 3 (10 exp):** BayBE (Exploitation-heavy). You can tune the acquisition function here to focus purely on maximizing growth rate based on the best predictions from Rounds 1 and 2.

### 4. Is DOE appropriate at all?
**Classical DOE (like Full/Fractional Factorial or Box-Behnken) is not appropriate here.**
You only have the budget to sample ~8.7% of your 343-point space. Classical DOE is too rigid and assumes you can execute the entire matrix before analyzing. However, *algorithmic DOE* (like D-optimal) is highly appropriate for selecting your Round 1 space-filling points. After Round 1, abandon DOE and rely entirely on sequential Bayesian Optimization.

### 5. Maximizing Information Per Experiment
To get the most out of your 30 experiments, focus on **data quality and feature extraction**:
*   **Don't just use endpoint OD.** *V. natriegens* has a variable lag phase (15-90 mins) when switching media. Endpoint OD will conflate lag time with growth rate.
*   **Extract $\mu_{max}$:** Use your kinetic reads (every 10 mins) to calculate the maximum specific growth rate ($\mu_{max}$) by finding the maximum slope of the $\ln(OD)$ vs. time curve during the exponential phase. Feed $\mu_{max}$ to BayBE as your target metric, not raw OD.
*   **Blank correction is critical:** Ensure your media-only blanks are subtracted at every timepoint before calculating $\mu_{max}$.

### 6. Replicates Across Rounds?
**No, do not waste your 10 condition slots on cross-round replicates.**
You already have a built-in cross-round calibrator: your **LBv2 positive control**.
Because you are running LBv2 on every single plate, you can use it to normalize batch effects (e.g., slight temperature differences in the Tecan between rounds).
*   *Pro-tip:* Instead of feeding raw $\mu_{max}$ to BayBE, feed it the **relative growth rate** ($\mu_{max, condition} / \mu_{max, LBv2}$). This perfectly controls for run-to-run variance without wasting experimental slots.

### 7. BayBE Configuration Recommendations
To make this work in BayBE, configure it as follows:
*   **Search Space Encoding:** Even though you have 7 discrete levels for your parameters, ensure BayBE treats them as **continuous/numerical** variables (e.g., actual concentrations like 5mM, 10mM), not categorical. This allows the model to interpolate between your levels.
*   **Surrogate Model:** Use a **Gaussian Process (GP)**. It is the gold standard for low-data regimes (<50 points) and provides excellent uncertainty quantification.
*   **Acquisition Function:** Use **q-Expected Improvement (qEI)** or **q-Upper Confidence Bound (qUCB)**. The "q" is critical—it tells BayBE to generate a *batch* of 10 points that are jointly optimal, preventing the model from suggesting 10 nearly identical points in a single round.
*   **Round 3 Tweak:** For the final round, if you are using qUCB, you can lower the beta parameter (the exploration weight) to force the model to exploit the best known regions.

**One final hackathon logistics note:** Because *V. natriegens* grows so fast, your bottleneck won't be incubation—it will be data processing. Write a Python script *before* the clock starts that automatically parses the Tecan output, subtracts blanks, calculates $\mu_{max}$, normalizes to LBv2, and formats the CSV for BayBE. If you automate the data handoff, you will easily hit your 3-round target.

Let me know if you need help writing the $\mu_{max}$ extraction script or the BayBE initialization code!
