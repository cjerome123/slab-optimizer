import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from itertools import combinations_with_replacement
from collections import Counter, defaultdict
import random

# ──────────────────────────────────────────────────
st.set_page_config(page_title="Slab Optimizer", layout="wide", initial_sidebar_state="expanded")
st.title("🧥 Slab Cutting Optimizer")
st.sidebar.title("⚙️ Settings")

slab_mode = st.sidebar.radio("Slab Type", ["Quartz", "Granite"])
dark_mode = st.sidebar.checkbox("🌙 Dark Mode", value=False)
if dark_mode:
    st.markdown("""
        <style>
            html, body, [class*="css"]  {
                background-color: #0e1117;
                color: #fafafa;
            }
            .stButton>button {
                background-color: #262730;
                color: white;
            }
        </style>
    """, unsafe_allow_html=True)

mode = slab_mode
st.caption(f"Mode: {mode}")

st.markdown("""
Enter your required pieces and slab sizes in **centimeters**.
This app finds the best slab combination that minimizes waste.
""")

# ──────────────────────────────────────────────────
# 1. Required Pieces Input
# ──────────────────────────────────────────────────
st.subheader("Required Pieces")
default_input = "65,253\n64,227\n64,73\n73,227\n73,314\n73,73\n8,166\n8,253\n16,83\n15,82"
user_input = st.text_area("✏️ One piece per line. Format: width,length (in cm)", value=default_input, height=150, label_visibility="visible")

pieces = []
for line in user_input.strip().splitlines():
    try:
        parts = line.replace('\t', ' ').replace(',', ' ').split()
        w, l = map(float, parts[:2])
        pieces.append((w, l))
    except:
        st.error(f"❌ Invalid format in: {line}")

if pieces:
    total_area_cm2 = sum(w * l for w, l in pieces)
    st.info(f"📀 Total required area: {total_area_cm2 / 10000:.2f} m²")

# ──────────────────────────────────────────────────
# 2. Slab Sizes Input
# ──────────────────────────────────────────────────
st.subheader("Available Slab Sizes")
default_slabs = "60,320\n70,320\n80,320\n90,320\n100,320\n160,320"
slab_input = st.text_area("📐 Slab sizes (one per line, in cm)", value=default_slabs, height=120)

slab_sizes = []
for line in slab_input.strip().splitlines():
    try:
        parts = line.replace('\t', ' ').replace(',', ' ').split()
        w, l = map(float, parts[:2])
        slab_sizes.append((w, l))
    except:
        st.error(f"❌ Invalid format in: {line}")

# ──────────────────────────────────────────────────
# Optimization and Layout Drawing
# ──────────────────────────────────────────────────
best_result = None
best_packer = None
min_waste = float('inf')

if st.button("🚀 Optimize"):
    for num_slabs in range(1, 4):  # Try combinations with 1 to 3 slabs
        for slab_combo in combinations_with_replacement(slab_sizes, num_slabs):
            packer = newPacker(rotation=False)
            for i, (w, h) in enumerate(pieces):
                packer.add_rect(w, h, rid=i)
            for w, h in slab_combo:
                packer.add_bin(w, h)
            packer.pack()

            if len(packer.rect_list()) < len(pieces):
                continue  # not all pieces fit

            total_piece_area = sum(w * h for w, h in pieces)
            total_slab_area = sum(w * h for w, h in slab_combo)
            waste = total_slab_area - total_piece_area

            if waste < min_waste:
                min_waste = waste
                best_result = {
                    "combo": slab_combo,
                    "waste": waste / 10000,
                    "slab_area": total_slab_area
                }
                best_packer = packer

    if best_result:
        st.success("✅ Optimization Successful!")
        st.markdown(f"**Estimated total waste:** `{best_result['waste']:.2f} m²`")

        # Slab Layout Visualizations
        st.subheader("📐 Slab Layout Visualizations")
        bins_rects = defaultdict(list)
        for rect in best_packer.rect_list():
            bin_index, x, y, w, h, rid = rect
            bins_rects[bin_index].append((x, y, w, h, rid))

        for bin_index, rects in bins_rects.items():
            sw, sh = best_result["combo"][bin_index]
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.add_patch(patches.Rectangle((0, 0), sw, sh, edgecolor='black', facecolor='none', lw=2))

            for (x, y, w, h, rid) in rects:
                color = [random.random() for _ in range(3)]
                ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=color, edgecolor='black', lw=1, alpha=0.6))
                label = f"{int(h)}x{int(w)}"
                ax.text(x + w / 2, y + h / 2, label, ha='center', va='center', fontsize=8, color='black')

            ax.set_xlim(0, sw)
            ax.set_ylim(0, sh)
            ax.set_aspect('equal')
            ax.axis('off')
            plt.gca().invert_yaxis()
            st.pyplot(fig)
    else:
        st.error("❌ No valid slab combination found.")











