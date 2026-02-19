import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- Configuration ---
CSV_FILE = 'training_log.csv'
USER_PROFILE = {
    "name": "Usuario",
    "age": 30,
    "gender": "Hombre",
    "goal_body_fat": 12.0,
    "current_weight": 90.7
}

st.set_page_config(
    page_title="Gym PWA",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Mobile-First CSS ---
st.markdown("""
    <style>
    /* Global Dark Mode adjustments if needed, though Streamlit auto-detects */
    
    /* Increase button size for touch targets */
    .stButton > button {
        width: 100%;
        height: 3.5rem;
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 12px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    
    /* Increase input height */
    .stTextInput > div > div > input {
        min-height: 3rem;
        font-size: 1.1rem;
    }
    .stNumberInput > div > div > input {
        min-height: 3rem;
        font-size: 1.1rem;
    }
    .stSelectbox > div > div > div {
        min-height: 3rem;
        font-size: 1.1rem;
    }
    
    /* Remove padding to maximize screen space */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Stats cards */
    .metric-card {
        background-color: #262730;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Data Persistence ---
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        return pd.DataFrame(columns=["Fecha", "Ejercicio", "Peso", "Reps", "Notas"])

def save_workout(ejercicio, peso, reps, notas):
    df = load_data()
    new_entry = {
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Ejercicio": ejercicio,
        "Peso": peso,
        "Reps": reps,
        "Notas": notas
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    return True

# --- UI Components ---

# 1. User Profile Header
col1, col2 = st.columns([1, 2])
with col1:
    st.image("https://api.dicebear.com/9.x/avataaars/svg?seed=Felix", width=80) 
with col2:
    st.subheader(f"Hola, {USER_PROFILE['name']}!")
    st.caption(f"Meta: {USER_PROFILE['goal_body_fat']}% Grasa | Actual: {USER_PROFILE['current_weight']}kg")

st.divider()

# 2. Workout Entry Form
st.header("Registrar Set")

# Exercise Selector
COMMON_EXERCISES = [
    "Sentadilla (Squat)", "Press Banca (Bench Press)", "Peso Muerto (Deadlift)",
    "Press Militar (Overhead)", "Dominadas (Pull Ups)", "Remo (Row)", 
    "Fondos (Dips)", "Curl Bíceps", "Extensión Tríceps", "Prensa Piernas"
]

with st.form("workout_form", clear_on_submit=True):
    ejercicio = st.selectbox("Ejercicio", COMMON_EXERCISES)
    
    c1, c2 = st.columns(2)
    with c1:
        peso = st.number_input("Peso (kg)", min_value=0.0, step=2.5, format="%.1f")
    with c2:
        reps = st.number_input("Reps", min_value=0, step=1, value=10)
        
    notas = st.text_area("Notas (RPE, sensaciones...)", height=80)
    
    # Big Submit Button
    submitted = st.form_submit_button("LOG SET 📝")
    
    if submitted:
        if save_workout(ejercicio, peso, reps, notas):
            st.success(f"✅ Guardado: {ejercicio} - {peso}kg x {reps}")
            # Rerun to update history immediately
            # st.rerun() # Commented out to prevent aggressive reruns, let user see success msg first

# 3. Recent History
st.divider()
st.subheader("Historial Reciente (Últimos 5)")

df = load_data()
if not df.empty:
    # Sort by date descending
    df['Fecha'] = pd.to_datetime(df['Fecha']) # Ensure datetime for sorting
    df_sorted = df.sort_values(by='Fecha', ascending=False).head(5)
    
    # Display as styled cards for mobile friendliness
    for index, row in df_sorted.iterrows():
        with st.container():
            st.markdown(f"""
            <div style="background-color: #1E1E1E; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #FF4B4B;">
                <div style="font-weight: bold; font-size: 1.1em;">{row['Ejercicio']}</div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                    <span>⚖️ {row['Peso']} kg</span>
                    <span>🔄 {row['Reps']} reps</span>
                </div>
                <div style="font-size: 0.8em; color: #888; margin-top: 5px;">{row['Fecha'].strftime('%d/%m %H:%M')} | {row['Notas']}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No hay registros aún. ¡Empieza a entrenar!")

# Footer spacing
st.write("") 
st.write("") 
st.write("") 
