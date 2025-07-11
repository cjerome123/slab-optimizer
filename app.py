import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict

# --- Constants ---
QUARTZ_SLAB_SIZES = [60, 70, 80, 90, 100, 160]  # heights in cm
SLAB_FIXED_LENGTH = 320  # fixed long side in cm

# --- Page Config ---
st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("🪨 Quartz Slab Optimizer (Auto: Uniform or Mixed)")
st.markdown("Paste required dimensions in **meters** (e.g., `0.65 2.53` per line).")

# --- Input ---
input_text = st.text_area("Enter piece dimensions (one per line):", value="""
0.65 2.53
0.64 2.27
0.64 0.73
0.73 2.27
0.73 3.14
0.73 0.73
0.08 1.66
0.08 2.53
0.16 0.83
0.15 0.82
""", height=200)

# --- Parse Input ---
pieces_raw = []
for line in input_text.strip().split("\n"):
    try:
        a, b = map(float, line.strip().split())
        pieces_raw.append((a * 100, b * 100))  # convert meters to cm
    except:
        continue

if not pieces_raw:
    st.error("Please enter at least one valid dimension (e.g., `0.6 2.3`).")
    st.stop()

# --- Packing Function ---
def pack_pieces(pieces, slab_w, slab_h):
    slabs = []
    current_slab = []
    x_cursor = y_cursor = row_height = 0

    for pw, ph in pieces:
        if x_cursor + pw <= slab_w:
            current_slab.append((x_cursor, y_cursor, pw, ph))
            x_cursor += pw
            row_height = max(row_height, ph)
        else:
            y_cursor += row_height
            if y_cursor + ph > slab_h:
                slabs.append(current_slab)
                current_slab = [(0, 0, pw, ph)]
                x_cursor, y_cursor, row_height = pw, 0, ph
            else:
                x_cursor = 0
                current_slab.append((x_cursor, y_cursor, pw, ph))
                x_cursor += pw
                row_height = max(row_height, ph)

    if current_slab:
        slabs.append(current_slab)
    return slabs

# --- Uniform Slab Strategy ---
best_uniform = {
    "strategy": "Uniform",
    "slab_size": None,
    "layout": None,
    "waste": float("inf"),
    "slab_count": 0
}

for slab_h in QUARTZ_SLAB_SIZES:
    for orientation in ["horizontal", "vertical"]:
        slab_w, slab_hh = (SLAB_FIXED_LENGTH, slab_h) if orientation == "horizontal" else (slab_h, SLAB_FIXED_LENGTH)
        pieces = [(max(w, h), min(w, h)) if orientation == "horizontal" else (min(w, h), max(w, h)) for (w, h) in pieces_raw]

        if any(pw > slab_w or ph > slab_hh for pw, ph in pieces):
            continue

        layout = pack_pieces(sorted(pieces, key=lambda x: x[0] * x[1], reverse=True), slab_w, slab_hh)
        used_area = sum(w * h for _, _, w, h in sum(layout, []))
        total_area = len(layout) * slab_w * slab_hh
        waste = total_area - used_area

        if waste < best_uniform["waste"]:
            best_uniform.update({
                "slab_size": (slab_w, slab_hh),
                "layout": layout,
                "waste": waste,
                "slab_count": len(layout)
            })

# --- Mixed Slab Strategy ---
def try_mixed_layout(pieces):
    remaining = sorted(pieces, key=lambda x: x[0] * x[1], reverse=True)
    layout = defaultdict(list)

    while remaining:
        piece = remaining.pop(0)
        fit = False

        for slab_h in sorted(QUARTZ_SLAB_SIZES, reverse=True):
            for orientation in ["horizontal", "vertical"]:
                slab_w, slab_hh = (SLAB_FIXED_LENGTH, slab_h) if orientation == "horizontal" else (slab_h, SLAB_FIXED_LENGTH)
                pw, ph = (max(piece), min(piece)) if orientation == "horizontal" else (min(piece), max(piece))

                if pw > slab_w or ph > slab_hh:
                    continue

                fit_group = [piece]
                leftovers = []

                for other in remaining:
                    tw, th = (max(other), min(other)) if orientation == "horizontal" else (min(other), max(other))
                    if tw <= slab_w and th <= slab_hh:
                        fit_group.append((tw, th))
                    else:
                        leftovers.append(other)

                packed = pack_pieces(fit_group, slab_w, slab_hh)
                if packed:
                    layout[(slab_w, slab_hh)].append(packed[0])
                    remaining = leftovers
                    fit = True
                    break
            if fit:
                break

        if not fit:
            return None

    used_area = sum(w * h for _, _, w, h in sum([sum(l, []) for l in layout.values()], []))
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

# --- Choose Best Strategy ---
if best_uniform["waste"] <= best_mixed["waste"]:
    result = best_uniform
    strategy = "Uniform"
else:
    result = best_mixed
    strategy = "Mixed"

# --- Show Result Summary ---
st.subheader(f"📦 Strategy: **{strategy} Slab Usage**")
st.write(f"🔢 Total Slabs Used: **{result['slab_count']}**")
st.write(f"🗑️ Estimated Waste: **{result['waste'] / 10_000:.2f} m²**")

if strategy == "Uniform":
    sw, sh = result["slab_size"]
    smaller, larger = sorted([sw, sh])
    st.write(f"📏 Recommended Slab Size: **{int(smaller)} x {int(larger)} cm**")
else:
    slab_list = ', '.join([f"{min(s)}×{max(s)} ({len(l)})" for s, l in result["layout"].items()])
    st.write(f"📏 Slabs Used: {slab_list}")

# --- Visualization ---
def visualize_slab(slab_data, slab_w, slab_h):
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.set_xlim(0, slab_w)
    ax.set_ylim(0, slab_h)
    ax.set_aspect('auto')
    ax.axis('off')

    for x, y, w, h in slab_data:
        rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor='skyblue')
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, f"{int(w)}×{int(h)}", ha='center', va='center', fontsize=8)

    st.pyplot(fig)

if strategy == "Uniform":
    sw, sh = result["slab_size"]
    for slab in result["layout"]:
        visualize_slab(slab, sw, sh)
else:
    for (sw, sh), slabs in result["layout"].items():
        for slab in slabs:
            visualize_slab(slab, sw, sh)




