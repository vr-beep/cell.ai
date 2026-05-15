---
notion_title: "Track A Experiment and Software Setup"
notion_id: "f7e329f4-baac-8260-9323-81d0e097663b"
exported: "2026-03-15"
---

# Track A Experiment and Software Setup

## Overview

In Track A, you will use Monomer's workcell to run autonomous experiments growing Vibrio Natriegens.

This guide will walk you through:
1. A Conceptual guide to Monomer's software stack (see our hackathon's [github repo](https://github.com/monomerbio/monomer-bio-hackathon-march14-15/) for the more in-depth software setup).
2. A Tutorial to get you familiar with executing an actual experiment and growing cells on our workcell.
3. An Experimental Guide to help you design an agentic experiment using AI tools.

## A Conceptual Guide to Monomer's Software for Track A

At the highest level, there are two components to Monomer's software stack being used in this Hackathon:

**Monomer Culture Monitor** — A Cloud data management platform for viewing experimental data in a plate-based format, built specifically for Cell Culture

**Monomer Automation Platform** — A lab automation scheduler which coordinates the execution of experimental operations on scientific instruments

During the course of this hackathon, you will connect to both of these applications.

- Using the **Monomer Automation Platform** you will define automated **Workflows** to run a series of **Routines** to **generate data** and **perform liquid handling operations.**
- Using the **Monomer Culture Monitor** you will **view the generated data** and **access well-level information** regarding the **reagent concentrations** and the **measured absorbance**.

### Running Experiments with the Automation Platform

You will run your experiments using pre-developed **Routines** which you will put into a **Workflow** which will be instantiated on the workcell via MCP.

**Routines:** A list of steps to perform on workcell instruments using a variety of resources, specifically **Culture Plates** and **Reagent Plates**.

We have developed two routines which will enable a large variety of experiments for the hackathon:

- **Measurement Routines**: Two separate routines depending on the plate type:
  - **`Measure Cell Culture Stock Absorbance`** — for the 24-well Cell Culture Stock Plate
  - **`Measure Experiment Plate Absorbance`** — for the 96-well Experiment Plate
  - Both take `culture_plate_barcode` and `wells_to_process` as inputs

- **Transfer Samples Routine (`Hackathon Transfer Samples`):** Takes more parameters, but the primary one is a `transfer_array`
  - Puts 3 plates on deck:

| Plate | Barcode Pattern | Labware | Notes |
|---|---|---|---|
| **Reagent Stock Plate** | `<TEAM_NAME>_REAGENTS` | 24-well v-bottom deep well | 8.5 mL max per well; pre-filled with known reagent stocks |
| **Experiment Plate** | `<TEAM_NAME>_EXPERIMENT` | 96-well flat bottom | Empty at the start of each run |
| **Cell Culture Stock Plate** | `<TEAM_NAME>_CELLS` | 24-well flat bottom | ~2 mL per well of cell culture |

  - Transfers volumes within and between plates
  - Example: "Fill A1 of the experiment plate with 180 uL of water (in B1 of reagent plate) and 20 uL of cells (in A1 of Cell stock plate)"

```python
transfer_array = [
    {
        "src_plate": "reagent",
        "src_well": "D1",
        "dst_plate": "experiment",
        "dst_well": "A1",
        "volume": 180,
        "new_tip": "once",
        "blow_out": True,
    },
    # Example: cell_culture_stock -> experiment (seed cells)
    {
        "src_plate": "cell_culture_stock",
        "src_well": "A1",
        "dst_plate": "experiment",
        "dst_well": "A1",
        "volume": 20,
        "post_mix_volume": 40,
        "post_mix_reps": 5,
        "new_tip": "always",
        "blow_out": False,  # So as not to produce bubbles in the well before measuring absorbance
    }
]
```

> **A Note to all practitioners of liquid handling dark arts:** We tried to balance control, flexibility, and a quality experience for this hackathon. We understand there are many more variables the opentrons API exposes (such as dispense height, speed of aspiration and dispense, tip touch, etc.) We wanted to focus more on the mixture of compounds and the unique needs of the bug vs. liquid handling nuances.

- Handles lidding and unlidding of the plates on deck

**Workflow:** A set of instructions in python to execute a series of **Routines** at specific times with specific parameters.
- Example: Measure Plate absorbance every 10 minutes for 2 hours, then passage 50 uLs of A1 into B1 filled with media would be a single workflow of 12 x Measure Absorbance routines and 1 x Hackathon Transfer Samples routines

## Part 1 - Workcell Tutorial: Basic Example of Executing 1 Open Loop Workflow

> Use [Cursor](https://cursor.com/home) (free first 7-days typically) or [Claude Code](https://code.claude.com/docs/en/quickstart) (requires a paid account) with the following prompt:
>
> `Guide me through this tutorial: https://github.com/monomerbio/monomer-bio-hackathon-march14-15 step-by-step.`

This will guide you through running a single shot workflow to determine what seeding density is best for measuring the change in growth.

1. **Setup:** We will ensure both teams are connected to Monomer's MCPs
2. **Design:** Design a **workflow** to test the impact of seeding density of growth curves in a standard Media using a provided example.
3. **Execute:** Monomer Staff will review the workflow, and then load it into the system. The workflow will execute on the system, generating data over the course of 1.5 hours
4. **Analyze:** You will use Monomer's MCP to perform analysis on the different growth curves over the course of the experiment.

## Part 2 - Autonomous Experimentation!

Here's where the real fun starts! Just like the **Tutorial** you will Design → Execute → Analyze, but now with the ability to do **loops**, and build Agents that will help you analyze and propose the next design.

As we did in the tutorial, you will run Measurement and Transfer Routines.

Design and test media compositions iteratively to determine the best media composition for Vibrio Natriegens.

1. **Experimental Design:** Determine how your experimental question and design on the workcell. You will have all of the reagent stocks below to work with **or you can build your own component stocks by mixing them together**.

2. **Submit your initial plate designs to Monomer — Reagent Stock Plate and Cell Stock Plate to Monomer:** We will help you generate both the 24 Deep Well plate which can hold 8.5 mLs in each well, and the Cell culture stock plate which should have 2 mL in each well.

| Plate | Barcode Pattern | Labware | Notes |
|---|---|---|---|
| **Reagent Stock Plate** | `<TEAM_NAME>_REAGENTS` | 24-well v-bottom deep well | 8.5 mL max per well; pre-filled with known reagent stocks |
| **Experiment Plate** | `<TEAM_NAME>_EXPERIMENT` | 96-well flat bottom | Empty at the start of each run |
| **Cell Culture Stock Plate** | `<TEAM_NAME>_CELLS` | 24-well flat bottom | ~2 mL per well of cell culture |

   > Monomer has the bandwidth to prepare up to 2 "Composed Media" i.e. LBv2 or Minimal Defined Media (these are solutions that take significant time to prepare), but we are happy to generate dilutions of existing stocks in the Reagent Database.
   > Monomer Staff will then generate and load this plate onto the workcell, which you will be able to see via MCP.

3. **Begin your Experimental Cycles of Design a workflow → Execute → Analyze → Design based off of new data**
   1. Just like in part 1, this will need to be approved the first time, and at some point Monomer Staff will turn on auto-approve of future workflows
   2. You will be able to add solutions to the stock plate in between experimental iterations, if you see precipitation

### Monomer and Elnora Wishlist

Here are some things we think are cool to build for:

- **Autonomous experimentation:** Build something that continuously loops and experiments. This can be:
  - **Closed-Loop:** using simple gradient descent or bayesian optimization to decide on the next media to try.
  - **Agentic:** incorporating a scientific agent with the ability to review literature, and explore new hypotheses branching off of the current ones.
- **A (vibe coded) dashboard:** showing progress of your experiments over time. Does your objective function minimize at each iteration?
- **A White Paper:** Describing your architecture and workflow.
