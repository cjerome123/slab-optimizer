import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple

def can_fit_any_rotation(piece: Tuple[float, float], slab: Tuple[float, float]) -> Tuple[bool, Tuple[float, float]]:
    pw, ph = piece
    sw, sh = slab
    orientations = [(pw, ph), (ph, pw)]
    for ow, oh in orientations:
        if sw >= ow and sh >= oh:
            return True, (ow, oh)
    return False, (0, 0)

def nest_pieces(required_pieces: List[Tuple[float, float]], available_slabs: List[Tuple[float, float]]):
    results = []
    used_slabs = []
    available_pool = available_slabs.copy()

    while required_pieces and available_pool:
        slab = available_pool.pop(0)
        slab_w, slab_h = slab
        if slab_h > slab_w:
            slab_w, slab_h = slab_h, slab_w

        layout = []
        x_cursor = 0
        y_cursor = 0
        row_height = 0
        still_needed = []

        for piece in required_pieces:
            fits, orientation = can_fit_any_rotation(piece, (slab_w, slab_h))
            if not fits:
                still_needed.append(piece)
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
                still_needed.append(piece)

        if layout:
            results.append(((slab_w, slab_h), layout))
            used_slabs.append((slab_w, slab_h))
        required_pieces = still_needed

    return results, required_pieces, used_slabs

def draw_slab_layout(slab: Tuple[float, float], layout: List[Tuple[Tuple[float, float], Tuple[float, float]]]):
    fig, ax = plt.subplots(figsize=(10, 4))
    sw, sh = slab
    ax.add_patch(patches.Rectangle((0, 0), sw, sh, edgecolor='black', facecolor='lightgray'))
    for i, ((x, y), (w, h)) in enumerate(layout):
        ax.add_patch(patches.Rectangle((x, y), w, h, edgecolor='blue', facecolor='skyblue'))
        ax.text(x + w/2, y + h/2, f'{int(w)}x{int(h)}', ha='center', va='center', fontsize=8)
    ax.set_xlim(0, sw)
    ax.set_ylim(0, sh)
    ax.set_aspect('auto')
    ax.set_xlabel('Width (longer side)')
    ax.set_ylabel('Height (shorter side)')
    ax.set_title(f'Nesting Layout: {int(sw)} x {int(sh)} cm')
    st.pyplot(fig)

st.title("📦 Slab Nesting Optimizer (Landscape Layout)")

req_input = st.text_area("Enter required slab sizes (in meters, one per line: width height)", "0.73 2.28\n0.73 3.14\n0.15 0.82")
slab_input = st.text_area("Enter available slab sizes (in cm, one per line: width height)", "90 320\n90 320\n90 320")

if st.button("Nest Slabs"):
    try:
        required = []
        for line in req_input.strip().splitlines():
            w, h = map(float, line.strip().split())
            required.append((w * 100, h * 100))

        available = []
        for line in slab_input.strip().splitlines():
            w, h = map(float, line.strip().split())
            available.append((w, h))

        results, leftovers, used_slabs = nest_pieces(required, available)

        total_used_area = 0
        total_piece_area = 0

        for slab, layout in results:
            st.subheader(f"🪵 Slab: {int(slab[0])} x {int(slab[1])} cm")
            draw_slab_layout(slab, layout)
            total_used_area += slab[0] * slab[1]
            for (_, (w, h)) in layout:
                total_piece_area += w * h

        st.markdown("---")
        st.subheader("📊 Summary")
        st.write("**Slabs Used:**")
        for slab in used_slabs:
            st.text(f"{int(slab[0])} x {int(slab[1])} cm")

        st.write(f"**Total Area of Slabs Used:** {total_used_area / 10000:.2f} m²")
        st.write(f"**Wastage (Unused Area):** {(total_used_area - total_piece_area) / 10000:.2f} m²")

        if leftovers:
            st.warning("⚠️ These pieces did not fit in any slab:")
            for pw, ph in leftovers:
                st.text(f"{pw / 100:.2f} x {ph / 100:.2f} m")
    except Exception as e:
        st.error(f"Error: {str(e)}")

