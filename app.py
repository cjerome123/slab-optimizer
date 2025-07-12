import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from collections import defaultdict
from itertools import combinations

# Set page config
st.set_page_config(
    page_title="Advanced Panel Optimizer",
    page_icon="✂️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.stButton>button {
    border-radius: 5px;
    border: 1px solid #4CAF50;
    color: white;
    background-color: #4CAF50;
}
.css-1v0mbdj {
    border-radius: 5px;
}
.stAlert {
    border-radius: 5px;
}
.css-1q8dd3e {
    border-radius: 5px;
}
.title-wrapper {
    display: flex;
    align-items: center;
}
.title-wrapper img {
    margin-right: 10px;
}
</style>
""", unsafe_allow_html=True)

def convert_to_cm(val_m):
    return round(val_m * 100, 2)

class PanelOptimizer:
    def __init__(self):
        self.stock_sizes = [
            (60, 320), 
            (70, 320),
            (80, 400),
            (90, 450)
        ]
        self.cuts = []
    
    def add_cuts_from_table(self, data):
        cleaned_data = []
        for row in data.split('\n'):
            if '\t' in row:
                dim1, dim2 = map(float, row.strip().split('\t'))
                cleaned_data.append((convert_to_cm(dim1), convert_to_cm(dim2)))
        return cleaned_data
    
    def optimize_panel_cutting(self, cuts, stock_size):
        width, height = stock_size
        bins = []
        remaining_cuts = cuts.copy()
        
        # Try both orientations for each cut
        oriented_cuts = []
        for cut in remaining_cuts:
            oriented_cuts.append(cut)
            oriented_cuts.append((cut[1], cut[0]))  # Rotated 90 degrees
        
        # Sort by area descending
        oriented_cuts.sort(key=lambda x: x[0]*x[1], reverse=True)
        
        while oriented_cuts:
            # Create new bin
            current_bin = {
                'cuts': [],
                'remaining_width': width,
                'remaining_height': height,
                'waste': width * height
            }
            
            # Try to add cuts
            i = 0
            while i < len(oriented_cuts):
                cut = oriented_cuts[i]
                
                # Check if cut fits in current orientation
                if (cut[0] <= current_bin['remaining_width'] and 
                    cut[1] <= current_bin['remaining_height']):
                    
                    current_bin['cuts'].append(cut)
                    current_bin['waste'] -= cut[0] * cut[1]
                    
                    # Update remaining space (simple vertical stacking)
                    current_bin['remaining_height'] -= cut[1]
                    
                    # Remove this cut from available cuts
                    oriented_cuts.pop(i)
                    
                    # Reset iterator since we modified the list
                    i = 0
                else:
                    i += 1
            
            bins.append(current_bin)
        
        return bins
    
    def visualize_panel(self, panel, stock_size):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_xlim(0, stock_size[0])
        ax.set_ylim(0, stock_size[1])
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_title(f"Panel Layout ({stock_size[0]}x{stock_size[1]}cm)", pad=20)
        
        current_y = 0
        colors = plt.cm.tab10.colors
        
        for i, cut in enumerate(panel['cuts']):
            rect = plt.Rectangle(
                (0, current_y), 
                cut[0], 
                cut[1],
                facecolor=colors[i % len(colors)],
                edgecolor='black',
                alpha=0.8,
                label=f"{cut[0]}x{cut[1]}cm"
            )
            ax.add_patch(rect)
            
            # Add text label
            ax.text(
                cut[0]/2, 
                current_y + cut[1]/2, 
                f"{cut[0]}x{cut[1]}",
                ha='center', 
                va='center',
                color='white',
                fontweight='bold'
            )
            
            current_y += cut[1]
        
        # Add waste area
        if panel['remaining_height'] > 0:
            waste_rect = plt.Rectangle(
                (0, current_y), 
                stock_size[0], 
                panel['remaining_height'],
                facecolor='lightgray',
                edgecolor='black',
                hatch='//',
                alpha=0.4,
                label='Waste'
            )
            ax.add_patch(waste_rect)
        
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        return fig

def main():
    st.title("📏 Advanced Panel Optimizer")
    st.markdown("Optimize material usage for rectangular cut pieces")
    
    # Initialize session state
    if 'input_data' not in st.session_state:
        st.session_state.input_data = """0.65\t2.53
0.64\t2.28
0.64\t0.73
0.73\t2.28
0.73\t3.14
0.73\t0.73
0.08\t1.67
0.08\t2.53
0.16\t0.83
0.15\t0.82"""
    
    if 'cuts_cm' not in st.session_state:
        st.session_state.cuts_cm = []
    
    # Create optimizer instance
    optimizer = PanelOptimizer()
    
    # Sidebar controls
    with st.sidebar:
        st.header("Stock Panel Sizes")
        selected_stock = st.selectbox(
            "Choose stock panel size:",
            options=[f"{w}x{h}cm" for w, h in optimizer.stock_sizes],
            index=0
        )
        stock_width, stock_height = map(int, selected_stock.replace('cm','').split('x'))
        
        st.markdown("---")
        st.header("Input Data")
        
        input_data = st.text_area(
            "Paste your cut dimensions (in meters):",
            value=st.session_state.input_data,
            height=200
        )
        
        if st.button("Process Input Data"):
            st.session_state.input_data = input_data
            st.session_state.cuts_cm = optimizer.add_cuts_from_table(input_data)
            st.rerun()
    
    # Main content
    st.header("Cut Pieces")
    
    if not st.session_state.cuts_cm:
        st.warning("No cut pieces loaded. Add data in the sidebar.")
    else:
        # Display cut list
        df = pd.DataFrame(
            [(w, h) for w, h in st.session_state.cuts_cm],
            columns=["Width (cm)", "Height (cm)"]
        )
        st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)
        
        # Calculate total area
        total_area = sum(w * h for w, h in st.session_state.cuts_cm)
        st.markdown(f"**Total cut area:** {total_area:.2f} cm²")
        
        # Optimization
        st.header("Optimization Results")
        
        if st.button(f"Optimize for {selected_stock} panels"):
            with st.spinner("Calculating optimal layout..."):
                results = optimizer.optimize_panel_cutting(
                    st.session_state.cuts_cm,
                    (stock_width, stock_height)
                )
                
                # Summary stats
                total_panels = len(results)
                total_stock_area = total_panels * stock_width * stock_height
                efficiency = (total_area / total_stock_area) * 100
                total_waste = total_stock_area - total_area
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Panels Needed", total_panels)
                col2.metric("Usage Efficiency", f"{efficiency:.1f}%")
                col3.metric("Total Waste", f"{total_waste:.1f} cm²")
                
                # Visualizations
                st.subheader("Panel Layouts")
                cols = st.columns(2)
                
                for i, panel in enumerate(results[:4]):  # Show first 4 panels
                    with cols[i % 2]:
                        st.markdown(f"**Panel {i+1}**")
                        fig = optimizer.visualize_panel(panel, (stock_width, stock_height))
                        st.pyplot(fig)
                        
                        # Show cut list for this panel
                        if panel['cuts']:
                            panel_cuts = pd.DataFrame(
                                panel['cuts'],
                                columns=["Width", "Height"]
                            )
                            st.dataframe(panel_cuts, hide_index=True)

if __name__ == "__main__":
    main()































