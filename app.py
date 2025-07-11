import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Quartz slab options: heights (short side), with fixed width = 320 cm
QUARTZ_SLAB_HEIGHTS = [60, 70, 80, 90, 100, 160]
SLAB_WIDTH = 320  # cm (long side, always horizontal)

st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("🪨 Quartz Slab Optimizer")
st.markdown("Enter required pieces in **meters**. The system will fit them into available slab sizes efficiently.")

# --- INPUT SECTION ---
df_input = st.data_editor(
    pd.DataFrame({"Width (m)": [0.6], "Height (m)": [2.3]}),
    num_rows="dynamic",
    use_container_width=True
)

# Convert user inputs (meters to cm)
pieces_cm = []
for _, row in df_input.iterrows():
    try:
        w = float(row["Width (m)"]) * 100
        h = float(row["Height (m)"]) * 100
        if w > 0 and h > 0:
            # Ensure width is longer side
            w, h = max(w, h), min(w, h)
            pieces_cm.append((round(w), round(h)))
    except:
        continue

if not pieces_cm:
    st.warning("Please input valid dimensions.")
    st.stop()

# --- SLAB PACKING FUNCTION ---
def pack_pieces(pieces, slab_height):
    slabs = []
    current_slab = []
    x_cursor = 0
    y_cursor = 0
    column_width = 0

    for piece in pieces:
        pw, ph = piece
        if y_cursor + ph <= slab_height:
            current_slab.append((x_cursor, y_cursor, pw, ph))
            y_cursor += ph
            column_width = max(column_width, pw)
        else:
            x_cursor += column_width
            if x_cursor + pw > SLAB_WIDTH:
                slabs.append(current_slab)
                current_slab = [(0, 0, pw, ph)]
                x_cursor = pw
                y_cursor = 0
                column_width = pw
            else:
                y_cursor = 0
                current_slab.append((x_cursor, y_cursor, pw, ph))
                y_cursor += ph
                column_width = max(column_width, pw)

    if current_slab:
        slabs.append(current_slab)

    return slabs

# --- SLAB SELECTION ---
best_slab = None
min_waste = float("inf")
best_layout = None

for slab_h in QUARTZ_SLAB_HEIGHTS:
    layout = pack_pieces(sorted(pieces_cm, key=lambda x: x[0]*x[1], reverse=True), slab_h)
    total_area_used = sum(w * h for _, _, w, h in sum(layout, []))
    total_area_available = len(layout) * SLAB_WIDTH * slab_h
    waste = total_area_available - total_area_used

    if waste < min_waste:
        min_waste = waste
        best_slab = slab_h
        best_layout = layout

# --- RESULTS ---
st.subheader(f"📏 Recommended Slab Size: **{SLAB_WIDTH} x {best_slab} cm** (landscape)")
st.write(f"🔢 Total Slabs Needed: {len(best_layout)}")
st.write(f"🗑️ Estimated Waste Area: **{min_waste:,.0f} cm²**")

# --- VISUALIZATION ---
for i, slab in enumerate(best_layout):
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.set_xlim(0, SLAB_WIDTH)
    ax.set_ylim(0, best_slab)
    ax.set_aspect('auto')
    ax.axis('off')

    for x, y, w, h in slab:
        rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor='skyblue')
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, f"{int(w)}×{int(h)}", ha='center', va='center', fontsize=8, color='black')

    st.pyplot(fig)

