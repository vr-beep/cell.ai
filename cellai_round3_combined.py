from src.platform.core_domain.units import Time
from src.workflows.workflow_definition_dsl.workflow_definition_descriptor import (
    MoreThanConstraint,
    RoutineReference,
    WorkflowDefinitionDescriptor,
)


def build_definition(
    plate_barcode: str = "CellAI Experiment Plate 2",
    reagent_name: str = "CellAI Reagent Plate",
    cell_stock_plate_barcode: str = "CellAI Cell Culture Stock",
    num_absorbance_readings: int = 13,
) -> WorkflowDefinitionDescriptor:
    """CellAI Round 3: BayBE (F2-F6) + Elnora (F7-F11) + NB Control (D8).

    11 wells total. 180 uL media + 20 uL cells (from A1) = 200 uL.

    BayBE conditions (Row F):
      F2: HB-1 (YE 12.4, Tryp 7.7, NaGl 34mM)
      F3: HB-2 (YE 7.8, Tryp 6.3, NaGl 26mM)
      F4: HB-3 (YE 5.1, Tryp 6.5, NaGl 33mM)
      F5: SD-1 (YE 7.3, Tryp 13.4, MOPS 36mM)
      F6: SD-2 (YE 5.0, Tryp 15.0, MOPS 73mM)

    Elnora conditions (Row F):
      F7: HB-Opt1 (HB 110, NaGl 12, Tryp 30, YE 15, Water 13)
      F8: HB-Rich (HB 100, NaGl 10, Tryp 40, YE 30)
      F9: HB-CarbonMix (HB 110, Tryp 25, YE 25, Glu 10, Glycerol 10)
      F10: HB-Phos (HB 110, Tryp 30, YE 20, KH2PO4 5, Water 15)
      F11: SD-CarbonMix (SD 120, Tryp 20, YE 20, Glu 10, Glycerol 10)

    Control:
      D8: NB-CTL (Novel Bio 180)

    Reagent plate:
      A1=Semi-Defined, A2=High Buffer, A3=LBv2, A4=Novel Bio Cyclone
      A5=Def-Glycerol, A6=Glycerol 10%
      B1=YE (100mg/mL), B2=Tryptone (100mg/mL), B3=MOPS (1M), B4=Water
      B5=MgSO4 0.5M, B6=Trace 500X
      C1=Glucose (100mg/mL), C2=KH2PO4 (1M), C3=Na L-Glutamate (1M)
      C4=FeSO4 0.5M, C5=Na Citrate 0.5M
    """
    workflow = WorkflowDefinitionDescriptor(
        description=(
            "CellAI Round 3: BayBE (F2-F6) + Elnora (F7-F11) "
            "+ Novel Bio control (D8), OD600 every 10 min"
        )
    )

    transfer_array = []

    # === BASE MEDIA ===
    # High Buffer Defined (A2)
    for well, vol in [("F2", 110), ("F3", 110), ("F4", 110),
                       ("F7", 110), ("F8", 100), ("F9", 110), ("F10", 110)]:
        transfer_array.append({
            "src_plate": "reagent", "src_well": "A2",
            "dst_plate": "experiment", "dst_well": well,
            "volume": vol, "new_tip": "once",
        })

    # Semi-Defined (A1)
    for well, vol in [("F5", 131.4), ("F6", 125.4), ("F11", 120)]:
        transfer_array.append({
            "src_plate": "reagent", "src_well": "A1",
            "dst_plate": "experiment", "dst_well": well,
            "volume": vol, "new_tip": "once",
        })

    # Novel Bio Cyclone (A4) -> control D8
    transfer_array.append({
        "src_plate": "reagent", "src_well": "A4",
        "dst_plate": "experiment", "dst_well": "D8",
        "volume": 180, "new_tip": "once",
    })

    # === SUPPLEMENTS ===
    # Yeast Extract (B1, 100 mg/mL)
    for well, vol in [("F2", 24.7), ("F3", 15.5), ("F4", 10.2),
                       ("F5", 14.6), ("F6", 10.0),
                       ("F7", 15), ("F8", 30), ("F9", 25),
                       ("F10", 20), ("F11", 20)]:
        transfer_array.append({
            "src_plate": "reagent", "src_well": "B1",
            "dst_plate": "experiment", "dst_well": well,
            "volume": vol, "new_tip": "once",
        })

    # Tryptone (B2, 100 mg/mL)
    for well, vol in [("F2", 15.5), ("F3", 12.6), ("F4", 13.0),
                       ("F5", 26.8), ("F6", 30.0),
                       ("F7", 30), ("F8", 40), ("F9", 25),
                       ("F10", 30), ("F11", 20)]:
        transfer_array.append({
            "src_plate": "reagent", "src_well": "B2",
            "dst_plate": "experiment", "dst_well": well,
            "volume": vol, "new_tip": "once",
        })

    # Na L-Glutamate 1M (C3)
    for well, vol in [("F2", 6.8), ("F3", 5.3), ("F4", 6.5),
                       ("F7", 12), ("F8", 10)]:
        transfer_array.append({
            "src_plate": "reagent", "src_well": "C3",
            "dst_plate": "experiment", "dst_well": well,
            "volume": vol, "new_tip": "once",
        })

    # MOPS 1M (B3)
    for well, vol in [("F5", 7.2), ("F6", 14.6)]:
        transfer_array.append({
            "src_plate": "reagent", "src_well": "B3",
            "dst_plate": "experiment", "dst_well": well,
            "volume": vol, "new_tip": "once",
        })

    # Water (B4)
    for well, vol in [("F2", 23.0), ("F3", 36.6), ("F4", 40.3),
                       ("F7", 13), ("F10", 15)]:
        transfer_array.append({
            "src_plate": "reagent", "src_well": "B4",
            "dst_plate": "experiment", "dst_well": well,
            "volume": vol, "new_tip": "once",
        })

    # Glucose 100 mg/mL (C1)
    for well, vol in [("F9", 10), ("F11", 10)]:
        transfer_array.append({
            "src_plate": "reagent", "src_well": "C1",
            "dst_plate": "experiment", "dst_well": well,
            "volume": vol, "new_tip": "once",
        })

    # Glycerol 10% (A6)
    for well, vol in [("F9", 10), ("F11", 10)]:
        transfer_array.append({
            "src_plate": "reagent", "src_well": "A6",
            "dst_plate": "experiment", "dst_well": well,
            "volume": vol, "new_tip": "once",
        })

    # KH2PO4 1M (C2)
    transfer_array.append({
        "src_plate": "reagent", "src_well": "C2",
        "dst_plate": "experiment", "dst_well": "F10",
        "volume": 5, "new_tip": "once",
    })

    # === CELL STOCK (from A1) ===
    target_wells = ["F2", "F3", "F4", "F5", "F6", "F7", "F8",
                    "F9", "F10", "F11", "D8"]
    for well in target_wells:
        transfer_array.append({
            "src_plate": "cell_culture_stock", "src_well": "A1",
            "dst_plate": "experiment", "dst_well": well,
            "volume": 20,
            "pre_mix_volume": 200,
            "pre_mix_reps": 3,
            "post_mix_volume": 50,
            "post_mix_reps": 3,
            "new_tip": "once",
        })

    transfer = RoutineReference(
        routine_name="Hackathon Transfer Samples",
        routine_parameters={
            "reagent_name": reagent_name,
            "experiment_plate_barcode": plate_barcode,
            "cell_culture_stock_plate_barcode": cell_stock_plate_barcode,
            "transfer_array": transfer_array,
        },
    )
    workflow.add_routine("transfer", transfer)

    for i in range(num_absorbance_readings):
        absorbance = RoutineReference(
            routine_name="Measure Experiment Plate Absorbance",
            routine_parameters={
                "culture_plate_barcode": plate_barcode,
                "wells_to_process": target_wells,
            },
        )
        key = f"absorbance_{i}"
        workflow.add_routine(key, absorbance)

        if i == 0:
            workflow.add_time_constraint(
                MoreThanConstraint(
                    from_start="transfer",
                    to_start=key,
                    value=Time("1 minute"),
                )
            )
        else:
            workflow.add_time_constraint(
                MoreThanConstraint(
                    from_start=f"absorbance_{i - 1}",
                    to_start=key,
                    value=Time("10 minute"),
                )
            )

    return workflow
