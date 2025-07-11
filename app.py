import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Available Quartz slab heights (shorter side), 320 cm is always the long side
QUARTZ_SLAB_SIZES = [60, 70, 80, 90, 100, 160]
SLAB_FIXED_LENGTH = 320  # cm

st.set_page_config(page_title="Quartz Slab Optimizer", layout="wide")
st.title("🪨 Quartz Slab Optimizer (Auto Orientation)")
st.markdown("""
Paste your required piece dimensions (in **meters**), one per line.  
The system will auto-detect orientation and select the most efficient slab size.
""")

# --- INPUT BOX ---
input_text = st.text_area(
    "Enter required pieces (e.g., `0.63 2.03`):",
    value="0.63 2.03\n0.13 0.63\n0.13 2.03",
    height=150
)

# --- PARSE INPUT ---
pieces_raw = []
for line in input_text.strip().split("\n"):
    try:
        numbers = list(map(float, line.strip().split()))
        if len(numbers) == 2:
            a, b = numbers
            pieces_raw.append((a * 100, b * 100))  # Convert to cm
    except:
        continue

if not pieces_raw:
    st.warning("Please input at least one valid dimension pair (e.g., `0.6 2.3`).")
    st.stop()

# --- TRY ALL ORIENTATIONS & SLAB OPTIONS ---
def pack_pieces(pieces, slab_w, slab_h):
    """Simple top-left packing algorithm (landscape layout)."""
    slabs = []
    current_slab = []
    x_cursor = 0
    y_cursor = 0
    row_height = 0

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
                x_cursor = pw
                y_cursor = 0
                row_height = ph
            else:
                x_cursor = 0
                current_slab.append((x_cursor, y_cursor, pw, ph))
                x_cursor += pw
                row_height = max(row_height, ph)

    if current_slab:
        slabs.append(current_slab)
    return slabs

best_result = {
    "waste": float("inf"),
    "layout": None,
    "slab_size": None,
    "orientation": None
}

for slab_h in QUARTZ_SLAB_SIZES:
    # Try both orientations
    for orientation in ["horizontal", "vertical"]:
        if orientation == "horizontal":
            usable_w, usable_h = SLAB_FIXED_LENGTH, slab_h
            pieces = [(max(w, h), min(w, h)) for (w, h) in pieces_raw]  # Ensure wide first
        else:
            usable_w, usable_h = slab_h, SLAB_FIXED_LENGTH
            pieces = [(min(w, h), max(w, h)) for (w, h) in pieces_raw]  # Rotate

        layout = pack_pieces(sorted(pieces, key=lambda x: x[0]*x[1], reverse=True), usable_w, usable_h)
        used_area = sum(w*h for _, _, w, h in sum(layout, []))
        total_area = len(layout) * usable_w * usable_h
        waste = total_area - used_area

        if waste < best_result["waste"]:
            best_result = {
                "waste": waste,
                "layout": layout,
                "slab_size": (usable_w, usable_h),
                "orientation": orientation
            }

# --- SHOW RESULTS ---
slab_w, slab_h = best_result["slab_size"]
st.subheader(f"📏 Recommended Slab Size: **{slab_w} x {slab_h} cm** ({best_result['orientation']})")
st.write(f"🔢 Total Slabs Needed: {len(best_result['layout'])}")
st.write(f"🗑️ Estimated Waste Area: **{best_result['waste']:.0f} cm²**")

# --- VISUALIZATION ---
for i, slab in enumerate(best_result["layout"]):
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.set_xlim(0, slab_w)
    ax.set_ylim(0, slab_h)
    ax.set_aspect('auto')
    ax.axis('off')

    for x, y, w, h in slab:
        rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor='skyblue')
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, f"{int(w)}×{int(h)}", ha='center', va='center', fontsize=8, color='black')

    st.pyplot(fig)
