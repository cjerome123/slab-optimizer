# Quartz Slab Optimizer - Advanced Bin-Packing Optimization

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple
import itertools

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

input_text = st.text_area("Dimensions:", value="""0.65 2.53
0.64 2.27
0.64 0.73
0.73 2.27
0.73 3.14
0.73 0.73
0.08 1.66
0.08 2.53
0.16 0.83
0.15 0.82""", height=200)

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

# --- Optimization over All Slab Sizes ---
def find_best_slab(pieces: List[Tuple[float, float]]):
    best_result = None
    for slab_h in QUARTZ_SLAB_SIZES:
        layout = best_fit_pack(pieces.copy(), slab_width=SLAB_FIXED_LENGTH, slab_height=slab_h)
        if not layout:
            continue  # Skip if nothing could be packed in this slab size
        used_area = sum(w * h for slab in layout for _, _, w, h in slab)
        total_area = len(layout) * SLAB_FIXED_LENGTH * slab_h
        waste = total_area - used_area
        if not best_result or waste < best_result['waste']:
            best_result = {
                "layout": layout,
                "slab_size": (SLAB_FIXED_LENGTH, slab_h),
                "slab_count": len(layout),
                "waste": waste
            }
    return best_result

# --- Run ---
if st.button("Run Slabbing"):
    pieces = parse_input(input_text)
    if not pieces:
        st.error("Invalid input.")
        st.stop()

    result = find_best_slab(pieces)
    if result is None:
        st.error("No slab size could accommodate your pieces.")
        st.stop()

    slab_w, slab_h = result['slab_size']
    smaller, larger = sorted([slab_w, slab_h])

    st.subheader("Results")
    st.write(f"Total Slabs: {result['slab_count']}")
    st.write(f"Waste: {result['waste']/10000:.2f} m²")
    st.write(f"Recommended Slab Size: {int(smaller)} x {int(larger)} cm")

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

    for slab in result['layout']:
        visualize_slab(slab, slab_w, slab_h)














