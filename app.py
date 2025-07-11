import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from itertools import combinations_with_replacement, permutations
from collections import Counter, defaultdict
import random

# ───────────────────────────────────────────────────
st.set_page_config(page_title="Slab Optimizer", layout="wide", initial_sidebar_state="expanded")
st.title("🩵 Slab Cutting Optimizer")
st.sidebar.title("⚙️ Settings")

slab_mode = st.sidebar.radio("Slab Type", ["Quartz", "Granite"])
dark_mode = st.sidebar.checkbox("🌙 Dark Mode", value=False)
if dark_mode:
    st.markdown("""
        <style>
            html, body, [class*="css"]  {
                background-color: #0e1117;
                color: #fafafa;
            }
            .stButton>button {
                background-color: #262730;
                color: white;
            }
        </style>
    """, unsafe_allow_html=True)

mode = slab_mode
st.caption(f"Mode: {mode}")

st.markdown("""
Enter your required pieces and slab sizes in **centimeters**.
This app finds the best slab combination that minimizes waste.
""")

# ───────────────────────────────────────────────────
# 1. Required Pieces Input
# ──────────────────────────────────────────────────
st.subheader("Required Pieces")
default_input = "65,253\n64,227\n64,73\n73,227\n73,314\n73,73\n8,166\n8,253\n16,83\n15,82"
user_input = st.text_area("✏️ One piece per line. Format: width,length (in cm)", value=default_input, height=150, label_visibility="visible")

pieces = []
for line in user_input.strip().splitlines():
    try:
        parts = line.replace('\t', ' ').replace(',', ' ').split()
        w, l = map(float, parts[:2])
        pieces.append((w, l))
    except:
        st.error(f"❌ Invalid format in: {line}")

if pieces:
    total_area_cm2 = sum(w * l for w, l in pieces)
    st.info(f"📀 Total required area: {total_area_cm2 / 10000:.2f} m²")

# ──────────────────────────────────────────────────
# [No change in slab inputs or optimization logic]
# ...

            ax.set_xlim(0, sw)
            ax.set_ylim(0, sh)
            ax.set_aspect('equal')
            ax.axis('off')  # Hide all axis elements for cleaner view
            plt.gca().invert_yaxis()
            st.pyplot(fig)
    else:
        st.error("❌ No valid slab combination found.")









