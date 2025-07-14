import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple
import itertools


def can_fit_any_rotation(piece: Tuple[float, float], space: Tuple[float, float]) -> Tuple[bool, Tuple[float, float]]:
    pw, ph = piece
    sw, sh = space
    for orientation in [(pw, ph), (ph, pw)]:
        if orientation[0] <= sw and orientation[1] <= sh:
            return True, orientation
    return False, (0, 0)


def guillotine_split(free_spaces: List[Tuple[float, float, float, float]],
                     pw: float, ph: float) -> Tuple[Tuple[float, float], List[Tuple[float, float, float, float]]]:
    for i, (fx, fy, fw, fh) in enumerate(free_spaces):
        fits, orientation = can_fit_any_rotation((pw, ph), (fw, fh))
        if fits:
            ow, oh = orientation
            px, py = fx, fy
            new_spaces = []
            new_spaces.append((fx + ow, fy, fw - ow, oh))
            new_spaces.append((fx, fy + oh, fw, fh - oh))
            free_spaces.pop(i)
            for s in new_spaces:
                if s[2] > 0 and s[3] > 0:
                    free_spaces.append(s)
            return (px, py), orientation
    return None, None


def sort_pieces(pieces: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    return sorted(pieces, key=lambda x: x[0] * x[1], reverse=True)


def try_combo(required_pieces: List[Tuple[float, float]], combo: List[Tuple[float, float]]):
    results = []
    used_slabs = []
    pieces = sort_pieces(required_pieces)

    for slab in combo:
        sw, sh = slab
        if sh > sw:
            sw, sh = sh, sw

        layout = []
        free_spaces = [(0, 0, sw, sh)]
        still_needed = []

        for piece in pieces:
            pos, dim = guillotine_split(free_spaces, piece[0], piece[1])
            if pos:
                layout.append((pos, dim))
            else:
                still_needed.append(piece)

        if layout:
            results.append(((sw, sh), layout))
            used_slabs.append((sw, sh))
        pieces = still_needed

        if not pieces:
            break

    return results, pieces, used_slabs


def nest_pieces_guillotine(required_pieces: List[Tuple[float, float]], available_slabs: List[Tuple[float, float]], use_smart_combo: bool = True):
    if not use_smart_combo:
        return try_combo(required_pieces, available_slabs)

    best_result = None
    min_wastage = float('inf')
    required_area = sum(w * h for w, h in required_pieces)

    for r in range(1, len(available_slabs) + 1):
        for combo in itertools.combinations(available_slabs, r):
            results, leftovers, used_slabs = try_combo(required_pieces, list(combo))
            if not leftovers:
                used_area = sum(w * h for w, h in used_slabs)
                wastage = used_area - required_area
                if wastage < min_wastage:
                    min_wastage = wastage
                    best_result = (results, leftovers, used_slabs)

    return best_result if best_result else ([], required_pieces, [])


def draw_slab_layout(slab: Tuple[float, float], layout: List[Tuple[Tuple[float, float], Tuple[float, float]]]):
    fig, ax = plt.subplots(figsize=(10, 4))
    sw, sh = slab
    ax.add_patch(patches.Rectangle((0, 0), sw, sh, edgecolor='black', facecolor='lightgray'))
    for ((x, y), (w, h)) in layout:
        ax.add_patch(patches.Rectangle((x, y), w, h, edgecolor='blue', facecolor='skyblue'))
        ax.text(x + w / 2, y + h / 2, f'{int(w)}x{int(h)}', ha='center', va='center', fontsize=8)
    ax.set_xlim(0, sw)
    ax.set_ylim(0, sh)
    ax.set_aspect('auto')
    ax.set_xlabel('LENGTH')
    ax.set_ylabel('WIDTH')
    ax.set_title(f'SLAB LAYOUT: {int(sw)} x {int(sh)} cm')
    st.pyplot(fig)


st.title("SLABBING")

req_input = st.text_area("Enter required slab sizes (in meters)",
                         "0.65 2.53\n0.64 2.28\n0.64 0.73\n0.73 2.28\n0.73 3.14\n0.73 0.73\n0.08 1.67\n0.08 2.53\n0.16 0.83\n0.15 0.82")
slab_input = st.text_area("Enter available slab sizes (in cm)", "160 320\n160 320")
smart_combo = st.checkbox("🔀 Enable Smart Combo (optimize slab selection)", value=True)

if st.button("START"):
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

        st.write(f"**Total Area:** {total_used_area / 10000:.2f} m²")
        st.write(f"**Wastage (Unused Area):** {(total_used_area - total_piece_area) / 10000:.2f} m²")

        if leftovers:
            st.warning("⚠️ These pieces did not fit in any slab:")
            for pw, ph in leftovers:
                st.text(f"{pw / 100:.2f} x {ph / 100:.2f} m")
    except Exception as e:
        st.error(f"Error: {str(e)}")

