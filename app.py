# Real-time slab optimizer with global optimization for better slab usage

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict
import itertools
import math

QUARTZ_SLAB_SIZES = [60, 70, 80, 90, 100, 160]
SLAB_FIXED_LENGTH = 320

st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("Quartz Slab Optimizer (Globally Optimized)")
st.markdown("Enter required dimensions in **meters**, one per line (e.g. `0.65 2.53`) and click Run")

# --- Input ---
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

@st.cache_data(show_spinner=False)
def compute_optimal_slabbing(pieces_raw):
    def can_fit(piece, x, y, placed, slab_w, slab_h):
        px, py = piece
        if x + px > slab_w or y + py > slab_h:
            return False
        for ox, oy, ow, oh in placed:
            if not (x + px <= ox or x >= ox + ow or y + py <= oy or y >= oy + oh):
                return False
        return True

    def pack_into_slab(pieces, slab_w, slab_h):
        placed = []
        for piece in pieces:
            pw, ph = piece
            fit = False
            for orientation in [(pw, ph), (ph, pw)]:
                ow, oh = orientation
                for y in range(0, slab_h + 1):
                    for x in range(0, slab_w + 1):
                        if can_fit((ow, oh), x, y, placed, slab_w, slab_h):
                            placed.append((x, y, ow, oh))
                            fit = True
                            break
                    if fit:
                        break
                if fit:
                    break
            if not fit:
                return None
        return placed

    def globally_pack(pieces, slab_w, slab_h):
        best_layout = []
        remaining = pieces.copy()
        slabs = []

        while remaining:
            n = len(remaining)
            best = None
            best_fit = None
            for r in range(n, 0, -1):
                for combo in itertools.combinations(remaining, r):
                    layout = pack_into_slab(list(combo), slab_w, slab_h)
                    if layout:
                        if not best or sum(w*h for _, _, w, h in layout) > sum(w*h for _, _, w, h in best):
                            best = layout
                            best_fit = combo
                if best:
                    break
            if best:
                slabs.append(best)
                for p in best_fit:
                    remaining.remove(p)
            else:
                break

        used_area = sum(w*h for _, _, w, h in sum(slabs, []))
        total_area = len(slabs) * slab_w * slab_h
        waste = total_area - used_area

        return {
            "strategy": "Uniform",
            "slab_size": (slab_w, slab_h),
            "layout": slabs,
            "waste": waste,
            "slab_count": len(slabs)
        }

    best_result = None
    for slab_h in QUARTZ_SLAB_SIZES:
        result = globally_pack(pieces_raw, SLAB_FIXED_LENGTH, slab_h)
        if not best_result or result['waste'] < best_result['waste']:
            best_result = result

    return best_result

if st.button("Run Slabbing"):
    pieces_raw = []
    for line in input_text.strip().split("\n"):
        try:
            a, b = map(float, line.strip().split())
            pieces_raw.append((a * 100, b * 100))
        except:
            continue

    if not pieces_raw:
        st.error("Invalid input.")
        st.stop()

    result = compute_optimal_slabbing(pieces_raw)

    st.subheader(f"Strategy: {result['strategy']}")
    st.write(f"Total Slabs: {result['slab_count']}")
    st.write(f"Waste: {result['waste']/10000:.2f} m²")
    sw, sh = result["slab_size"]
    smaller, larger = sorted([sw, sh])
    st.write(f"Slab Size: {int(smaller)} x {int(larger)} cm")

    def visualize_slab(slab_data, slab_w, slab_h):
        fig, ax = plt.subplots(figsize=(12, 3))
        ax.set_xlim(0, slab_w)
        ax.set_ylim(0, slab_h)
        ax.set_aspect('auto')
        ax.axis('off')
        for x, y, w, h in slab_data:
            rect = patches.Rectangle((x, y), w, h, edgecolor='black', facecolor='skyblue', lw=1)
            ax.add_patch(rect)
            ax.text(x + w/2, y + h/2, f"{int(w)}×{int(h)}", ha='center', va='center', fontsize=8)
        st.pyplot(fig)

    for slab in result["layout"]:
        visualize_slab(slab, *result["slab_size"])










