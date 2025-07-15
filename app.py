import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Tuple
import itertools

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
    if not use_smart_combo:
        return try_combo(required_pieces, available_slabs)

    best_result = None
    min_wastage = float('inf')
    min_total_slab_area = float('inf')
    required_area = sum(w * h for _, w, h in required_pieces)

    # Sort slabs by area ascending, prefer smaller slabs first
    sorted_slabs = sorted(available_slabs, key=lambda x: (x[0] * x[1], x[0]))

    for r in range(1, len(sorted_slabs) + 1):
        for combo in itertools.combinations(sorted_slabs, r):
            combo = sorted(combo, key=lambda x: (x[0] * x[1], x[0]))  # prefer smaller slabs
            results, leftovers, used_slabs = try_combo(required_pieces, list(combo))
            if not leftovers:
                used_area = sum(w * h for w, h in used_slabs)
                wastage = used_area - required_area
                total_slab_area = sum(w * h for w, h in combo)
                if total_slab_area < min_total_slab_area or (total_slab_area == min_total_slab_area and wastage < min_wastage):
                    min_total_slab_area = total_slab_area
                    min_wastage = wastage
                    best_result = (results, leftovers, used_slabs)

    return best_result if best_result else ([], required_pieces, [])

def draw_slab_layout(slab: Tuple[float, float], layout: List[Tuple[str, Tuple[float, float], Tuple[float, float]]] ):
    fig, ax = plt.subplots(figsize=(12, 5))
    sw, sh = slab
    ax.add_patch(patches.Rectangle((0, 0), sw, sh, edgecolor='black', facecolor=slab_color))
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

with st.sidebar:
    smart_combo = st.checkbox("\U0001f500 Enable Smart Combo", value=True)

with st.expander("\U0001f4e5 Input Dimensions", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        req_input = st.text_area("Required pieces (in m)", "", placeholder="Input data here")
    with col2:
        slab_input = st.text_area("Available slabs (in cm)", "60 320\n60 320\n60 320\n70 320\n70 320\n70 320\n80 320\n80 320\n80 320\n90 320\n90 320\n90 320\n100 320\n100 320\n100 320\n160 320\n160 320\n160 320")

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

st.caption(f"\U0001f9ee Total Area Required: {required_area_preview:.2f} m²")
st.caption(f"\U0001f4e6 Total Number of Slabs: {piece_count}")

if st.button("\U0001f4d0 Nest Slabs"):
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
        st.subheader("\U0001f9e9 Slab Layouts")
        for slab, layout in results:
            st.markdown(f"**Slab:** {int(slab[0])} x {int(slab[1])} cm")
            draw_slab_layout(slab, layout)
            total_used_area += slab[0] * slab[1]
            for (_, _, (w, h)) in layout:
                total_piece_area += w * h

        st.markdown("---")
        st.subheader("\U0001f4ca Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Slabs Used", f"{len(used_slabs)}")
        with col2:
            st.metric("Total Slab Area", f"{total_used_area / 10000:.2f} m²")
        with col3:
            st.metric("Wastage Area", f"{(total_used_area - total_piece_area) / 10000:.2f} m²")

        if leftovers:
            st.warning("\u26a0\ufe0f These pieces did not fit in any slab:")
            st.code("\n".join([f"{name if name else 'Unnamed'}: {pw / 100:.2f} x {ph / 100:.2f} m" for name, pw, ph in leftovers]), language="text")
    except Exception as e:
        st.error(f"\u274c Error: {str(e)}")
