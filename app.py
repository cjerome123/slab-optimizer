import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from itertools import combinations_with_replacement
from collections import defaultdict
import pandas as pd
from io import StringIO

# ──────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Slab Optimizer Pro",
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
# APP LAYOUT
# ──────────────────────────────────────────────────
st.title("Slab Cutting Optimizer")
st.markdown("<hr>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────
# SIDEBAR SETTINGS
# ──────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Settings")
    material_type = st.radio("Material Type", ["Quartz", "Granite", "Porcelain"])
    
# ──────────────────────────────────────────────────
# INPUT SECTIONS
# ──────────────────────────────────────────────────
col1, col2 = st.columns(2)

# REQUIRED PIECES (meters input)
with col1:
    st.subheader("Required Pieces (m)")
    default_pieces = """0.65,2.53
0.64,2.27
0.64,0.73
0.73,2.27
0.73,3.14
0.73,0.73"""
    
    pieces_input = st.text_area(
        "Enter one piece per line (width,length):",
        value=default_pieces,
        height=200
    )

    # Process pieces
    pieces = []
    for line in pieces_input.strip().splitlines():
        try:
            parts = line.replace('\t', ' ').replace(',', ' ').split()
            w, l = map(float, parts[:2])
            pieces.append((w*100, l*100))  # Convert meters to cm
        except ValueError:
            st.error(f"Invalid format: {line}")

    if pieces:
        total_area = sum(w * l for w, l in pieces) / 10000
        st.markdown(f"**Total required:** {total_area:.2f} m²")

# AVAILABLE SLABS (dynamic input based on material)
with col2:
    st.subheader("Available Slabs (cm)")
    
    if material_type == "Quartz":
        st.caption("Standard quartz slab sizes:")
        quartz_sizes = [
            (60, 320), (70, 320), (80, 320),
            (90, 320), (100, 320), (160, 320)
        ]
        
        selected_sizes = st.multiselect(
            "Select slab sizes:",
            options=[f"{w}×{h} cm" for w, h in quartz_sizes],
            default=[f"{w}×{h} cm" for w, h in quartz_sizes[:4]],
            help="Standard quartz slab sizes"
        )
        
        # Convert selected strings back to dimensions
        slab_sizes = []
        for size in selected_sizes:
            w, h = map(float, size.split('×'))  # Split "60×320" into (60, 320)
            slab_sizes.append((w, h))
            
    else:  # Granite or Porcelain
        tab1, tab2 = st.tabs(["Manual Input", "Import from Excel"])
        
        with tab1:
            default_slabs = """60,120
90,240
120,240
150,300"""
            
            slabs_input = st.text_area(
                f"Enter {material_type.lower()} slab sizes (width,length cm):",
                value=default_slabs,
                height=150
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
                f"Upload {material_type.lower()} slab sizes",
                type=["xlsx", "csv", "txt"],
                help="File should have width and length columns (in cm)"
            )
            
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.xlsx'):
                        df = pd.read_excel(uploaded_file)
                    else:
                        df = pd.read_csv(uploaded_file)
                    
                    # Try to find width/length columns (case insensitive)
                    w_col = next((col for col in df.columns if 'width' in col.lower()), None)
                    l_col = next((col for col in df.columns if 'length' in col.lower()), None)
                    
                    if w_col and l_col:
                        slab_sizes.extend(zip(df[w_col], df[l_col]))
                        st.success(f"Successfully imported {len(df)} slab sizes")
                    else:
                        st.error("File must contain width and length columns")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")

    # Always display current slab sizes
    if slab_sizes:
        st.markdown("**Selected slab sizes:**")
        for w, h in slab_sizes:
            st.write(f"- {int(w)} × {int(h)} cm")

# ──────────────────────────────────────────────────
# OPTIMIZATION LOGIC (unchanged from previous version)
# ──────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
run_optimization = st.button("Generate Optimal Cutting Plan")

if run_optimization and pieces and slab_sizes:
    best_result = None
    best_packer = None
    min_waste = float('inf')

    with st.spinner("Calculating optimal slab combination..."):
        for num_slabs in range(1, 4):  # Test combinations of 1-3 slabs
            for slab_combo in combinations_with_replacement(slab_sizes, num_slabs):
                packer = newPacker(rotation=False)
                
                for i, (w, h) in enumerate(pieces):
                    packer.add_rect(w, h, rid=i)
                
                for w, h in slab_combo:
                    packer.add_bin(w, h)
                
                packer.pack()

                if len(packer.rect_list()) < len(pieces):
                    continue  # Skip if not all pieces fit

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
        st.subheader(f"Optimal {material_type} Slab Combination")
        
        for i, (w, h) in enumerate(best_result["combo"]):
            st.markdown(f"""
            **Slab {i+1}:** {int(w)} × {int(h)} cm  
            &nbsp;&nbsp;&nbsp;&nbsp;Area: {w*h/10000:.2f} m²
            """)
        
        st.markdown(f"""
        **Total:**  
        - Slab area: {best_result['slab_area']:.2f} m²  
        - Waste: {best_result['waste']:.2f} m²  
        - Utilization: {best_result['utilization']:.1f}%
        """)

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # VISUALIZATION
        st.subheader("Cutting Layout")
        bins_rects = defaultdict(list)
        for rect in best_result["packer"].rect_list():
            bin_index, x, y, w, h, rid = rect
            bins_rects[bin_index].append((x, y, w, h, rid))

        cols = st.columns(len(bins_rects))
        
        for bin_index, rects in bins_rects.items():
            slab_w, slab_h = best_result["combo"][bin_index]
            
            fig, ax = plt.subplots(figsize=(6, 3))
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')
            
            # Draw slab
            ax.add_patch(patches.Rectangle(
                (0, 0), slab_w, slab_h,
                edgecolor='#0068c9',
                facecolor='#f0f7ff',
                lw=1.5
            ))
            
            # Draw pieces
            for i, (x, y, w, h, _) in enumerate(rects):
                ax.add_patch(patches.Rectangle(
                    (x, y), w, h,
                    facecolor=plt.cm.tab20(i % 20),
                    edgecolor='#333',
                    alpha=0.9,
                    lw=0.5
                ))
                ax.text(x + w/2, y + h/2, 
                       f"{int(w)}×{int(h)}", 
                       ha='center', va='center',
                       fontsize=8)
            
            ax.set_xlim(0, slab_w)
            ax.set_ylim(0, slab_h)
            ax.set_aspect('equal')
            ax.axis('off')
            plt.gca().invert_yaxis()
            
            with cols[bin_index]:
                st.pyplot(fig)
                slab_waste = (slab_w*slab_h - sum(w*h for _,_,w,h,_ in rects))/10000
                st.caption(f"Utilization: {sum(w*h for _,_,w,h,_ in rects)/(slab_w*slab_h)*100:.1f}%  Waste: {slab_waste:.2f} m²")

    else:
        st.error("No valid combination found with current slabs")

elif run_optimization:
    if not pieces:
        st.error("Please enter required pieces first")
    if not slab_sizes:
        st.error("Please enter available slab sizes")
















