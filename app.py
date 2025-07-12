# Quartz Slab Optimizer - Mixed Slab Bin-Packing Optimization

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple, Dict
from itertools import product, islice

# --- Page Setup ---
st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("Quartz Slab Optimizer")
st.markdown("Enter required dimensions in **meters**, one per line (e.g. `0.65 2.53`) and click Run")

# --- Slab Configuration ---
SLAB_FIXED_LENGTH = 320  # cm
SLAB_OPTIONS_ALL = [60, 70, 80, 90, 100, 160]
available_slab_sizes = st.multiselect(
    "Select available slab sizes (cm)",
    options=SLAB_OPTIONS_ALL,
    default=SLAB_OPTIONS_ALL,
    format_func=lambda x: f"{x} cm height"
)
QUARTZ_SLAB_SIZES = sorted(available_slab_sizes)

# --- Input Parser ---
def parse_input(text: str) -> List[Tuple[float, float]]:
    pieces = []
    for line in text.strip().split("\n"):
        try:
            a, b = map(float, line.strip().split())
            pieces.append((min(a, b) * 100, max(a, b) * 100))  # convert to cm (height, width)
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

# --- Best Fit Bin-Packing ---
def best_fit_pack(pieces: List[Tuple[float, float]], slab_w: float, slab_h: float):
    bins = []
    sorted_pieces = sorted(pieces, key=lambda x: x[0] * x[1], reverse=True)

    for ph, pw in sorted_pieces:
        orientations = [(ph, pw), (pw, ph)]
        placed = False

        for h, w in orientations:
            for slab in bins:
                x, y = slab["x_cursor"], slab["y_cursor"]
                row_h = slab["row_height"]

                if x + w <= slab_w and y + h <= slab_h:
                    slab["rects"].append((x, y, w, h))
                    slab["x_cursor"] += w
                    slab["row_height"] = max(row_h, h)
                    placed = True
                    break

                elif y + row_h + h <= slab_h and w <= slab_w:
                    slab["x_cursor"] = w
                    slab["y_cursor"] += row_h
                    slab["row_height"] = h
                    slab["rects"].append((0, slab["y_cursor"], w, h))
                    placed = True
                    break
            if placed:
                break

        if not placed:
            for h, w in orientations:
                if w <= slab_w and h <= slab_h:
                    bins.append({
                        "x_cursor": w,
                        "y_cursor": 0,
                        "row_height": h,
                        "rects": [(0, 0, w, h)]
                    })
                    break

    return [slab["rects"] for slab in bins]

# --- Optimizer ---
def find_best_mixed_slabs(pieces: List[Tuple[float, float]]):
    best_result = None
    min_slabs, min_waste = float('inf'), float('inf')

    valid_heights = [h for h in QUARTZ_SLAB_SIZES if all(p[0] <= h for p in pieces)]
    all_assignments = islice(product(valid_heights, repeat=len(pieces)), 50000)

    for combo in all_assignments:
        assigned: Dict[int, List[Tuple[float, float]]] = {}
        for i, slab_h in enumerate(combo):
            assigned.setdefault(slab_h, []).append(pieces[i])

        layout, waste, slab_count, records = [], 0, 0, []

        for h, group in assigned.items():
            if not group:
                continue
            packed = best_fit_pack(group, SLAB_FIXED_LENGTH, h)
            used = sum(w * h for slab in packed for _, _, w, h in slab)
            total = len(packed) * SLAB_FIXED_LENGTH * h
            layout.extend([(slab, SLAB_FIXED_LENGTH, h) for slab in packed])
            records.extend([(SLAB_FIXED_LENGTH, h)] * len(packed))
            waste += total - used
            slab_count += len(packed)

        if slab_count < min_slabs or (
            slab_count == min_slabs and (
                waste < min_waste or (
                    waste == min_waste and (
                        sorted(records) < sorted(best_result["slab_records"]) or (
                            sorted(records) == sorted(best_result["slab_records"]) and
                            sum(h for _, h in records) / len(records) < sum(h for _, h in best_result["slab_records"]) / len(best_result["slab_records"])
                        )
                    )
                )
            )
        ):
            best_result = {
                "layout": layout,
                "waste": waste,
                "slab_count": slab_count,
                "slab_records": records
            }
            min_slabs, min_waste = slab_count, waste

    return best_result if best_result else {"layout": [], "waste": 0, "slab_count": 0, "slab_records": []}

# --- Run Button ---
if st.button("Run Slabbing"):
    pieces = parse_input(input_text)
    result = find_best_mixed_slabs(pieces)

    st.subheader(f"Recommended Layout: {result['slab_count']} slab(s)")
    st.write(f"Estimated Waste Area: {result['waste'] / 10000:.2f} m²")

    # --- Visualization ---
    cols = st.columns(min(len(result['layout']), 3))
    for idx, (slab, w, h) in enumerate(result['layout']):
        with cols[idx % len(cols)]:
            fig, ax = plt.subplots(figsize=(6, h / 60))
            ax.set_xlim(0, w)
            ax.set_ylim(0, h)
            for x, y, pw, ph in slab:
                rect = patches.Rectangle((x, y), pw, ph, linewidth=1, edgecolor='black', facecolor='skyblue')
                ax.add_patch(rect)
                ax.text(x + pw / 2, y + ph / 2, f"{int(ph)}x{int(pw)}", ha='center', va='center', fontsize=8)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f"{int(h)} x {int(w)} cm")
            st.pyplot(fig)












