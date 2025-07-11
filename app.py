import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict

# Quartz slabs (height values in cm), fixed 320 cm long side
QUARTZ_SLAB_SIZES = [60, 70, 80, 90, 100, 160]
SLAB_FIXED_LENGTH = 320  # cm

st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("🪨 Quartz Slab Optimizer (Auto: Best Uniform or Mixed)")
st.markdown("Paste dimensions like `0.65 2.53`, one per line.")

# --- INPUT AREA ---
input_text = st.text_area("Required pieces (in meters):", value="""
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

# --- PARSE INPUT ---
pieces_raw = []
for line in input_text.strip().split("\n"):
    try:
        a, b = map(float, line.strip().split())
        pieces_raw.append((a * 100, b * 100))  # m to cm
    except:
        continue

if not pieces_raw:
    st.warning("Invalid input. Use lines like `0.6 2.3`")
    st.stop()

# --- SHARED SLAB PACKING FUNCTION ---
def pack_pieces(pieces, slab_w, slab_h):
    """Greedy top-left packer for a single slab."""
    slabs = []
    current_slab = []
    x_cursor, y_cursor, row_height = 0, 0, 0

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

# --- MODE 1: UNIFORM SLAB SIZE TEST ---
best_uniform = {
    "strategy": "Uniform",
    "slab_size": None,
    "layout": None,
    "waste": float("inf"),
    "slab_count": 0
}

for slab_h in QUARTZ_SLAB_SIZES:
    for orientation in ["horizontal", "vertical"]:
        if orientation == "horizontal":
            slab_w, slab_hh = SLAB_FIXED_LENGTH, slab_h
            pieces = [(max(w, h), min(w, h)) for (w, h) in pieces_raw]
        else:
            slab_w, slab_hh = slab_h, SLAB_FIXED_LENGTH
            pieces = [(min(w, h), max(w, h)) for (w, h) in pieces_raw]

        if any(pw > slab_w or ph > slab_hh for pw, ph in pieces):
            continue

        layout = pack_pieces(sorted(pieces, key=lambda x: x[0] * x[1], reverse=True), slab_w, slab_hh)
        used = sum(w * h for _, _, w, h in sum(layout, []))
        total = len(layout) * slab_w * slab_hh
        waste = total - used

        if waste < best_uniform["waste"]:
            best_uniform.update({
                "slab_size": (slab_w, slab_hh),
                "layout": layout,
                "waste": waste,
                "slab_count": len(layout)
            })

# --- MODE 2: MIXED SLABS ---
def try_mixed_layout(pieces):
    slabs_used = defaultdict(list)
    remaining = sorted(pieces, key=lambda x: x[0]*x[1], reverse=True)
    slab_usage = []

    while remaining:
        piece = remaining.pop(0)
        fit_found = False

        for slab_h in sorted(QUARTZ_SLAB_SIZES, reverse=True):
            for orientation in ["horizontal", "vertical"]:
                slab_w, slab_hh = (SLAB_FIXED_LENGTH, slab_h) if orientation == "horizontal" else (slab_h, SLAB_FIXED_LENGTH)
                pw, ph = (max(piece), min(piece)) if orientation == "horizontal" else (min(piece), max(piece))

                if pw > slab_w or ph > slab_hh:
                    continue

                # Try to pack current + others that fit
                fit_group = [piece]
                leftovers = []

                for p in remaining:
                    tw, th = (max(p), min(p)) if orientation == "horizontal" else (min(p), max(p))
                    if tw <= slab_w and th <= slab_hh:
                        fit_group.append((tw, th))
                    else:
                        leftovers.append(p)

                layout = pack_pieces(fit_group, slab_w, slab_hh)
                used = sum(w*h for _, _, w, h in sum(layout, []))
                waste = slab_w * slab_hh * len(layout) - used

                if layout:
                    slabs_used[(slab_w, slab_hh)].append(layout[0])  # Just record 1 slab per group
                    remaining = leftovers
                    fit_found = True
                    break
            if fit_found:
                break

        if not fit_found:
            return None  # At least one piece couldn't be fit

    # Flatten and measure waste
    total_slabs = sum(len(v) for v in slabs_used.values())
    total_area = sum(w * h * len(slabs) for (w, h), slabs in slabs_used.items())
    used_area = sum(w * h for _, _, w, h in sum([sum(v, []) for v in slabs_used.values()], []))
    total_waste = total_area - used_area

    return {
        "strategy": "Mixed",
        "slab_size": None,
        "layout": slabs_used,
        "waste": total_waste,
        "slab_count": total_slabs
    }

best_mixed = try_mixed_layout([(max(w, h), min(w, h)) for (w, h) in pieces_raw]) or {"waste": float("inf")}

# --- DECIDE BEST OVERALL ---
if best_uniform["waste"] <= best_mixed["waste"]:
    result = best_uniform
    strategy = "Uniform"
else:
    result = best_mixed
    strategy = "Mixed"

# --- DISPLAY RESULT ---
st.subheader(f"📦 Strategy: **{strategy} Slabs**")
if strategy == "Uniform":
    sw, sh = result["slab_size"]
    smaller, larger = sorted([sw, sh])
    st.markdown(f"📏 Slab Size Used: **{int(smaller)} x {int(larger)} cm**")
else:
    slab_list = ', '.join([f"{min(k)}×{max(k)} ({len(v)})" for k, v in result["layout"].items()])
    st.markdown(f"📏 Slabs Used: {slab_list}")

waste_sqm = result["waste"] / 10_000
st.write(f"🔢 Total Slabs: **{result['slab_count']}**")
st.write(f"🗑️ Waste: **{waste_sqm:.2f} m²**")

# --- VISUALIZATION ---
if strategy == "Uniform":
    sw, sh = result["slab_size"]
    for i, slab in enumerate(result["layout"]):
        fig, ax = plt.subplots(figsize=(12, 3))
        ax.set_xlim(0, sw)
        ax.set_ylim(0, sh)
        ax.set_aspect('auto')
        ax.axis('off')
        for x, y, w, h in slab:
            rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor='skyblue')
            ax.add_patch(rect)
            ax.text(x + w/2, y + h/2, f"{int(w)}×{int(h)}", ha='center', va='center', fontsize=8)
        st.pyplot(fig)
else:
    for (sw, sh), slabs in result["layout"].items():
        for slab in slabs:
            fig, ax = plt.subplots(figsize=(12, 3))
            ax.set_xlim(0, sw)
            ax.set_ylim(0, sh)
            ax.set_aspect('auto')
            ax.axis('off')
            for x, y, w, h in slab:
                rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor='skyblue')
                ax.add_patch(rect)
                ax.text(x + w/2, y + h/2, f"{int(w)}×{int(h)}", ha='center', va='center', fontsize=8)
            st.pyplot(fig)



