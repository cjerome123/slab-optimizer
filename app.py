import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple

def fit_slab(required_m: Tuple[float, float], available_slabs_cm: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], float, Tuple[float, float], bool]:
    required_w = required_m[0] * 100
    required_h = required_m[1] * 100

    best_fit = None
    least_waste = float('inf')
    orientation = (required_w, required_h)
    rotated = False

    for slab in available_slabs_cm:
        slab_w, slab_h = slab

        if slab_w >= required_w and slab_h >= required_h:
            waste = (slab_w * slab_h) - (required_w * required_h)
            if waste < least_waste:
                best_fit = slab
                least_waste = waste
                orientation = (required_w, required_h)
                rotated = False

        elif slab_w >= required_h and slab_h >= required_w:
            waste = (slab_w * slab_h) - (required_w * required_h)
            if waste < least_waste:
                best_fit = slab
                least_waste = waste
                orientation = (required_h, required_w)
                rotated = True

    return best_fit, least_waste, orientation, rotated

def draw_layout(slab_size: Tuple[float, float], piece_size: Tuple[float, float]):
    fig, ax = plt.subplots()
    slab_w, slab_h = slab_size
    piece_w, piece_h = piece_size

    ax.add_patch(patches.Rectangle((0, 0), slab_w, slab_h, edgecolor='black', facecolor='lightgray'))
    ax.add_patch(patches.Rectangle((0, 0), piece_w, piece_h, edgecolor='blue', facecolor='skyblue'))

    ax.set_xlim(0, slab_w)
    ax.set_ylim(0, slab_h)
    ax.set_aspect('equal')
    ax.set_title('Slab Layout')
    st.pyplot(fig)

st.title("🔍 Slab Fitting Optimizer with Layout")

req_input = st.text_area("Enter required slab sizes (in meters, format: width height per line)", "0.90 1.80\n0.60 1.20")
slab_input = st.text_area("Enter available slab sizes (in cm, format: width height per line)", "60 320\n90 300\n100 320")

if st.button("Optimize Slabs"):
    try:
        required_list = []
        for line in req_input.strip().splitlines():
            w, h = map(float, line.strip().split())
            required_list.append((w, h))

        available = []
        for line in slab_input.strip().splitlines():
            w, h = map(float, line.strip().split())
            available.append((w, h))

        for i, required in enumerate(required_list):
            best_fit, waste, orientation, rotated = fit_slab(required, available)

            st.subheader(f"🧩 Required Piece {i+1}: {required[0]}m x {required[1]}m")
            if best_fit:
                st.success(f"✅ Best fit: {best_fit[0]} cm x {best_fit[1]} cm with {waste:.2f} cm² waste. {'(Rotated)' if rotated else ''}")
                draw_layout(best_fit, orientation)
            else:
                st.error("❌ No suitable slab found for this piece.")

    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")































