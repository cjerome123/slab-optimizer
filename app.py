import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from itertools import combinations_with_replacement
from collections import defaultdict
import pandas as pd

# ──────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────
st.set_page_config(
    page_title="SlabCut Optimizer",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Improved minimal styling with dark text visibility
st.markdown("""
    <style>
        /* Dark text on light background */
        h1, h2, h3, h4, h5, h6, p, div, span {
            color: #333333 !important;
        }
        
        /* Clean card styling */
        .stMetric {
            background-color: white !important;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 16px !important;
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #0068c9;
            color: white;
            border-radius: 8px;
            font-weight: 500;
            padding: 12px 24px;
            margin-top: 16px;
            margin-bottom: 16px;
        }
        
        /* Input styling */
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

# REQUIRED PIECES (meters input)
with col1:
    st.subheader("Required Pieces (m)")
    default_pieces = """0.60,1.20
0.60,1.50
0.80,1.20
0.90,1.80
1.20,2.40"""
    
    pieces_input = st.text_area(
        "Enter one piece per line (width,length):",
        value=default_pieces,
        height=200
    )

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
                
    else:  # Granite
        tab1, tab2 = st.tabs(["Manual Input", "Import from Excel"])
        
        with tab1:
            default_slabs = """60,120
90,240
120,240
150,300"""
            
            slabs_input = st.text_area(
                "Enter slab sizes (width,length cm):",
                value=default_slabs,
                height=150,
                label_visibility="collapsed"
            )
            
            slab_sizes = []
            for line in slabs_input.strip().splitlines():
                try:
                    parts = line.replace('\t', ' ').replace(',', ' ').split()
                    w, l = map(float, parts[:2])
                    slab_sizes.append((w, l))
                except ValueError:
                    st.error(f"Invalid format: {line}")
        
        with tab2:
            uploaded_file = st.file_uploader(
                "Upload spreadsheet",
                type=["xlsx", "csv"],
                help="Should contain width and length columns"
            )
            
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.xlsx'):
                        df = pd.read_excel(uploaded_file)
                    else:
                        df = pd.read_csv(uploaded_file)
                    
                    w_col = next((col for col in df.columns if 'width' in col.lower()), df.columns[0])
                    l_col = next((col for col in df.columns if 'length' in col.lower()), df.columns[1])
                    
                    slab_sizes.extend([(w,h) for w,h in zip(df[w_col], df[l_col])])
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")

# ──────────────────────────────────────────────────
# OPTIMIZATION LOGIC WITH HORIZONTAL LAYOUT
# ──────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
run_optimization = st.button("Generate Cutting Plan")

if run_optimization and pieces and slab_sizes:
    best_result = None
    best_packer = None
    min_waste = float('inf')

    with st.spinner("Finding optimal arrangement..."):
        for num_slabs in range(1, 4):
            for slab_combo in combinations_with_replacement(slab_sizes, num_slabs):
                packer = newPacker(rotation=False)
                for i, (w, h) in enumerate(pieces):
                    packer.add_rect(w, h, rid=i)
                for w, h in slab_combo:
                    packer.add_bin(w, h)
                packer.pack()

                if len(packer.rect_list()) < len(pieces):
                    continue

                total_piece_area = sum(w * h for w, h in pieces)
                total_slab_area = sum(w * h for w, h in slab_combo)
                waste = total_slab_area - total_piece_area

                if waste < min_waste:
                    min_waste = waste
                    best_result = {
                        "combo": slab_combo,
                        "waste": waste / 10000,
                        "utilization": total_piece_area / total_slab_area * 100,
                        "packer": packer
                    }

    if best_result:
        st.success("Optimization Complete")
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # RESULTS SUMMARY
        cols = st.columns(3)
        with cols[0]:
            st.metric("Slabs Needed", len(best_result["combo"]))
        with cols[1]:
            st.metric("Total Waste", f"{best_result['waste']:.2f} m²")
        with cols[2]:
            st.metric("Utilization", f"{best_result['utilization']:.1f}%")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # HORIZONTAL VISUALIZATION
        st.subheader("Cutting Layout (cm)")
        bins_rects = defaultdict(list)
        for rect in best_result["packer"].rect_list():
            bin_index, x, y, w, h, rid = rect
            bins_rects[bin_index].append((x, y, w, h, rid))

        cols = st.columns(len(bins_rects))
        
        for bin_index, rects in bins_rects.items():
            slab_w, slab_h = best_result["combo"][bin_index]
            
            # Determine orientation (always display width >= height)
            display_w = max(slab_w, slab_h)
            display_h = min(slab_w, slab_h)
            rotated = slab_h > slab_w
            
            fig, ax = plt.subplots(figsize=(8, 4))
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')
            
            # Draw slab (always horizontal)
            ax.add_patch(patches.Rectangle(
                (0, 0), display_w, display_h,
                edgecolor='#0068c9', facecolor='#f0f7ff', lw=2
            ))
            
            # Draw pieces
            for i, (x, y, w, h, _) in enumerate(rects):
                if rotated:
                    # Rotate piece coordinates if slab was rotated
                    draw_x = y
                    draw_y = slab_w - x - w
                    draw_w = h
                    draw_h = w
                else:
                    draw_x = x
                    draw_y = y
                    draw_w = w
                    draw_h = h
                
                ax.add_patch(patches.Rectangle(
                    (draw_x, draw_y), draw_w, draw_h,
                    facecolor=plt.cm.tab20(i % 20),
                    edgecolor='#333', lw=1, alpha=0.9
                ))
                ax.text(
                    draw_x + draw_w/2, draw_y + draw_h/2,
                    f"{w}×{h}" if not rotated else f"{h}×{w}",
                    ha='center', va='center', fontsize=8
                )
            
            ax.set_xlim(0, display_w)
            ax.set_ylim(0, display_h)
            ax.set_aspect('equal')
            ax.axis('off')
            plt.gca().invert_yaxis()
            
            with cols[bin_index]:
                st.pyplot(fig)
                used_area = sum(w*h for _,_,w,h,_ in rects)
                slab_waste = (slab_w * slab_h - used_area) / 10000
                st.caption(f"""
                {slab_w}×{slab_h} cm  
                Waste: {slab_waste:.2f} m²  
                ({slab_waste/(slab_w*slab_h/10000)*100:.1f}%)
                """)

    else:
        st.error("No valid solution found")
elif run_optimization:
    if not pieces:
        st.error("Please enter required pieces")
    if not slab_sizes:
        st.error("Please enter available slab sizes")



















