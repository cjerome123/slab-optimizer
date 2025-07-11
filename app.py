import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from itertools import combinations_with_replacement
from collections import defaultdict
import pandas as pd

# ──────────────── PAGE CONFIG ────────────────
st.set_page_config(
    page_title="SlabCut Optimizer",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
        .reportview-container {
            background: #f8f9fa;
        }
        .sidebar .sidebar-content {
            background: #ffffff;
        }
        .stButton>button {
            background-color: #0068c9;
            color: white;
            font-weight: 500;
        }
        .stButton>button:hover {
            background-color: #0052a3;
        }
        .metric {
            background: #ffffff;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .slab-title {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .slab-details {
            font-size: 14px;
            color: #555;
        }
    </style>
""", unsafe_allow_html=True)

# ──────────────── APP MAIN LAYOUT ────────────────
st.title("SlabCut Optimizer")
st.markdown("<hr>", unsafe_allow_html=True)

# ──────────────── MATERIAL SELECTION ────────────────
with st.sidebar:
    st.subheader("Material Settings")
    material_type = st.radio("Material Type", ["Quartz", "Granite"])

# ──────────────── INPUT SECTIONS ────────────────
col1, col2 = st.columns(2)

# REQUIRED PIECES (meters input)
with col1:
    st.subheader("Required Pieces (m)")
    pieces_input = st.text_area(
        "Enter dimensions (width,length):",
        value="""0.60,1.20\n0.60,1.50\n0.80,1.20\n0.90,1.80\n1.20,2.40""",
        height=200
    )
    pieces = []
    for line in pieces_input.strip().splitlines():
        try:
            w, l = map(float, line.replace(',', ' ').split())
            pieces.append((w*100, l*100))  # Convert to cm
        except:
            st.error(f"Invalid format: {line}")
    
    if pieces:
        total_area = sum(w * l for w, l in pieces) / 10000
        st.markdown(f"**Total required:** {total_area:.2f} m²", help="Total area needed")

# AVAILABLE SLABS
with col2:
    st.subheader("Available Slabs")
    
    if material_type == "Quartz":
        quartz_sizes = [(60,320), (70,320), (80,320), (90,320), (100,320), (160,320)]
        selected = st.multiselect(
            "Select quartz slab sizes (cm):",
            options=[f"{w}x{h}" for w,h in quartz_sizes],
            default=[f"{w}x{h}" for w,h in quartz_sizes[:3]]
        )
        slab_sizes = []
        for size in selected:
            w, h = map(int, size.split('x'))
            slab_sizes.append((w, h))
    else:
        slabs_input = st.text_area(
            "Enter granite slab sizes (width,length cm):",
            value="60,120\n90,240\n120,240\n150,300",
            height=150
        )
        slab_sizes = []
        for line in slabs_input.strip().splitlines():
            try:
                w, h = map(float, line.replace(',', ' ').split())
                slab_sizes.append((w, h))
            except:
                st.error(f"Invalid format: {line}")

# ──────────────── OPTIMIZATION ────────────────
st.markdown("<hr>", unsafe_allow_html=True)
if st.button("Generate Optimal Cutting Plan"):
    best_result = None
    min_waste = float('inf')

    with st.spinner("Calculating..."):
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
        st.success("✅ Optimization Complete")
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # RESULTS SUMMARY
        st.subheader(f"Optimal {material_type} Solution")
        cols = st.columns(3)
        cols[0].metric("Slabs Used", len(best_result["combo"]))
        cols[1].metric("Total Waste", f"{best_result['waste']:.2f} m²")
        cols[2].metric("Utilization", f"{best_result['utilization']:.1f}%")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # HORIZONTAL VISUALIZATION
        st.subheader("Slab Layout (cm)")
        bins_rects = defaultdict(list)
        for rect in best_result["packer"].rect_list():
            bin_index, x, y, w, h, rid = rect
            bins_rects[bin_index].append((x, y, w, h, rid))

        for bin_index, rects in bins_rects.items():
            slab_w, slab_h = best_result["combo"][bin_index]
            
            # Ensure longer side is horizontal
            if slab_w < slab_h:
                slab_w, slab_h = slab_h, slab_w  # Swap dimensions
            
            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')
            
            # Draw slab
            ax.add_patch(patches.Rectangle(
                (0, 0), slab_w, slab_h,
                edgecolor='#0068c9', facecolor='#f0f7ff', lw=1.5
            ))
            
            # Draw pieces
            for i, (x, y, w, h, _) in enumerate(rects):
                ax.add_patch(patches.Rectangle(
                    (x, y), w, h,
                    facecolor=plt.cm.tab20(i % 20),
                    edgecolor='#333', alpha=0.9, lw=0.5
                ))
                ax.text(x + w/2, y + h/2, f"{int(w)}×{int(h)}", 
                       ha='center', va='center', fontsize=8)
            
            ax.set_xlim(0, slab_w)
            ax.set_ylim(0, slab_h)
            ax.set_aspect('equal')
            ax.axis('off')
            plt.gca().invert_yaxis()
            
            # Display slab info
            st.pyplot(fig)
            used_area = sum(w*h for _,_,w,h,_ in rects)
            waste_m2 = (slab_w*slab_h - used_area)/10000
            st.markdown(f"""
            <div class="metric">
                <p class="slab-title">Slab {bin_index+1}: {int(slab_w)}×{int(slab_h)} cm</p>
                <p class="slab-details">Waste: {waste_m2:.2f} m² | Utilized: {used_area/(slab_w*slab_h)*100:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)


















