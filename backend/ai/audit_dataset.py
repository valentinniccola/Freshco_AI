import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import cv2
import numpy as np
from ai.preprocessor import ImagePreprocessor

# Define Food-Specific Class Boundary Criteria
BOUNDARY_RULES = {
    "Cut Fruit (Apple, Avocado, Pear)": {
        "Fresh": "No oxidation or light cut surface oxidation (< 4% surface, light amber browning < 2.0)",
        "Nearly Spoiled": "Moderate enzymatic browning (4% - 20% area, browning 2.0 - 4.5, no liquefaction/mold)",
        "Spoiled": "Deep black necrosis (> 20%), mold fuzzy colonies, slimy liquefaction, browning > 5.0"
    },
    "Whole Fruit (Banana, Orange, Citrus)": {
        "Fresh": "Clean rind, sugar spots < 5%, browning < 1.5",
        "Nearly Spoiled": "Dense sugar spots (5% - 25%), skin yellow-brown, flesh intact, browning 1.8 - 4.2",
        "Spoiled": "White/green/black fungal mold colonies, rind puncture rot, collapse (> 25% decay)"
    },
    "Vegetables (Tomato, Bell Pepper, Cucumber)": {
        "Fresh": "Taut skin, 0% spots, browning < 1.0",
        "Nearly Spoiled": "Wrinkling skin, minor soft spots (3% - 15%), stem browning, no mold spores",
        "Spoiled": "Wet soft rot, white/grey mold mycelium, fungal lesions (> 15% coverage)"
    },
    "Leafy Greens (Spinach, Lettuce, Kale)": {
        "Fresh": "Crisp green leaves, no wilting, discoloration < 8.0",
        "Nearly Spoiled": "Edge yellowing/wilting (5% - 25% area), slight limpness, fully edible when cooked",
        "Spoiled": "Dark black slime, liquefied leaf decay, foul odor equivalent visual rot (> 25%)"
    },
    "Bakery & Bread": {
        "Fresh": "Golden crust, soft crumb, 0% mold colonies",
        "Nearly Spoiled": "Dry/stale crumb, firm texture, 0% mold colonies (ideal for croutons/French toast)",
        "Spoiled": "Any visible green/blue/black/white mold spore clusters (> 0.5% colony presence)"
    },
    "Meat & Poultry": {
        "Fresh": "Bright red/pink, white fat marbling, 0% green/grey discoloration",
        "Nearly Spoiled": "Surface dulling, light myoglobin oxidation (browning 1.5 - 3.5, consume today)",
        "Spoiled": "Iridescent grey/green slime, deep putrid discoloration (LAB a* collapse < 120)"
    }
}

def audit_dataset_and_samples():
    print("=================================================================")
    print("  FRESHCO AI: DATASET AUDIT & CLASS BOUNDARY VERIFICATION        ")
    print("=================================================================\n")

    # Edge cases for audit (e.g. Cut Apple with small brown spot, spotted banana, aged meat, stale bread)
    edge_cases = [
        ("Cut Apple (Small Brown Cut Spot)", "Fresh", 1.8, 1.4, 9.2, 85.0, "Surface cut oxidation (edible)"),
        ("Cut Apple (Moderate Flesh Browning)", "Nearly Spoiled", 8.5, 3.2, 14.5, 68.0, "Air-exposed cut fruit (cook/prep today)"),
        ("Cut Apple (Black Rot & Mold)", "Spoiled", 28.0, 7.8, 26.0, 35.0, "Fungal mold & mushy necrotic decay"),
        ("Banana (3-4 Small Sugar Spots)", "Fresh", 3.2, 1.2, 10.5, 82.0, "Sweet peak ripeness sugar spots"),
        ("Banana (Heavy Sugar Spots 18%)", "Nearly Spoiled", 18.0, 3.8, 15.2, 58.0, "Ideal for banana bread / smoothies"),
        ("Banana (Black Skin Split & Mold)", "Spoiled", 38.0, 8.5, 32.0, 22.0, "Rotted skin with fungal growth"),
        ("Stale Sourdough Bread (0% Mold)", "Nearly Spoiled", 0.0, 1.2, 8.0, 42.0, "Stale crumb without mold (croutons)"),
        ("Bread (Small Green Mold Dot 1.5%)", "Spoiled", 2.2, 2.5, 18.0, 52.0, "Mycotoxin risk: zero mold tolerance"),
        ("Beef Steak (Natural White Marbling)", "Fresh", 0.0, 0.0, 9.4, 44.0, "Natural fat striations (not decay)"),
        ("Beef Steak (Grey Edge Oxidation)", "Nearly Spoiled", 5.2, 2.8, 16.0, 55.0, "Myoglobin air oxidation (cook today)"),
        ("Beef Steak (Greenish Putrid Slime)", "Spoiled", 24.0, 8.0, 35.0, 28.0, "Bacterial spoilage slime"),
    ]

    print("--- 1. AUDIT REPORT: EDGE CASES & SUSPECTED OVER-CLASSIFICATION ---")
    print(f"{'Sample / Case Name':<38} | {'Ground Truth':<14} | {'Spot %':<7} | {'Brown':<6} | {'Status':<12} | {'Risk / Analysis'}")
    print("-" * 115)

    flagged_count = 0
    for name, true_label, spot, browning, disc, homog, note in edge_cases:
        naive_spoilage = (spot * 3.5) + (browning * 7.0)

        is_naive_spoiled = (naive_spoilage > 28.0 or (spot > 7.0 and browning > 2.0)) and true_label != "Spoiled"
        status_flag = "[FLAGGED]" if is_naive_spoiled else "[OK]"
        if is_naive_spoiled:
            flagged_count += 1

        print(f"{name:<38} | {true_label:<14} | {spot:>5.1f}% | {browning:>5.1f} | {status_flag:<12} | {note}")

    print("-" * 115)
    print(f"Audit Summary: {flagged_count} of {len(edge_cases)} borderline/edible edge cases would be falsely labeled 'Spoiled' without calibrated boundaries.\n")

if __name__ == "__main__":
    audit_dataset_and_samples()
