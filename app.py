import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from itertools import combinations_with_replacement
from collections import Counter, defaultdict
import random

# ───────────────────────────────────────────────
# Title and Instructions
# ───────────────────────────────────────────────
st.set_page_config(page_title="Slab Optimizer", layout="centered")
st.title("🧱 Slab Cutting Optimizer (cm)")
st.markdown("""
Enter your required pieces and available slab sizes in **centimeters**.
This app finds the best slab combination that minimizes cutting waste using 2D bin packing.
""")

# ───────────────────────────────────────────────
# 1. Required Pieces Input
# ───────────────────────────────────────────────
st.subheader("1️⃣ Required Pieces (width x length in cm)")
default_input = "65,253\n64,227\n64,73\n73,227\n73,314\n73,73\n8,166\n8,253\n16,83\n15,82"
user_input = st.text_area("✏️ One piece per line. Format: width,length", value=default_input)

pieces = []
for line in user_input.strip().splitlines():
    try:
        w, l = map(int, line.strip().split(','))
        pieces.append((w, l))
    except:
        st.error(f"❌ Invalid format in: {line}")

if pieces:
    total_area_cm2 = sum(w * l for w, l in pieces)
    st.info(f"📐 Total required area: {total_area_cm2 / 10000:.2f} m²")

# ───────────────────────────────────────────────
# 2. Slab Sizes Input
# ───────────────────────────────────────────────
st.subheader("2️⃣ Available Slab Sizes (width x length in cm)")
default_slabs = "60,320\n70,320\n80,320\n90,320\n100,320\n160,320"
user_slabs = st.text_area("✏️ One slab size per line. Format: width,length", value=default_slabs)

slab_sizes = []
for line in user_slabs.strip().splitlines():
    try:
        w, l = map(int, line.strip().split(','))
        slab_sizes.append((w, l))
    except:
        st.error(f"❌ Invalid slab format in: {line}")

# ───────────────────────────────────────────────
# 3. Settings and Run Button
# ───────────────────────────────────────────────
st.subheader("3️⃣ Optimization Settings")
max_slabs = st.slider("🔢 Max Number of Slabs to Combine", 1, 6, 3)

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
                continue  # not all pieces fit

            total_piece_area = sum(w * h for w, h in pieces)
            total_slab_area = sum(w * h for w, h in slab_combo)
            waste = total_slab_area - total_piece_area

            # Define ranking metrics
num_large_slabs = sum(1 for w, _ in slab_combo if w >= 100)
total_slab_area = sum(w * h for w, h in slab_combo)

# Compare current combo to best so far
is_better = False
if best_result is None:
    is_better = True
elif num_large_slabs < best_result["large_slabs"]:
    is_better = True
elif num_large_slabs == best_result["large_slabs"]:
    if total_slab_area < best_result["slab_area"]:
        is_better = True
    elif total_slab_area == best_result["slab_area"] and waste < min_waste:
        is_better = True

if is_better:
    min_waste = waste
    best_result = {
        "combo": slab_combo,
        "waste": waste / 10000,
        "large_slabs": num_large_slabs,
        "slab_area": total_slab_area
    }
    best_packer = packer


    # ───────────────────────────────────────────────
    # Show Result
    # ───────────────────────────────────────────────
    if best_result:
        st.success("✅ Optimization Successful!")
        summary = Counter(best_result["combo"])
        for (w, l), count in summary.items():
            st.write(f"- {count} slab(s) of size {w} x {l} cm")
        st.markdown(f"💡 **Estimated total waste:** `{best_result['waste']:.2f} m²`")

        # ───────────────────────────────────────────────
        # Draw Layouts
        # ───────────────────────────────────────────────
        st.subheader("📐 Slab Layout Visualizations")
        bins_rects = defaultdict(list)
        for rect in best_packer.rect_list():
            bin_index, x, y, w, h, rid = rect
            bins_rects[bin_index].append((x, y, w, h, rid))

        for bin_index, rects in bins_rects.items():
            sw, sh = best_result["combo"][bin_index]
            fig, ax = plt.subplots(figsize=(6, 8))
            ax.set_title(f"Slab {bin_index+1} - {sw} x {sh} cm")
            ax.add_patch(patches.Rectangle((0, 0), sw, sh, edgecolor='black', facecolor='none', lw=2))

            for (x, y, w, h, rid) in rects:
                color = [random.random() for _ in range(3)]
                ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=color, edgecolor='black', lw=1, alpha=0.6))
                ax.text(x + w/2, y + h/2, str(rid), ha='center', va='center', fontsize=8)

            ax.set_xlim(0, sw)
            ax.set_ylim(0, sh)
            ax.set_aspect('equal')
            plt.gca().invert_yaxis()
            st.pyplot(fig)
    else:
        st.error("❌ No valid slab combination found.")

