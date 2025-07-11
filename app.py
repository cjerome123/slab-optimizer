import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from itertools import combinations_with_replacement
from collections import defaultdict
import random

# ──────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Slab Optimizer",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Apply minimalist style
st.markdown("""
    <style>
        .reportview-container {
            background: #f8f9fa;
        }
        .sidebar .sidebar-content {
            background: #ffffff;
        }
        div[data-testid="stSidebarNav"] {
            padding-top: 20px;
        }
        .st-bb, .st-at, .st-ae, .st-af, .st-ag, .st-ah {
            border-color: #e9ecef;
        }
        .css-1aumxhk {
            background-color: #ffffff;
            background-image: none;
        }
        [data-testid="stSidebarUserContent"] {
            padding: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────
st.title("Slab Cutting Optimizer")
st.markdown("""<hr style="height:1px;border:none;color:#e9ecef;background-color:#e9ecef;"/>""", 
            unsafe_allow_html=True)

# ──────────────────────────────────────────────────
# SIDEBAR SETTINGS
# ──────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Settings")
    slab_mode = st.selectbox("Material Type", ["Quartz", "Granite", "Marble"])
    measurement_unit = st.selectbox("Unit", ["Meters", "Centimeters"], index=0)
    submit_btn_style = """
    <style>
        div.stButton > button:first-child {
            background-color: #4a8bfc;
            color: white;
            width: 100%;
            border-radius: 4px;
        }
    </style>
    """
    st.markdown(submit_btn_style, unsafe_allow_html=True)

# Conversion function
def convert_to_cm(value):
    return value * 100 if measurement_unit == "Meters" else value

# ──────────────────────────────────────────────────
# INPUT SECTIONS
# ──────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Required Pieces")
    default_pieces = "0.65,2.53\n0.64,2.27\n0.64,0.73\n0.73,2.27\n0.73,3.14\n0.73,0.73\n0.08,1.66\n0.08,2.53\n0.16,0.83\n0.15,0.82"
    pieces_input = st.text_area(
        f"Dimensions in {measurement_unit} (width,length)",
        value=default_pieces,
        height=200,
        help="Enter one piece per line in format: width,length"
    )

    pieces = []
    for line in pieces_input.strip().splitlines():
        try:
            parts = line.replace('\t', ' ').replace(',', ' ').split()
            w, l = map(float, parts[:2])
            pieces.append((convert_to_cm(w), convert_to_cm(l)))
        except ValueError:
            st.error(f"Invalid format: {line}")

    if pieces:
        total_area = sum(w * l for w, l in pieces) / (10000 if measurement_unit == "Meters" else 1)
        st.caption(f"Total area: {total_area:.2f} {'m²' if measurement_unit == 'Meters' else 'cm²'}")

with col2:
    st.subheader("Available Slabs")
    default_slabs = "0.60,3.20\n0.70,3.20\n0.80,3.20\n0.90,3.20\n1.00,3.20\n1.60,3.20"
    slabs_input = st.text_area(
        f"Slab sizes in {measurement_unit} (width,length)",
        value=default_slabs,
        height=200,
        help="Enter one slab size per line in format: width,length"
    )

    slab_sizes = []
    for line in slabs_input.strip().splitlines():
        try:
            parts = line.replace('\t', ' ').replace(',', ' ').split()
            w, l = map(float, parts[:2])
            slab_sizes.append((convert_to_cm(w), convert_to_cm(l)))
        except ValueError:
            st.error(f"Invalid format: {line}")

# ──────────────────────────────────────────────────
# OPTIMIZATION BUTTON
# ──────────────────────────────────────────────────
st.markdown("""<hr style="height:1px;border:none;color:#e9ecef;background-color:#e9ecef;"/>""", 
            unsafe_allow_html=True)

if st.button("Run Optimization"):
    # Optimization logic remains the same as previous version
    best_result = None
    best_packer = None
    min_waste = float('inf')

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
                    "slab_area": total_slab_area
                }
                best_packer = packer

    # Results display
    if best_result:
        st.success("Optimization completed successfully")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Material Type", slab_mode)
            st.metric("Total Waste", f"{best_result['waste']:.2f} m²")
        
        with col2:
            st.metric("Number of Slabs", len(best_result["combo"]))
            st.metric("Total Slab Area", f"{best_result['slab_area']/10000:.2f} m²")

        # Visualizations
        bins_rects = defaultdict(list)
        for rect in best_packer.rect_list():
            bin_index, x, y, w, h, rid = rect
            bins_rects[bin_index].append((x, y, w, h, rid))

        st.subheader("Layout Plans")
        
        for bin_index, rects in bins_rects.items():
            sw, sh = best_result["combo"][bin_index]
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Set white background
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')
            
            # Main slab rectangle
            ax.add_patch(patches.Rectangle(
                (0, 0), sw, sh, 
                edgecolor='#4a8bfc', 
                facecolor='#f8f9fa', 
                lw=2)
            )

            # Pieces
            colors = plt.cm.tab20.colors
            for i, (x, y, w, h, rid) in enumerate(rects):
                ax.add_patch(patches.Rectangle(
                    (x, y), w, h,
                    facecolor=colors[i % len(colors)],
                    edgecolor='#333',
                    lw=0.5,
                    alpha=0.8)
                )
                dim_text = f"{w/100:.2f}x{h/100:.2f}" if measurement_unit == "Meters" else f"{int(w)}x{int(h)}"
                ax.text(
                    x + w/2, y + h/2, dim_text,
                    ha='center', va='center',
                    fontsize=8,
                    color='#333'
                )

            ax.set_xlim(0, sw)
            ax.set_ylim(0, sh)
            ax.set_aspect('equal')
            ax.axis('off')
            plt.gca().invert_yaxis()
            
            slab_title = f"Slab {bin_index+1} ({sw/100:.2f}x{sh/100:.2f}m)" if measurement_unit == "Meters" else f"Slab {bin_index+1} ({int(sw)}x{int(sh)}cm)"
            st.pyplot(fig)
            st.caption(slab_title)

    else:
        st.error("No valid slab combination found")













