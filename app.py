import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple

def can_fit(piece: Tuple[float, float], slab: Tuple[float, float]) -> Tuple[bool, Tuple[float, float]]:
    pw, ph = piece
    sw, sh = slab
    if sw >= pw and sh >= ph:
        return True, (pw, ph)
    elif sw >= ph and sh >= pw:
        return True, (ph, pw)  # rotated
    return False, (0, 0)

def nest_pieces(required_pieces: List[Tuple[float, float]], available_slabs: List[Tuple[float, float]]):
    results = []
    used_slabs = []

    for slab_index, slab in enumerate(available_slabs):
        slab_w, slab_h = slab
        if slab_h > slab_w:
            slab_w, slab_h = slab_h, slab_w  # Ensure landscape orientation
        layout = []
        x_cursor = 0
        y_cursor = 0
        row_height = 0
        remaining_pieces = []

        for piece in required_pieces:
            fits, orientation = can_fit(piece, (slab_w, slab_h))
            if not fits:
                remaining_pieces.append(piece)
                continue

            pw, ph = orientation
            if x_cursor + pw <= slab_w and y_cursor + ph <= slab_h:
                layout.append(((x_cursor, y_cursor), (pw, ph)))
                x_cursor += pw
                row_height = max(row_height, ph)
            elif y_cursor + row_height + ph <= slab_h:
                x_cursor = 0
                y_cursor += row_height
                row_height = ph
                layout.append(((x_cursor, y_cursor), (pw, ph)))
                x_cursor += pw
            else:
                remaining_pieces.append(piece)

        if layout:
            results.append(((slab_w, slab_h), layout))
            used_slabs.append((slab_w, slab_h))
        required_pieces = remaining_pieces

    return results, required_pieces

def draw_slab_layout(slab: Tuple[float, float], layout: List[Tuple[Tuple[float, float], Tuple[float, float]]]):
    fig, ax = plt.subplots(figsize=(10, 4))
    sw, sh = slab
    ax.add_patch(patches.Rectangle((0, 0), sw, sh, edgecolor='black', facecolor='lightgray'))
    for i, ((x, y), (w, h)) in enumerate(layout):
        ax.add_patch(patches.Rectangle((x, y), w, h, edgecolor='blue', facecolor='skyblue'))
        ax.text(x + w/2, y + h/2, f'{i+1}', ha='center', va='center', fontsize=8)
    ax.set_xlim(0, sw)
    ax.set_ylim(0, sh)
    ax.set_aspect('auto')
    ax.set_xlabel('Width (longer side)')
    ax.set_ylabel('Height (shorter side)')
    ax.set_title('Nesting Layout (Landscape)')
    st.pyplot(fig)

st.title("📦 Slab Nesting Optimizer (Landscape Layout)")

req_input = st.text_area("Enter required slab sizes (in meters, one per line: width height)", "0.90 1.80\n0.60 1.20\n1.00 0.60")
slab_input = st.text_area("Enter available slab sizes (in cm, one per line: width height)", "100 320\n120 300")

if st.button("Nest Slabs"):
    try:
        required = []
        for line in req_input.strip().splitlines():
            w, h = map(float, line.strip().split())
            required.append((w * 100, h * 100))  # convert to cm

        available = []
        for line in slab_input.strip().splitlines():
            w, h = map(float, line.strip().split())
            available.append((w, h))

        results, leftovers = nest_pieces(required, available)

        for i, (slab, layout) in enumerate(results):
            st.subheader(f"🪵 Slab {i+1}: {slab[0]} x {slab[1]} cm")
            draw_slab_layout(slab, layout)

        if leftovers:
            st.warning("⚠️ These pieces did not fit in any slab:")
            for pw, ph in leftovers:
                st.text(f"{pw/100:.2f} x {ph/100:.2f} m")
    except Exception as e:
        st.error(f"Error: {str(e)}")































