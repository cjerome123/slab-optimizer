# Real-time slab optimizer with multiprocessing and accurate mixed slab usage

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict
from multiprocessing import Pool, cpu_count
import itertools

QUARTZ_SLAB_SIZES = [60, 70, 80, 90, 100, 160]
SLAB_FIXED_LENGTH = 320

st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("🪨 Quartz Slab Optimizer (Accurate + Fast)")
st.markdown("Enter required dimensions in **meters**, one per line (e.g. `0.65 2.53`)")

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

# --- Parse input ---
pieces_raw = []
for line in input_text.strip().split("\n"):
    try:
        a, b = map(float, line.strip().split())
        pieces_raw.append((a * 100, b * 100))
    except:
        continue

if not pieces_raw:
    st.error("❌ Invalid input.")
    st.stop()

# --- Packing algorithm with rotation ---
def pack_pieces(pieces, slab_w, slab_h):
    slabs = []
    current = []
    x_cursor = y_cursor = row_height = 0

    for pw, ph in pieces:
        orientations = [(pw, ph), (ph, pw)]
        placed = False

        for ow, oh in orientations:
            if ow > slab_w or oh > slab_h:
                continue

            if x_cursor + ow <= slab_w:
                current.append((x_cursor, y_cursor, ow, oh))
                x_cursor += ow
                row_height = max(row_height, oh)
                placed = True
                break
            else:
                y_cursor += row_height
                if y_cursor + oh > slab_h:
                    break
                else:
                    x_cursor = 0
                    current.append((x_cursor, y_cursor, ow, oh))
                    x_cursor += ow
                    row_height = max(row_height, oh)
                    placed = True
                    break

        if not placed:
            slabs.append(current)
            current = []
            x_cursor = y_cursor = row_height = 0
            orientations = [(pw, ph), (ph, pw)]
            for ow, oh in orientations:
                if ow <= slab_w and oh <= slab_h:
                    current.append((0, 0, ow, oh))
                    x_cursor = ow
                    row_height = oh
                    break

    if current:
        slabs.append(current)
    return slabs

# --- Parallelized slab fit checker ---
def evaluate_uniform_slab(args):
    slab_h, orientation, raw_pieces = args
    slab_w, slab_hh = (SLAB_FIXED_LENGTH, slab_h) if orientation == "horizontal" else (slab_h, SLAB_FIXED_LENGTH)
    pieces = [(max(w, h), min(w, h)) if orientation == "horizontal" else (min(w, h), max(w, h)) for (w, h) in raw_pieces]

    if any(pw > slab_w and ph > slab_hh and ph > slab_w and pw > slab_hh for pw, ph in pieces):
        return None

    layout = pack_pieces(sorted(pieces, key=lambda x: x[0]*x[1], reverse=True), slab_w, slab_hh)
    if layout is None:
        return None

    used = sum(w*h for _, _, w, h in sum(layout, []))
    total = len(layout) * slab_w * slab_hh
    waste = total - used

    return {
        "strategy": "Uniform",
        "slab_size": (slab_w, slab_hh),
        "layout": layout,
        "waste": waste,
        "slab_count": len(layout)
    }

# --- Try all uniform slabs in parallel ---
args_list = list(itertools.product(QUARTZ_SLAB_SIZES, ["horizontal", "vertical"], [pieces_raw]))
with Pool(cpu_count()) as pool:
    uniform_results = pool.map(evaluate_uniform_slab, args_list)

uniform_results = [r for r in uniform_results if r]
best_uniform = min(uniform_results, key=lambda x: x['waste'], default=None)

# --- Mixed strategy ---
def try_mixed_layout(pieces):
    remaining = sorted(pieces, key=lambda x: x[0]*x[1], reverse=True)
    layout = defaultdict(list)

    while remaining:
        piece = remaining.pop(0)
        fit = False

        for slab_h in sorted(QUARTZ_SLAB_SIZES, reverse=True):
            slab_w = SLAB_FIXED_LENGTH
            slab_hh = slab_h

            candidates = [piece] + [p for p in remaining if max(p) <= slab_w and min(p) <= slab_hh]
            packed = pack_pieces(candidates, slab_w, slab_hh)
            if packed:
                layout[(slab_w, slab_hh)].append(packed[0])
                used = set(candidates[:len(packed[0])])
                remaining = [p for p in remaining if p not in used]
                fit = True
                break

        if not fit:
            return None

    used_area = sum(w*h for _, _, w, h in sum([sum(l, []) for l in layout.values()], []))
    total_area = sum(w * h * len(l) for (w, h), l in layout.items())
    waste = total_area - used_area
    count = sum(len(l) for l in layout.values())

    return {
        "strategy": "Mixed",
        "layout": layout,
        "waste": waste,
        "slab_count": count
    }

best_mixed = try_mixed_layout([(max(w, h), min(w, h)) for (w, h) in pieces_raw]) or {"waste": float("inf")}

# --- Choose best ---
result = best_uniform if best_uniform and best_uniform["waste"] <= best_mixed["waste"] else best_mixed
strategy = result["strategy"]

# --- Display ---
st.subheader(f"📦 Strategy: **{strategy}**")
st.write(f"🔢 Total Slabs: **{result['slab_count']}**")
st.write(f"🗑️ Waste: **{result['waste']/10000:.2f} m²**")

if strategy == "Uniform":
    sw, sh = result["slab_size"]
    smaller, larger = sorted([sw, sh])
    st.write(f"📏 Slab Size: **{int(smaller)} x {int(larger)} cm**")
else:
    slab_list = ', '.join([f"{min(k)}×{max(k)} ({len(v)})" for k, v in result["layout"].items()])
    st.write(f"📏 Slabs Used: {slab_list}")

# --- Visualize ---
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

if strategy == "Uniform":
    for slab in result["layout"]:
        visualize_slab(slab, *result["slab_size"])
else:
    for (sw, sh), slabs in result["layout"].items():
        for slab in slabs:
            visualize_slab(slab, sw, sh)






