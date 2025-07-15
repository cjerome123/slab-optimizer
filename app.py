import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations

# -----------------------------
# Theme Color Configuration
# -----------------------------

st.set_page_config(layout="wide")

# Light mode only settings
primary_bg = "#ffffff"
font_color = "#000000"
slab_color = "#e28a8b"
piece_color = "#e3dec3"
input_bg = "#f9f9f9"

st.markdown(f"""
<style>
    body {{
        background-color: {primary_bg};
        color: {font_color};
    }}
    .stTextArea textarea {{
        background-color: {input_bg};
        color: {font_color};
        caret-color: {font_color};
        font-family: monospace;
    }}
    .stButton>button {{
        background-color: #007bff;
        color: white;
        font-weight: bold;
        border-radius: 8px;
    }}
</style>
""", unsafe_allow_html=True)

st.title("SLAB OPTIMIZATION")

def can_fit_any_rotation(piece: Tuple[float, float], space: Tuple[float, float]) -> Tuple[bool, Tuple[float, float]]:
    pw, ph = piece
    sw, sh = space
    for orientation in [(pw, ph), (ph, pw)]:
        if orientation[0] <= sw and orientation[1] <= sh:
            return True, orientation
    return False, (0, 0)

def guillotine_split(free_spaces: List[Tuple[float, float, float, float]],
                     pw: float, ph: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
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

def try_combo(required_pieces: List[Tuple[str, float, float]], combo: List[Tuple[float, float]]):
    results = []
    used_slabs = []
    pieces = sorted(required_pieces, key=lambda x: x[1] * x[2], reverse=True)

    for slab in combo:
        sw, sh = slab
        if sh > sw:
            sw, sh = sh, sw

        layout = []
        free_spaces = [(0, 0, sw, sh)]
        still_needed = []

        for name, pw, ph in pieces:
            pos, dim = guillotine_split(free_spaces, pw, ph)
            if pos:
                layout.append((name, pos, dim))
            else:
                still_needed.append((name, pw, ph))

        if layout:
            results.append(((sw, sh), layout))
            used_slabs.append((sw, sh))
        pieces = still_needed

        if not pieces:
            break

    return results, pieces, used_slabs

def nest_pieces_guillotine(required_pieces: List[Tuple[str, float, float]], available_slabs: List[Tuple[float, float]], use_smart_combo: bool = True):
    def sort_slabs(slabs):
        return sorted(slabs, key=lambda x: x[0] * x[1])  # prioritize smaller slabs

    def try_combo_wrapped(combo):
        combo_list = list(combo) * 5  # simulate reuse
        results, leftovers, used = try_combo(required_pieces, combo_list)
        if not leftovers:
            used_area = sum(w * h for w, h in used)
            wastage = used_area - required_area
            return wastage, (results, leftovers, used)
        return float('inf'), None

    required_area = sum(w * h for _, w, h in required_pieces)
    sorted_slabs = sort_slabs(available_slabs)

    if not use_smart_combo:
        return try_combo(required_pieces, available_slabs)

    best_result = None
    min_wastage = float('inf')

    # Smart Combo Phase — parallel combo filtering and evaluation
    with ThreadPoolExecutor() as executor:
        futures = []
        for r in range(1, min(len(sorted_slabs), 5) + 1):
            for combo in combinations(sorted_slabs, r):
                slab_area = sum(w * h for w, h in combo)
                if slab_area < required_area:
                    continue  # filter inefficient combos
                futures.append(executor.submit(try_combo_wrapped, combo))

        for future in as_completed(futures):
            wastage, result = future.result()
            if result and wastage < min_wastage:
                min_wastage = wastage
                best_result = result

    return best_result if best_result else ([], required_pieces, [])
    

def draw_slab_layout(slab: Tuple[float, float], layout: List[Tuple[str, Tuple[float, float], Tuple[float, float]]] ):
    fig, ax = plt.subplots(figsize=(12, 5))
    sw, sh = slab
    ax.add_patch(patches.Rectangle((0, 0), sw, sh, edgecolor='black', facecolor=slab_color, linewidth=0.5, antialiased=True))
    for idx, (label, (x, y), (w, h)) in enumerate(layout):
        label = label.strip()
        label_text = f"{int(min(w,h))}x{int(max(w,h))}" if label == "" else f"{label}\n{int(min(w,h))}x{int(max(w,h))}"
        ax.add_patch(patches.Rectangle((x, y), w, h, edgecolor='black', facecolor=piece_color))
        ax.text(x + w / 2, y + h / 2, label_text,
                ha='center', va='center', fontsize=10, color='black')
    ax.set_xlim(0, sw)
    ax.set_ylim(0, sh)
    ax.set_aspect('auto')
    ax.axis('off')
    st.pyplot(fig)

with st.expander("📅 Input Dimensions", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        req_input = st.text_area("Required pieces (in m)", "", placeholder="Input data here")
    with col2:
        slab_input = st.text_area("Available slabs (in cm)", "60 320\n70 320\n80 320\n90 320\n100 320\n160 320")

required_area_preview = 0
piece_count = 0
for line in req_input.strip().splitlines():
    parts = line.strip().split()
    if len(parts) == 3:
        _, w, h = parts[0], float(parts[1]), float(parts[2])
    elif len(parts) == 2:
        w, h = float(parts[0]), float(parts[1])
    else:
        continue
    required_area_preview += w * h
    piece_count += 1

with st.sidebar:
    st.markdown("### 📊 Summary")
    smart_combo = st.checkbox("💡 Smart Combo", value=True)
    st.metric("Total Area Required", f"{required_area_preview:.2f} m²")
    st.metric("Number of Required Slabs", piece_count)

if st.button("⚙️ Nest Slabs"):
    try:
        required = []
        for line in req_input.strip().splitlines():
            parts = line.strip().split()
            if len(parts) == 3:
                name, w, h = parts[0], float(parts[1]), float(parts[2])
            elif len(parts) == 2:
                name, w, h = "", float(parts[0]), float(parts[1])
            else:
                continue
            required.append((name, w * 100, h * 100))

        available = []
        for line in slab_input.strip().splitlines():
            w, h = map(float, line.strip().split())
            available.append((w, h))

        results, leftovers, used_slabs = nest_pieces_guillotine(required, available, use_smart_combo=smart_combo)

        total_used_area = 0
        total_piece_area = 0

        st.markdown("---")
        st.subheader("📏 Slab Layouts")
        for i, (slab, layout) in enumerate(results):
            label = f"{int(slab[0])} x {int(slab[1])} cm"
            with st.expander(f"Slab {i+1}: {label}", expanded=False):
                draw_slab_layout(slab, layout)
            total_used_area += slab[0] * slab[1]
            for (_, _, (w, h)) in layout:
                total_piece_area += w * h

        with st.sidebar:
            st.markdown("---")
            st.markdown("### 📊 Results")
            st.markdown(f"**Slabs Used:** {len(used_slabs)}")
            st.markdown(f"**Total Slab Area:** {total_used_area / 10000:.2f} m²")
            st.markdown(f"**Wastage Area:** {(total_used_area - total_piece_area) / 10000:.2f} m²")


        if leftovers:
            st.warning("⚠️ These pieces did not fit in any slab:")
            st.code("\n".join([f"{name if name else 'Unnamed'}: {pw / 100:.2f} x {ph / 100:.2f} m" for name, pw, ph in leftovers]), language="text")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
