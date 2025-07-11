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

# Minimalist style
st.markdown("""
    <style>
        .reportview-container {
            background: #f8f9fa;
        }
        .sidebar .sidebar-content {
            background: #ffffff;
            padding: 1rem;
        }
        hr {
            margin: 1rem 0;
            border: 0;
            border-top: 1px solid #e9ecef;
        }
        .stButton>button {
            background-color: #0068c9;
            color: white;
            border-radius: 4px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .stButton>button:hover {
            background-color: #0052a3;
        }
        .stMetric {
            padding: 0.5rem;
            border-radius: 4px;
            background: #ffffff;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 12px;
            border-radius: 4px;
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

    # Process pieces (convert meters to cm)
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
        st.markdown(f"**Total required area:** {total_area:.2f} m²")

# AVAILABLE SLABS (dynamic input based on material)
with col2:
    st.subheader("Available Slabs")
    
    if material_type == "Quartz":
        st.caption("Standard quartz slab sizes:")
        selected_formats = st.multiselect(
            "Select slab sizes to use:",
            options=[f"{w} × {h} cm" for w, h in QUARTZ_SIZES],
            default=[f"{w} × {h} cm" for w, h in QUARTZ_SIZES[:4]],
            help="Standard engineered quartz slab sizes"
        )
        
        # Parse selected sizes
        slab_sizes = []
        for size in selected_formats:
            try:
                # Handle various input formats
                cleaned = size.lower().replace('cm','').replace(' ','').replace('x','×')
                w, h = map(float, cleaned.split('×'))
                slab_sizes.append((w, h))
            except Exception:
                st.error(f"Could not parse size: {size}")
                
    else:  # Granite
        tab1, tab2 = st.tabs(["Manual Input", "Import from Excel"])
        
        with tab1:
            default_slabs = """60,120
90,240
120,240
150,300"""
            
            slabs_input = st.text_area(
                "Enter granite slab sizes (width,length cm):",
                value=default_slabs,
                height=150,
                help="One slab size per line"
            )
            
            # Process slabs from text
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
                "Upload slab sizes",
                type=["xlsx", "csv"],
                help="Excel/CSV with width and length columns (cm)"
            )
            
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.xlsx'):
                        df = pd.read_excel(uploaded_file)
                    else:
                        df = pd.read_csv(uploaded_file)
                    
                    # Flexible column name matching
                    w_col = next((col for col in df.columns if 'width' in col.lower()), df.columns[0])
                    l_col = next((col for col in df.columns if 'length' in col.lower()), df.columns[1])
                    
                    slab_sizes.extend([(w,h) for w,h in zip(df[w_col], df[l_col])])
                    st.success(f"Imported {len(df)} slab sizes")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")

    # Display selected sizes
    if slab_sizes:
        st.markdown("**Selected slab sizes:**")
        for w, h in slab_sizes[:5]:  # Show first 5 to save space
            st.write(f"- {int(w)} × {int(h)} cm")
        if len(slab_sizes) > 5:
            st.write(f"- ...and {len(slab_sizes)-5} more")

# ──────────────────────────────────────────────────
# OPTIMIZATION LOGIC
# ──────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
run_optimization = st.button("Generate Optimal Cutting Plan")

if run_optimization and pieces and slab_sizes:
    best_result = None
    best_packer = None
    min_waste = float('inf')

    with st.spinner("Calculating optimal slab combination..."):
        for num_slabs in range(1, 4):  # Try 1-3 slab combinations
            for slab_combo in combinations_with_replacement(slab_sizes, num_slabs):
                packer = newPacker(rotation=False)
                
                # Add all pieces
                for i, (w, h) in enumerate(pieces):
                    packer.add_rect(w, h, rid=i)
                
                # Add slabs
                for w, h in slab_combo:
                    packer.add_bin(w, h)
                
                packer.pack()

                if len(packer.rect_list()) < len(pieces):
                    continue  # Skip incomplete solutions

                total_piece_area = sum(w * h for w, h in pieces)
                total_slab_area = sum(w * h for w, h in slab_combo)
                waste = total_slab_area - total_piece_area

                if waste < min_waste:
                    min_waste = waste
                    best_result = {
                        "combo": slab_combo,
                        "waste": waste / 10000,
                        "slab_area": total_slab_area / 10000,
                        "utilization": total_piece_area / total_slab_area * 100,
                        "packer": packer
                    }

    if best_result:
        st.success("Optimization complete")
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # RESULTS SUMMARY
        st.subheader(f"Optimal {material_type} Solution")
        
        # Detailed slab info
        cols = st.columns(3)
        with cols[0]:
            st.metric("Slabs Required", len(best_result["combo"]))
        with cols[1]:
            st.metric("Total Waste", f"{best_result['waste']:.2f} m²")
        with cols[2]:
            st.metric("Utilization Rate", f"{best_result['utilization']:.1f}%")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # VISUALIZATION
        st.subheader("Cutting Layout (cm)")
        bins_rects = defaultdict(list)
        for rect in best_result["packer"].rect_list():
            bin_index, x, y, w, h, rid = rect
            bins_rects[bin_index].append((x, y, w, h, rid))

        # Horizontal slab display
        cols = st.columns(len(bins_rects))
        
        for bin_index, rects in bins_rects.items():
            slab_w, slab_h = best_result["combo"][bin_index]
            
            fig, ax = plt.subplots(figsize=(6, 3))
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')
            
            # Draw slab
            slab_rect = patches.Rectangle(
                (0, 0), slab_w, slab_h,
                edgecolor='#0068c9', facecolor='#f0f7ff', lw=1.5
            )
            ax.add_patch(slab_rect)
            
            # Draw pieces
            for i, (x, y, w, h, _) in enumerate(rects):
                piece_rect = patches.Rectangle(
                    (x, y), w, h,
                    facecolor=plt.cm.tab20(i % 20),
                    edgecolor='#333', alpha=0.9, lw=0.5
                )
                ax.add_patch(piece_rect)
                ax.text(
                    x + w/2, y + h/2, f"{w}×{h}", 
                    ha='center', va='center', fontsize=8
                )
            
            ax.set_xlim(0, slab_w)
            ax.set_ylim(0, slab_h)
            ax.set_aspect('equal')
            ax.axis('off')
            plt.gca().invert_yaxis()
            
            with cols[bin_index]:
                st.pyplot(fig)
                used_area = sum(w*h for _,_,w,h,_ in rects)
                slab_waste_m2 = (slab_w * slab_h - used_area) / 10000
                util_percent = used_area / (slab_w * slab_h) * 100
                st.caption(f"""
                **Slab {bin_index+1}:** {slab_w}×{slab_h} cm  
                Waste: {slab_waste_m2:.2f} m²  
                Utilized: {util_percent:.1f}%
                """)

    else:
        st.error("No valid combination found with current slabs")

elif run_optimization:
    if not pieces:
        st.error("Please enter required pieces first")
    if not slab_sizes:
        st.error("Please enter available slab sizes")

















