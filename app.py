import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from itertools import combinations_with_replacement, permutations
from collections import Counter, defaultdict
import random

# ───────────────────────────────────────────────
st.set_page_config(page_title="Slab Optimizer", layout="centered")
st.title("🧱 Slab Cutting Optimizer (cm)")

mode = st.radio("Select Material Type", ["Quartz (Standard Slabs)", "Granite (Custom Inventory Slabs)"])
st.write("🔍 Current mode:", mode)  # Debugging display

st.markdown("""
Enter your required pieces and slab sizes in **centimeters**.
This app finds the best slab combination that minimizes waste.
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
slab_sizes = []
slab_inventory = []

if mode == "Quartz (Standard Slabs)":
    st.subheader("2️⃣ Available Slab Sizes (toggle selection)")
    standard_slabs = [(60, 320), (70, 320), (80, 320), (90, 320), (100, 320), (160, 320)]

    all_options = [f"{w}x{l}" for w, l in standard_slabs]
    enable_all = st.checkbox("✅ Select/Deselect All", value=True)

    if enable_all:
        selected_slabs = st.multiselect("Select slab sizes:", all_options, default=all_options, key="slab_selector")
    else:
        selected_slabs = st.multiselect("Select slab sizes:", all_options, key="slab_selector")
    for slab in selected_slabs:
        w, l = map(int, slab.split("x"))
        slab_sizes.append((w, l))

    # The following block is no longer needed since selection is handled via multiselect
    # for line in user_slabs.strip().splitlines():
    #     try:
    #         w, l = map(int, line.strip().split(','))
    #         slab_sizes.append((w, l))
    #     except:
    #         st.error(f"❌ Invalid slab format in: {line}")
else:
    st.subheader("2️⃣ Granite Slab Inventory (custom sizes with quantity)")
    default_inventory = "124,312,1\n120,310,2\n116,298,1"
    user_inventory = st.text_area("✏️ Format: width,length,quantity", value=default_inventory)

    for line in user_inventory.strip().splitlines():
        try:
            w, l, qty = map(int, line.strip().split(','))
            for _ in range(qty):
                slab_inventory.append((w, l))
        except:
            st.error(f"❌ Invalid inventory format in: {line}")

# ───────────────────────────────────────────────
# 3. Optimization and Results
# ───────────────────────────────────────────────
if mode == "Quartz (Standard Slabs)":
    st.subheader("3️⃣ Optimization Settings")
    st.caption("ℹ️ You no longer need to adjust this — optimization will automatically use the smallest viable number of slabs.")
    max_slabs = len(pieces)  # Automatically try up to the number of pieces
else:
    max_slabs = len(slab_inventory)  # For granite, use all available slabs

if st.button("🚀 Run Optimization"):
    best_result = None
    best_packer = None
    min_waste = float('inf')

    if mode == "Quartz (Standard Slabs)":
        for num_slabs in range(1, max_slabs + 1):
            for slab_combo in combinations_with_replacement(slab_sizes, num_slabs):
                packer = newPacker(rotation=False)
                for i, (w_raw, h_raw) in enumerate(pieces):
                width, height = max(w_raw, h_raw), min(w_raw, h_raw)
                packer.add_rect(width, height, rid=i)
                for w_raw, h_raw in slab_combo:
                width, height = max(w_raw, h_raw), min(w_raw, h_raw)
                packer.add_bin(width, height)
                packer.pack()

                if len(packer.rect_list()) < len(pieces):
                    continue

                total_piece_area = sum(w * h for w, h in pieces)
                total_slab_area = sum(w * h for w, h in slab_combo)
                waste = total_slab_area - total_piece_area

                num_large_slabs = sum(1 for w, _ in slab_combo if w >= 100)
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
    else:
        for slab_combo in permutations(slab_inventory, len(slab_inventory)):
            packer = newPacker(rotation=True)
            for i, (w_raw, h_raw) in enumerate(pieces):
                h, w = min(w_raw, h_raw), max(w_raw, h_raw)
                packer.add_rect(w, h, rid=i)
            for w_raw, h_raw in slab_combo:
                h, w = min(w_raw, h_raw), max(w_raw, h_raw)
                packer.add_bin(w, h)
            packer.pack()

            if len(packer.rect_list()) < len(pieces):
                continue

            total_piece_area = sum(w * h for w, h in pieces)
            total_slab_area = sum(w * h for w, h in slab_combo)
            waste = total_slab_area - total_piece_area

            num_large_slabs = sum(1 for w, _ in slab_combo if w >= 100)
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

    if best_result:
        st.success("✅ Optimization Successful!")
        summary = Counter(best_result["combo"])
        for (w, l), count in summary.items():
            height, width = min(w, l), max(w, l)
            st.write(f"- {count} slab(s) of size {height}x{width} cm (height x width)")
        st.markdown(f"💡 **Estimated total waste:** `{best_result['waste']:.2f} m²`")
        st.markdown(f"📦 **Large slabs used (≥100 cm wide)**: `{best_result['large_slabs']}`")
        st.markdown(f"📏 **Total slab area used**: `{best_result['slab_area'] / 10000:.2f} m²`")

        # Visualize Slab Layouts
        st.subheader("📐 Slab Layout Visualizations")
        bins_rects = defaultdict(list)
        for rect in best_packer.rect_list():
            bin_index, x, y, w, h, rid = rect
            bins_rects[bin_index].append((x, y, w, h, rid))

        for bin_index, rects in bins_rects.items():
            w_raw, l_raw = best_result["combo"][bin_index]
            sh, sw = min(w_raw, l_raw), max(w_raw, l_raw)
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.set_title(f"Slab {bin_index+1} - {sh}x{sw} cm (height x width)")
            ax.add_patch(patches.Rectangle((0, 0), sw, sh, edgecolor='black', facecolor='none', lw=2))

            for (x, y, w, h, rid) in rects:
                color = [random.random() for _ in range(3)]
                ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=color, edgecolor='black', lw=1, alpha=0.6))
                label = f"{pieces[rid][1]}x{pieces[rid][0]}"
                ax.text(x + w/2, y + h/2, label, ha='center', va='center', fontsize=8)

            ax.set_xlim(0, sw)
            ax.set_ylim(0, sh)
            ax.set_aspect('equal')
            plt.gca().invert_yaxis()
            st.pyplot(fig)
    else:
        st.error("❌ No valid slab combination found.")








