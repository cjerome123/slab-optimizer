import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from itertools import combinations_with_replacement
from collections import defaultdict
import pandas as pd
import concurrent.futures

# ──────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────
st.set_page_config(
    page_title="SlabCut Optimizer",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        h1, h2, h3, h4, h5, h6, p, div, span {
            color: #000000 !important;
        }
        .stMetric {
            background-color: white !important;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 16px !important;
            color: #000000 !important;
        }
        .stButton>button {
            background-color: #0068c9;
            color: white;
            border-radius: 8px;
            font-weight: 500;
            padding: 12px 24px;
            margin-top: 16px;
            margin-bottom: 16px;
        }
        .stTextArea textarea {
            min-height: 150px;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────
QUARTZ_SIZES = [
    (60, 320), (70, 320), (80, 320),
    (90, 320), (100, 320), (160, 320)
]

# ──────────────────────────────────────────────────
# APP LAYOUT
# ──────────────────────────────────────────────────
st.title("SlabCut Optimizer")
st.markdown("<hr>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────
# MATERIAL SELECTION
# ──────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Material Settings")
    material_type = st.radio("Material Type", ["Quartz", "Granite"])

# ──────────────────────────────────────────────────
# INPUT SECTIONS
# ──────────────────────────────────────────────────
col1, col2 = st.columns(2)

# REQUIRED PIECES
with col1:
    st.subheader("Required Pieces (m)")
    default_pieces = """0.60,1.20
0.60,1.50
0.80,1.20
0.90,1.80
1.20,2.40"""
    pieces_input = st.text_area("Enter one piece per line (width,length):", value=default_pieces, height=200)

    pieces = []
    for line in pieces_input.strip().splitlines():
        try:
            parts = line.replace('\t', ' ').replace(',', ' ').split()
            w, l = map(float, parts[:2])
            pieces.append((w*100, l*100))  # Convert to cm
        except ValueError:
            st.error(f"Invalid format: {line}")

    if pieces:
        total_area = sum(w * l for w, l in pieces) / 10000
        st.metric("Total Required Area", f"{total_area:.2f} m²")

# AVAILABLE SLABS
with col2:
    st.subheader("Available Slabs")
    if material_type == "Quartz":
        st.caption("Standard quartz sizes (cm)")
        selected_sizes = st.multiselect(
            "Select slab sizes:",
            options=[f"{w}×{h}" for w, h in QUARTZ_SIZES],
            default=[f"{w}×{h}" for w, h in QUARTZ_SIZES[:3]],
            label_visibility="collapsed"
        )

        slab_sizes = []
        for size in selected_sizes:
            try:
                cleaned = size.replace(' ', '').replace('×','x')
                w, h = map(float, cleaned.split('x'))
                slab_sizes.append((w, h))
            except:
                st.error(f"Could not parse: {size}")
    else:
        tab1, tab2 = st.tabs(["Manual Input", "Import from Excel"])
        with tab1:
            default_slabs = """60,120
90,240
120,240
150,300"""
            slabs_input = st.text_area("Enter slab sizes (width,length cm):", value=default_slabs, height=150, label_visibility="collapsed")
            slab_sizes = []
            for line in slabs_input.strip().splitlines():
                try:
                    parts = line.replace('\t', ' ').replace(',', ' ').split()
                    w, l = map(float, parts[:2])
                    slab_sizes.append((w, l))
                except ValueError:
                    st.error(f"Invalid format: {line}")

        with tab2:
            uploaded_file = st.file_uploader("Upload spreadsheet", type=["xlsx", "csv"], help="Should contain width and length columns")
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.xlsx'):
                        df = pd.read_excel(uploaded_file)
                    else:
                        df = pd.read_csv(uploaded_file)

                    w_col = next((col for col in df.columns if 'width' in col.lower()), df.columns[0])
                    l_col = next((col for col in df.columns if 'length' in col.lower()), df.columns[1])

                    slab_sizes.extend([(w, h) for w, h in zip(df[w_col], df[l_col])])
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")

# ──────────────────────────────────────────────────
# OPTIMIZATION + FIXED VISUALIZATION
# ──────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
run_optimization = st.button("Generate Cutting Plan")

def evaluate_combination(slab_combo, pieces):
    packer = newPacker(rotation=False)
    for i, (w, h) in enumerate(pieces):
        packer.add_rect(w, h, rid=i)
    for w, h in slab_combo:
        packer.add_bin(w, h)
    packer.pack()

    if len(packer.rect_list()) < len(pieces):
        return None

    total_piece_area = sum(w * h for w, h in pieces)
    total_slab_area = sum(w * h for w, h in slab_combo)
    waste = total_slab_area - total_piece_area

    return {
        "combo": slab_combo,
        "waste": waste / 10000,
        "utilization": total_piece_area / total_slab_area * 100,
        "packer": packer
    }

if run_optimization and pieces and slab_sizes:
    best_result = None
    min_waste = float('inf')

    with st.spinner("Finding optimal arrangement..."):
        all_combos = []
        for num_slabs in range(1, 4):
            all_combos.extend(list(combinations_with_replacement(slab_sizes, num_slabs)))
        all_combos = all_combos[:300]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(evaluate_combination, combo, pieces) for combo in all_combos]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result and result["waste"] < min_waste:
                    min_waste = result["waste"]
                    best_result = result

    if best_result:
        st.success("Optimization Complete")
        st.markdown("<hr>", unsafe_allow_html=True)
        cols = st.columns(3)
        with cols[0]: st.metric("Slabs Needed", len(best_result["combo"]))
        with cols[1]: st.metric("Total Waste", f"{best_result['waste']:.2f} m²")
        with cols[2]: st.metric("Utilization", f"{best_result['utilization']:.1f}%")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("Cutting Layout (cm)")

        bins_rects = defaultdict(list)
        for rect in best_result["packer"].rect_list():
            bin_index, x, y, w, h, rid = rect
            bins_rects[bin_index].append((x, y, w, h, rid))

        cols = st.columns(len(bins_rects))
        used_ids = set()

        for bin_index, rects in bins_rects.items():
            slab_w, slab_h = best_result["combo"][bin_index]

            # Rotate slab to always be horizontal
            if slab_h > slab_w:
                slab_w, slab_h = slab_h, slab_w
                rotate_slab = True
            else:
                rotate_slab = False

            fig, ax = plt.subplots(figsize=(8, 4))
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')

            ax.add_patch(patches.Rectangle((0, 0), slab_w, slab_h, edgecolor='#0068c9', facecolor='#f0f7ff', lw=2))

            used_area = 0
            for i, (x, y, w, h, rid) in enumerate(rects):
                used_ids.add(rid)

                if rotate_slab:
                    x, y, w, h = y, x, h, w

                ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=plt.cm.tab20(i % 20), edgecolor='black', lw=1, alpha=0.9))
                ax.text(x + w/2, y + h/2, f"{w}×{h}", ha='center', va='center', fontsize=8, color='black')
                used_area += w * h

            slab_area = slab_w * slab_h
            waste_area = (slab_area - used_area) / 10000
            waste_pct = (waste_area / (slab_area / 10000)) * 100

            ax.set_xlim(0, slab_w)
            ax.set_ylim(0, slab_h)
            ax.set_aspect('equal')
            ax.axis('off')
            plt.gca().invert_yaxis()

            with cols[bin_index]:
                st.pyplot(fig)
                st.caption(f"""
                {slab_w}×{slab_h} cm  
                Waste: {waste_area:.2f} m²  
                ({waste_pct:.1f}%)
                """)

        all_ids = set(range(len(pieces)))
        unfitted_ids = list(all_ids - used_ids)
        if unfitted_ids:
            st.subheader("Unfitted Pieces")
            unfitted_df = pd.DataFrame([pieces[rid] for rid in unfitted_ids], columns=["Width (cm)", "Height (cm)"])
            st.dataframe(unfitted_df)
    else:
        st.error("No valid solution found")
elif run_optimization:
    if not pieces:
        st.error("Please enter required pieces")
    if not slab_sizes:
        st.error("Please enter available slab sizes")





















