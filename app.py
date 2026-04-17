# app.py optimisé pour chargement rapide
import streamlit as st
import pandas as pd
import json
from utils_gov_gear import get_best_upgrades, pareto_front_fast, compute_detailed_stats, PIECES, LEVEL_ORDER

st.set_page_config(page_title="Kingshot Governor Gear Optimizer", layout="wide")
st.title("⚔️ Kingshot Governor Gear Optimizer")

# ----------------------------
# INITIALISATION SESSION STATE
# ----------------------------
for piece in PIECES:
    if piece not in st.session_state:
        st.session_state[piece] = "Blue**"

# ----------------------------
# LOAD / SAVE CURRENT GEAR
# ----------------------------
st.header("💾 Load / Save Current Gear Preset (optional)")
col1, col2 = st.columns(2)

uploaded_file = col1.file_uploader("Load gear JSON", type="json")
if uploaded_file is not None:
    loaded_data = json.load(uploaded_file)
    st.success("Gear loaded successfully!")
    for piece, level in loaded_data.items():
        if piece in PIECES and level in LEVEL_ORDER:
            st.session_state[piece] = level
else:
    loaded_data = None

if col2.button("Save current gear"):
    build = {piece: st.session_state.get(piece, "Blue**") for piece in PIECES}
    st.download_button(
        label="Download gear JSON",
        data=json.dumps(build, indent=2),
        file_name="gear.json",
        mime="application/json"
    )

# ----------------------------
# CURRENT GEAR INPUT (selectboxes)
# ----------------------------
st.header("🛡️ Current Governor Gear")
gear = {}
cols = st.columns(len(PIECES))
for i, piece in enumerate(PIECES):
    gear[piece] = cols[i].selectbox(
        piece.capitalize(),
        LEVEL_ORDER,
        index=LEVEL_ORDER.index(st.session_state[piece]),
        key=piece
    )
st.divider()

col1, col2, col3 = st.columns([1, 1, 4])

# Load bouton + uploader caché
with col1:
    uploaded_file = st.file_uploader(
        "Load",
        type="json",
        label_visibility="collapsed"
    )

# Save bouton
with col2:
    if st.button("💾 Save"):
        build = {piece: st.session_state.get(piece, "Blue**") for piece in PIECES}
        st.download_button(
            label="Download",
            data=json.dumps(build, indent=2),
            file_name="gear.json",
            mime="application/json"
        )

# Feedback zone
with col3:
    if uploaded_file is not None:
        loaded_data = json.load(uploaded_file)
        for piece, level in loaded_data.items():
            if piece in PIECES and level in LEVEL_ORDER:
                st.session_state[piece] = level
        st.success("Gear loaded")
# ----------------------------
# INVENTORY INPUT
# ----------------------------
st.header("📦 Inventory (Not saved)")
inv_cols = st.columns(3)
satin = inv_cols[0].number_input("Satin", min_value=0, value=0, key="satin")
threads = inv_cols[1].number_input("Threads", min_value=0, value=0, key="threads")
artisans = inv_cols[2].number_input("Artisans", min_value=0, value=0, key="artisans")
materials = {"satin": satin, "threads": threads, "artisans": artisans}

# ----------------------------
# RUN OPTIMIZATION (uniquement sur clic)
# ----------------------------
st.header("▶️ Find Best Upgrades")
if st.button("Calculate Best Upgrades"):

    # Charger le fichier JSON uniquement maintenant
    with open("data/gear_levels.json", "r") as f:
        levels_dict = json.load(f)

    level_keys = list(levels_dict.keys())
    level_index = {lvl: i for i, lvl in enumerate(level_keys)}

    # Calcul des upgrades
    solutions = get_best_upgrades(gear, levels=levels_dict, materials=materials)
    pareto_solutions = pareto_front_fast(solutions)

    if not pareto_solutions:
        st.warning("No possible upgrades with your current inventory")
        st.stop()

    # Max pour normalisation Gain % et KVK %
    max_gain = max(s["gain"] for s in pareto_solutions)
    max_kvk_points = max(s["kvk"]*36 for s in pareto_solutions)

    rows = []
    for idx, sol in enumerate(pareto_solutions, start=1):
        kvk_pts = sol["kvk"] * 36
        gain_pct = sol["gain"]
        row = {
            "Option #": idx,
            "KVK Points": f"{kvk_pts:,}".replace(",", " "),
            "Gain (%)": f"{gain_pct:.1f}",
            "% of Max Gain": f"{(gain_pct/max_gain*100):.1f}%" if max_gain>0 else "0%",
            "% of Max KVK Points": f"{(kvk_pts/max_kvk_points*100):.1f}%" if max_kvk_points>0 else "0%",
            "Cost (S/T/A)": f"{sol['satin']}/{sol['threads']}/{sol['artisans']}"
        }

        for c in sol["combo"]:
            piece = c["piece"]
            start_level = gear[piece]
            end_level = c["to"]
            upgrades = LEVEL_ORDER.index(end_level) - LEVEL_ORDER.index(start_level)
            row[piece.capitalize()] = f"{end_level} (+{upgrades})" if upgrades > 0 else end_level

        rows.append(row)

    df = pd.DataFrame(rows)

    # Highlight best KVK Points et % of Max Gain
    def highlight_cells(val, col):
        if col == "KVK Points" and val == f"{max_kvk_points:,}".replace(",", " "):
            return "background-color: lightblue; font-weight: bold"
        if col == "Gain (%)" and val == f"{max_gain:.1f}".replace(",", " "):
            return "background-color: orange; font-weight: bold"
        return ""

    def style_table(df):
        return df.style.map(lambda v: highlight_cells(v, "KVK Points"), subset=["KVK Points"])\
                       .map(lambda v: highlight_cells(v, "Gain (%)"), subset=["Gain (%)"])

    # Légende visuelle au-dessus du tableau
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:20px; margin-bottom:10px;">
            <div style="display:flex; align-items:center;">
                <div style="width:20px; height:20px; background-color: lightblue; margin-right:5px;"></div> 🔹 Best KVK Points
            </div>
            <div style="display:flex; align-items:center;">
                <div style="width:20px; height:20px; background-color: orange; margin-right:5px;"></div> 🔸 Best Power Gain %
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Tri par défaut décroissant sur KVK Points et affichage complet
    df_sorted = df.sort_values(by="KVK Points", ascending=False)
    st.dataframe(style_table(df_sorted), use_container_width=True, height=1200)

    st.markdown("## 🔍 Detailed Breakdown")
    for idx, sol in enumerate(pareto_solutions, start=1):

        with st.expander(f"Option #{idx} — Gain {sol['gain']:.2f}% | KVK {(sol['kvk']*36):,}".replace(",", " ")):

            stats = compute_detailed_stats(sol, gear, level_index)

            cols = st.columns(3)

            for i, (troop, values) in enumerate(stats.items()):
                with cols[i]:
                    st.markdown(f"""
                    **{troop.capitalize()}**  
                    - ATK: {values['atk']:.2f}%  
                    - DEF: {values['def']:.2f}%  
                    """)

