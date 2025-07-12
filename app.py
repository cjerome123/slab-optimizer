# Quartz Slab Optimizer - Mixed Slab Bin-Packing Optimization

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple, Dict

# --- Available slab sizes toggle ---
slab_options_all = [60, 70, 80, 90, 100, 160]
available_slab_sizes = st.multiselect(
    "Select available slab sizes (cm)",
    options=slab_options_all,
    default=[60, 70, 80, 90, 100, 160],
    format_func=lambda x: f"{x} cm height"
)

QUARTZ_SLAB_SIZES = sorted(available_slab_sizes)  # in cm
SLAB_FIXED_LENGTH = 320  # in cm

st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("Quartz Slab Optimizer")
st.markdown("Enter required dimensions in **meters**, one per line (e.g. `0.65 2.53`) and click Run")

# --- Input ---
def parse_input(text: str) -> List[Tuple[float, float]]:
    pieces = []
    for line in text.strip().split("\n"):
        try:
            a, b = map(float, line.strip().split())
            pieces.append((min(a, b) * 100, max(a, b) * 100))  # height, width in cm
        except:
            continue
    return pieces

input_text = st.text_area("Dimensions:", value="""0.63 3.01
0.13 0.63
0.13 3.01
0.13 0.63
0.33 2.43

0.81 2.76
0.13 2.76
0.13 2.76
0.13 0.81
0.81 1.03
0.13 1.03
0.13 1.03""", height=200)

# --- Bin Packing with Best Fit ---
def best_fit_pack(pieces: List[Tuple[float, float]], slab_width: float, slab_height: float):
    bins = []
    sorted_pieces = sorted(pieces, key=lambda x: max(x[0], x[1]) * min(x[0], x[1]), reverse=True)

    for original_h, original_w in sorted_pieces:
        orientations = [(original_h, original_w), (original_w, original_h)]
        placed = False

        for h, w in orientations:
            for slab in bins:
                x = slab["x_cursor"]
                y = slab["y_cursor"]
                row_height = slab["row_height"]

                # Try placing in current row
                if x + w <= slab_width and y + h <= slab_height:
                    slab["rects"].append((x, y, w, h))
                    slab["x_cursor"] += w
                    slab["row_height"] = max(row_height, h)
                    placed = True
                    break
                # Try starting new row
                elif y + row_height + h <= slab_height and w <= slab_width:
                    slab["x_cursor"] = w
                    slab["y_cursor"] += row_height
                    slab["row_height"] = h
                    slab["rects"].append((0, slab["y_cursor"], w, h))
                    placed = True
                    break
            if placed:
                break

        if not placed:
            # Start new slab with best orientation that fits
            for h, w in orientations:
                if w <= slab_width and h <= slab_height:
                    bins.append({
                        "x_cursor": w,
                        "y_cursor": 0,
                        "row_height": h,
                        "rects": [(0, 0, w, h)]
                    })
                    placed = True
                    break

        if not placed:
            # Piece doesn't fit even in new slab (shouldn't happen with proper filtering)
            continue

    return [slab["rects"] for slab in bins]

# --- Mixed Slab Optimization ---
def find_best_mixed_slabs(pieces: List[Tuple[float, float]]):
    from itertools import product, combinations, islice

    best_result = None
    min_slabs = float('inf')
    min_waste = float('inf')

    valid_slab_heights = [h for h in QUARTZ_SLAB_SIZES if all(p[0] <= h for p in pieces)]
    all_assignments = islice(product(valid_slab_heights, repeat=len(pieces)), 50000)




