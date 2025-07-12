import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import uuid

st.set_page_config(layout="wide")
st.title("📐 Cutlist Optimizer (Streamlit)")

# --- Helper Functions ---
def parse_input(text):
    lines = text.strip().split("\n")
    items = []
    for line in lines:
        parts = line.strip().split(",")
        if len(parts) < 3:
            continue
        width, height, qty = map(int, parts[:3])
        items.extend([(width, height)] * qty)
    return items

def parse_slabs(text):
    lines = text.strip().split("\n")
    slabs = []
    for line in lines:
        parts = line.strip().split(",")
        if len(parts) < 2:
            continue
        width, height = map(int, parts[:2])
        slabs.append((width, height))
    return slabs


def fit_parts_to_slabs(parts, slabs):
    placed = []
    leftovers = []
    used_slabs = []

    for slab_index, (sw, sh) in enumerate(slabs):
        slab_id = str(uuid.uuid4())
        x, y, row_height = 0, 0, 0
        layout = []
        remaining_parts = []

        for pw, ph in parts:
            placed_flag = False
            # Try both orientations
            for rw, rh in [(pw, ph), (ph, pw)]:
                if x + rw <= sw and y + rh <= sh:
                    layout.append((x, y, rw, rh))
                    placed.append((rw, rh, slab_id))
                    x += rw
                    row_height = max(row_height, rh)
                    placed_flag = True
                    break

            if not placed_flag:
                # Try new row
                if y + row_height + ph <= sh:
                    x = 0
                    y += row_height
                    row_height = 0
                    for rw, rh in [(pw, ph), (ph, pw)]:
                        if x + rw <= sw and y + rh <= sh:
                            layout.append((x, y, rw, rh))
                            placed.append((rw, rh, slab_id))
                            x += rw
                            row_height = max(row_height, rh)
                            placed_flag = True
                            break

            if not placed_flag:
                remaining_parts.append((pw, ph))

        used_slabs.append((sw, sh, layout, slab_id))
        parts = remaining_parts
        if not parts:
            break

    leftovers = parts
    return used_slabs, leftovers


def plot_layout(slabs):
    for i, (sw, sh, layout, slab_id) in enumerate(slabs):
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.set_title(f"Slab {i+1} - {sw}x{sh} cm")
        ax.set_xlim(0, sw)
        ax.set_ylim(0, sh)
        ax.set_aspect('equal')
        ax.invert_yaxis()

        for x, y, w, h in layout:
            ax.add_patch(Rectangle((x, y), w, h, edgecolor='black', facecolor='#aad3df'))
            ax.text(x + w/2, y + h/2, f"{w}x{h}", ha='center', va='center', fontsize=8)

        st.pyplot(fig)

# --- Sidebar Inputs ---
st.sidebar.header("🧾 Input Dimensions")
part_input = st.sidebar.text_area("Parts (width,height,qty)",
                                  "30,20,4\n50,40,2\n60,30,1")
slab_input = st.sidebar.text_area("Slabs (width,height)",
                                  "100,200\n120,240")

if st.sidebar.button("🔄 Optimize"):
    parts = parse_input(part_input)
    slabs = parse_slabs(slab_input)

    st.subheader("📦 Layout Results")
    used, leftover = fit_parts_to_slabs(parts, slabs)
    plot_layout(used)

    st.subheader("🚫 Leftover Parts")
    if leftover:
        for w, h in leftover:
            st.write(f"{w} x {h} cm")
    else:
        st.success("All parts were fitted into slabs!")























