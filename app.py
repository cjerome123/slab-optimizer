import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict

# Set page config
st.set_page_config(
    page_title="Cutlist Optimizer PRO",
    page_icon="✂️",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
.stButton>button {
    border-radius: 5px;
    border: 1px solid #4CAF50;
    color: white;
    background-color: #4CAF50;
}
.stTextInput>div>div>input, .stNumberInput>div>div>input {
    padding: 10px !important;
}
.st-ax {
    background-color: #f0f0f0;
}
.stAlert {
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

def main():
    st.title("✂️ Cutlist Optimizer PRO")
    st.write("Optimize material usage with professional cut planning")
    
    # Initialize session state
    if 'cuts' not in st.session_state:
        st.session_state.cuts = []
    if 'stock_length' not in st.session_state:
        st.session_state.stock_length = 2400.0
    
    # Sidebar controls
    with st.sidebar:
        st.header("Settings")
        st.session_state.stock_length = st.number_input(
            "Stock Length (mm)",
            min_value=100.0,
            value=2400.0,
            step=100.0
        )
        
        st.markdown("---")
        st.header("Add Cuts")
        
        cut_cols = st.columns(2)
        with cut_cols[0]:
            cut_length = st.number_input(
                "Cut Length (mm)",
                min_value=1.0,
                step=1.0
            )
        with cut_cols[1]:
            quantity = st.number_input(
                "Quantity",
                min_value=1,
                step=1
            )
            
        if st.button("➕ Add Cut"):
            if cut_length > st.session_state.stock_length:
                st.error("Cut length cannot exceed stock length!")
            else:
                st.session_state.cuts.append((cut_length, quantity))
                st.rerun()
                
        if st.button("🧹 Clear All"):
            st.session_state.cuts = []
            st.rerun()
    
    # Main content area
    tab1, tab2 = st.tabs(["📋 Input Cuts", "📊 Optimize & Visualize"])
    
    with tab1:
        if not st.session_state.cuts:
            st.info("No cuts added yet. Add cuts using the sidebar controls.")
        else:
            df = pd.DataFrame(
                st.session_state.cuts,
                columns=["Length (mm)", "Quantity"]
            )
            
            # Add total row
            total_row = pd.DataFrame({
                "Length (mm)": ["Total"],
                "Quantity": [df["Quantity"].sum()]
            })
            df = pd.concat([df, total_row], ignore_index=True)
            
            st.dataframe(
                df.style.apply(
                    lambda x: ["background: #e6f3e6" if x.name == len(df)-1 else "" for i in x],
                    axis=1
                ),
                use_container_width=True,
                hide_index=True
            )
            
            # Single cut deletion
            if len(st.session_state.cuts) > 0:
                st.write("Delete individual cuts:")
                delete_cols = st.columns(6)
                for i, cut in enumerate(st.session_state.cuts):
                    with delete_cols[i % 6]:
                        if st.button(
                            f"❌ {cut[0]}mm × {cut[1]}",
                            key=f"del_{i}",
                            use_container_width=True
                        ):
                            st.session_state.cuts.pop(i)
                            st.rerun()
    
    with tab2:
        if not st.session_state.cuts:
            st.warning("Please add cuts to optimize")
        else:
            if st.button("🔄 Run Optimization"):
                with st.spinner("Optimizing cut plan..."):
                    # Expand all cuts
                    expanded_cuts = []
                    for length, quantity in st.session_state.cuts:
                        expanded_cuts.extend([length] * quantity)
                    
                    # First-Fit Decreasing algorithm
                    expanded_cuts.sort(reverse=True)
                    bins = []
                    
                    for cut in expanded_cuts:
                        placed = False
                        for bin in bins:
                            if sum(bin) + cut <= st.session_state.stock_length:
                                bin.append(cut)
                                placed = True
                                break
                        if not placed:
                            bins.append([cut])
                    
                    # Display results
                    total_stock = len(bins)
                    total_material = total_stock * st.session_state.stock_length
                    used_material = sum(sum(bin) for bin in bins)
                    efficiency = (used_material / total_material) * 100
                    total_waste = total_material - used_material
                    
                    st.success(f"""
                    **Optimization Complete!**  
                    • Stock pieces needed: **{total_stock}**  
                    • Material usage efficiency: **{efficiency:.2f}%**  
                    • Total waste: **{total_waste:.1f} mm**  
                    """)
                    
                    # Visualization
                    fig, ax = plt.subplots(figsize=(10, max(3, len(bins)*0.5)))
                    colors = plt.cm.tab20c.colors
                    
                    for i, bin in enumerate(bins):
                        current_pos = 0
                        for j, cut in enumerate(bin):
                            ax.barh(
                                f'Stock {i+1}',
                                cut,
                                left=current_pos,
                                color=colors[j % len(colors)],
                                edgecolor='black'
                            )
                            ax.text(
                                current_pos + cut/2,
                                i,
                                f"{cut}mm",
                                ha='center',
                                va='center',
                                color='white',
                                fontsize=8
                            )
                            current_pos += cut
                        
                        # Waste portion
                        waste = st.session_state.stock_length - sum(bin)
                        ax.barh(
                            f'Stock {i+1}',
                            waste,
                            left=current_pos,
                            color='#cccccc',
                            alpha=0.7,
                            edgecolor='black'
                        )
                    
                    ax.set_xlabel('Length (mm)')
                    ax.set_title('Cut Optimization Plan', fontsize=12)
                    ax.grid(True, axis='x', alpha=0.3)
                    ax.set_axisbelow(True)
                    
                    st.pyplot(fig)
                    
                    # Detailed breakdown
                    st.subheader("Detailed Breakdown")
                    for i, bin in enumerate(bins, 1):
                        waste = st.session_state.stock_length - sum(bin)
                        st.write(f"""
                        **Stock Piece {i}**
                        - Cuts: {', '.join([f"{cut}mm" for cut in bin])}
                        - Usage: {sum(bin)} mm ({sum(bin)/st.session_state.stock_length:.1%})
                        - Waste: {waste} mm ({waste/st.session_state.stock_length:.1%})
                        """)

if __name__ == "__main__":
    main()






























