import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from itertools import combinations_with_replacement
from collections import Counter, defaultdict
import random

st.title("📏 Slab Cutting Optimizer")
st.markdown("This app finds the best combination of slabs to cut all required pieces with minimal waste.")

# User inputs
st.subheader("1. Enter Required Pieces (width x length in meters)")
default_input = "0.65,2.53\n0.64,2.27\n0.64,0.73\n0.73,2.27\n0.73,3.14\n0.73,0.73\n0.08,1.66\n0.08,2.53\n0.16,0.83\n0.15,0.82"
user_input = st.text_area("Each line = one piece. Separate width & length with a comma.", value=default_input)

pieces = []
for line in user_input.strip().splitlines():
    try:
        w, l = map(float, line.strip().split(','))
        pieces.append((int(w * 100), int(l * 100)))  # convert to cm
    except:
        st.error(f"Invalid format: {line}")

# Slab sizes (you can allow custom input later)
slab_sizes = [
    (60, 320),
    (70, 320),
    (80, 320),
    (90, 320),
    (100, 320),
    (160, 320)
]

st.subheader("2. Optimization Settings")
max_slabs = st.slider("Maximum Number of Slabs to Combine", 1, 6, 3)

if st.button("🚀 Run Optimization"):
    best_result = None
    best_packer = None
    min_waste = float('inf')

    for num_slabs in range(1, max_slabs + 1):
        for slab_combo in combinations_with_replacement(slab_sizes, num_slabs):
            packer = newPacker(rotation=True)
            for i, (w, h) in enumerate(pieces):
                packer.add_rect(w, h, rid=i)
            for w, h in slab_combo:
                packer.add_bin(w, h)
            packer.pack()

            if len(packer.rect_list()) < len(pieces):
                continue

            total_area = sum(w * h for w, h in pieces)
            slab_area = sum(w * h for w, h in slab_combo)
            waste = slab_area - total_area

            if waste < min_waste:
                min_waste = waste
                best_result = {
                    "combo": slab_combo,
                    "waste": waste / 10000
                }
                best_packer = packer

    if best_result:
        st.success("✅ Optimization successful!")
        summary = Counter(best_result["combo"])
        for (w, l), count in summary.items():
            st.write(f"- {count} slab(s) of size {w/100:.2f} x {l/100:.2f} meters")
        st.write(f"💡 Estimated total waste: {best_result['waste']:.2f} m²")

        # Draw layout
        st.subheader("📐 Slab Layouts")
        bins_rects = defaultdict(list)
        for rect in best_packer.rect_list():
            bin_index, x, y, w, h, rid = rect
            bins_rects[bin_index].append((x, y, w, h, rid))

        for bin_index, rects in bins_rects.items():
            slab_size = best_result["combo"][bin_index]
            sw, sh = slab_size
            fig, ax = plt.subplots(figsize=(5, 6))
            ax.add_patch(patches.Rectangle((0, 0), sw, sh, edgecolor='black', facecolor='none', lw=2))
            for (x, y, w, h, rid) in rects:
                color = [random.random() for _ in range(3)]
                ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=color, edgecolor='black', lw=1))
                ax.text(x + w/2, y + h/2, str(rid), ha='center', va='center', fontsize=8)
            ax.set_xlim(0, sw)
            ax.set_ylim(0, sh)
            ax.set_aspect('equal')
            plt.gca().invert_yaxis()
            st.pyplot(fig)
    else:
        st.error("❌ No valid slab combination found.")
