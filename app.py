# ✅ IMPLEMENTATION OF UI IMPROVEMENTS 1, 3, 4, 5
# ======================================================
# - (1) Input layout with columns and expander
# - (3) Sidebar settings for Smart Combo toggle
# - (4) Summary presentation with st.metric
# - (5) Enhanced visualization: add legend + labels

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple
import itertools

# ... [functions unchanged: can_fit_any_rotation, guillotine_split, sort_pieces, try_combo, nest_pieces_guillotine] ...


def draw_slab_layout(slab: Tuple[float, float], layout: List[Tuple[Tuple[float, float], Tuple[float, float]]]):
    fig, ax = plt.subplots(figsize=(10, 4))
    sw, sh = slab
    ax.add_patch(patches.Rectangle((0, 0), sw, sh, edgecolor='black', facecolor='lightgray', label='Free Area'))
    for idx, ((x, y), (w, h)) in enumerate(layout):
        ax.add_patch(patches.Rectangle((x, y), w, h, edgecolor='blue', facecolor='skyblue', label='Fitted Piece' if idx == 0 else ""))
        ax.text(x + w / 2, y + h / 2, f'P{idx+1}\n{int(w)}x{int(h)}', ha='center', va='center', fontsize=7)
    ax.set_xlim(0, sw)
    ax.set_ylim(0, sh)
    ax.set_aspect('auto')
    ax.set_xlabel('Width (longer side)')
    ax.set_ylabel('Height (shorter side)')
    ax.set_title(f'Nesting Layout: {int(sw)} x {int(sh)} cm')
    ax.legend(loc='upper right')
    st.pyplot(fig)


st.set_page_config(layout="wide")
st.title("📦 Slab Nesting Optimizer (Guillotine Packing)")

# (3) Sidebar settings
with st.sidebar:
    smart_combo = st.checkbox("🔀 Enable Smart Combo (optimize slab selection)", value=True)

# (1) Expander + Columns for Inputs
with st.expander("📥 Input Dimensions", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        req_input = st.text_area("Required pieces (in meters)",
                                 "0.65 2.53\n0.64 2.28\n0.64 0.73\n0.73 2.28\n0.73 3.14\n0.73 0.73\n0.08 1.67\n0.08 2.53\n0.16 0.83\n0.15 0.82")
    with col2:
        slab_input = st.text_area("Available slabs (in cm)", "160 320\n160 320")

if st.button("📐 Nest Slabs"):
    try:
        required = []
        for line in req_input.strip().splitlines():
            w, h = map(float, line.strip().split())
            required.append((w * 100, h * 100))

        available = []
        for line in slab_input.strip().splitlines():
            w, h = map(float, line.strip().split())
            available.append((w, h))

        results, leftovers, used_slabs = nest_pieces_guillotine(required, available, use_smart_combo=smart_combo)

        total_used_area = 0
        total_piece_area = 0

        st.markdown("---")
        st.subheader("🧩 Slab Layouts")
        for slab, layout in results:
            st.markdown(f"**Slab:** {int(slab[0])} x {int(slab[1])} cm")
            draw_slab_layout(slab, layout)
            total_used_area += slab[0] * slab[1]
            for (_, (w, h)) in layout:
                total_piece_area += w * h

        # (4) Summary metrics
        st.markdown("---")
        st.subheader("📊 Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🪵 Slabs Used", f"{len(used_slabs)}")
        with col2:
            st.metric("📐 Total Slab Area", f"{total_used_area / 10000:.2f} m²")
        with col3:
            st.metric("🗑️ Wastage Area", f"{(total_used_area - total_piece_area) / 10000:.2f} m²")

        if leftovers:
            st.warning("⚠️ These pieces did not fit in any slab:")
            for pw, ph in leftovers:
                st.text(f"{pw / 100:.2f} x {ph / 100:.2f} m")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

