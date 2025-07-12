# Quartz Slab Optimizer - Mixed Slab Bin-Packing Optimization

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple, Dict

QUARTZ_SLAB_SIZES = [60, 70, 80, 90, 100, 160]  # in cm
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
    for h, w in sorted(pieces, key=lambda x: x[0]*x[1], reverse=True):
        placed = False
        for slab in bins:
            x = slab["x_cursor"]
            y = slab["y_cursor"]
            row_height = slab["row_height"]
            rects = slab["rects"]

            if w > slab_width or h > slab_height:
                continue

            if x + w <= slab_width:
                rects.append((x, y, w, h))
                slab["x_cursor"] += w
                slab["row_height"] = max(row_height, h)
                placed = True
                break
            elif y + row_height + h <= slab_height:
                slab["x_cursor"] = w
                slab["y_cursor"] += row_height
                slab["row_height"] = h
                rects.append((0, slab["y_cursor"], w, h))
                placed = True
                break

        if not placed:
            bins.append({
                "x_cursor": w,
                "y_cursor": 0,
                "row_height": h,
                "rects": [(0, 0, w, h)]
            })
    return [slab["rects"] for slab in bins]

# --- Mixed Slab Optimization ---
def find_best_mixed_slabs(pieces: List[Tuple[float, float]]):
    grouped: Dict[int, List[Tuple[float, float]]] = {h: [] for h in QUARTZ_SLAB_SIZES}
    for h, w in pieces:
        for slab_h in sorted(QUARTZ_SLAB_SIZES):
            if h <= slab_h:
                grouped[slab_h].append((h, w))
                break

    result_layouts = []
    total_waste = 0
    total_slabs = 0
    slab_records = []

    for slab_h, group in grouped.items():
        if not group:
            continue
        layout = best_fit_pack(group, slab_width=SLAB_FIXED_LENGTH, slab_height=slab_h)
        used_area = sum(w * h for slab in layout for _, _, w, h in slab)
        total_area = len(layout) * SLAB_FIXED_LENGTH * slab_h
        waste = total_area - used_area

        total_slabs += len(layout)
        total_waste += waste

        for slab in layout:
            result_layouts.append((slab, SLAB_FIXED_LENGTH, slab_h))
            slab_records.append((SLAB_FIXED_LENGTH, slab_h))

    return {
        "layout": result_layouts,
        "waste": total_waste,
        "slab_count": total_slabs,
        "slab_records": slab_records
    }

# --- Run ---
if st.button("Run Slabbing"):
    pieces = parse_input(input_text)
    if not pieces:
        st.error("Invalid input.")
        st.stop()

    result = find_best_mixed_slabs(pieces)
    if not result or not result["layout"]:
        st.error("No slab size could accommodate your pieces.")
        st.stop()

    st.subheader("Results")
    st.write(f"Total Slabs: {result['slab_count']}")
    st.write(f"Waste: {result['waste']/10000:.2f} m²")

    # Count unique slab sizes used
    from collections import Counter
    slab_summary = Counter((min(w, h), max(w, h)) for w, h in result["slab_records"])
    st.write("Used Slab Sizes:")
    for (sh, sw), count in slab_summary.items():
        st.write(f"- {sh} x {sw} cm: {count} slab(s)")

    # --- Visualization ---
    def visualize_slab(slab_data, slab_w, slab_h):
        fig, ax = plt.subplots(figsize=(12, 3))
        ax.set_xlim(0, slab_w)
        ax.set_ylim(0, slab_h)
        ax.set_aspect('auto')
        ax.axis('off')
        for x, y, w, h in slab_data:
            rect = patches.Rectangle((x, y), w, h, edgecolor='black', facecolor='skyblue', lw=1)
            ax.add_patch(rect)
            ax.text(x + w / 2, y + h / 2, f"{int(w)}×{int(h)}", ha='center', va='center', fontsize=8)
        st.pyplot(fig)

    for slab, slab_w, slab_h in result['layout']:
        visualize_slab(slab, slab_w, slab_h)
















