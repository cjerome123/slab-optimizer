# Quartz Slab Optimizer - Rebuilt for Structured Shelf Packing

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple

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
            pieces.append((min(a, b) * 100, max(a, b) * 100))  # height, width
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

# --- Shelf-based Packing ---
def shelf_pack(pieces: List[Tuple[float, float]], slab_width: float, slab_height: float):
    remaining = sorted(pieces, key=lambda x: x[1], reverse=True)  # sort by width desc
    slabs = []

    while remaining:
        current_slab = []
        y = 0
        shelf_height = 0
        shelf = []
        while remaining:
            fit = False
            for i, (h, w) in enumerate(remaining):
                if w > slab_width or h > slab_height:
                    continue
                if sum(p[1] for p in shelf) + w <= slab_width:
                    shelf.append((h, w))
                    shelf_height = max(shelf_height, h)
                    remaining.pop(i)
                    fit = True
                    break
            if not fit:
                if not shelf:
                    break
                x = 0
                for sh, sw in shelf:
                    current_slab.append((x, y, sw, sh))
                    x += sw
                y += shelf_height
                shelf = []
                shelf_height = 0
                if y >= slab_height:
                    break
        if shelf:
            x = 0
            for sh, sw in shelf:
                current_slab.append((x, y, sw, sh))
                x += sw
        slabs.append(current_slab)

    return slabs

# --- Optimization ---
def find_best_slab(pieces: List[Tuple[float, float]]):
    best_result = None
    for slab_h in QUARTZ_SLAB_SIZES:
        layout = shelf_pack(pieces.copy(), slab_width=SLAB_FIXED_LENGTH, slab_height=slab_h)
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











