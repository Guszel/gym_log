import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from PIL import Image
import json

# --- Configuration ---
CSV_FILE = 'training_log.csv'
BODY_COMP_CSV_FILE = 'body_comp_log.csv'
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
    /* Dark Industrial Lab Theme */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
    
    /* Global Background */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Primary buttons (Chemistry Neon Green) */
    .stButton > button[kind="primary"] {
        background-color: transparent !important;
        color: #39FF14 !important;
        border: 2px solid #39FF14 !important;
        box-shadow: 0 0 10px rgba(57, 255, 20, 0.2);
        transition: all 0.3s ease;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #39FF14 !important;
        color: #0E1117 !important;
        box-shadow: 0 0 20px rgba(57, 255, 20, 0.6);
    }
    
    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        color: #E0E0CE !important;
        border: 1px solid #333 !important;
        transition: all 0.3s ease;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: #39FF14 !important;
        color: #39FF14 !important;
        box-shadow: 0 0 10px rgba(57, 255, 20, 0.4);
    }

    /* Input fields */
    .stTextInput > div > div > input, 
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea > div > div > textarea {
        background-color: #1A1D24 !important;
        color: #E0E0CE !important;
        border: 1px solid #333 !important;
    }
    .stTextInput > div > div > input:focus, 
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #39FF14 !important;
        box-shadow: 0 0 5px rgba(57, 255, 20, 0.5) !important;
    }
    
    /* Monospace class for stats */
    .mono-text {
        font-family: 'Roboto Mono', monospace !important;
    }
    
    /* Industrial Cards */
    .industrial-card {
        background-color: #13161C;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 12px;
        border: 1px solid rgba(57, 255, 20, 0.3);
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        transition: all 0.3s ease;
    }
    .industrial-card:hover {
        border-color: rgba(57, 255, 20, 0.8);
        box-shadow: 0 0 15px rgba(57, 255, 20, 0.2);
    }

    /* Increase button size for touch targets */
    .stButton > button {
        width: 100%;
        min-height: 3.5rem;
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 8px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    
    /* Text styles mapping */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #E0E0CE;
    }
    
    /* Remove padding to maximize screen space */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Data Persistence ---
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        return pd.DataFrame(columns=["Fecha", "Ejercicio", "Peso", "Reps", "Notas"])

def load_body_comp_data():
    if os.path.exists(BODY_COMP_CSV_FILE):
        return pd.read_csv(BODY_COMP_CSV_FILE)
    else:
        return pd.DataFrame(columns=["Fecha", "Peso", "Grasa_pct", "FFMI"])

def delete_workout(index):
    df = load_data()
    if index in df.index:
        df = df.drop(index)
        df.to_csv(CSV_FILE, index=False)
        return True
    return False

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

def save_body_comp(peso, grasa_pct, ffmi):
    df = load_body_comp_data()
    new_entry = {
        "Fecha": datetime.now().strftime("%Y-%m-%d"),
        "Peso": peso,
        "Grasa_pct": grasa_pct,
        "FFMI": ffmi
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    # Remove older duplicates for the same day to keep history clean (1 record per day max)
    df = df.drop_duplicates(subset=['Fecha'], keep='last')
    df.to_csv(BODY_COMP_CSV_FILE, index=False)
    return True

# --- UI Components ---

with st.sidebar:
    st.header("⚙️ Opciones")
    st.write("Exporta un respaldo de tus datos localmente.")
    
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "rb") as f:
            st.download_button(
                label="📥 Exportar Entrenamientos (CSV)",
                data=f,
                file_name="training_log.csv",
                mime="text/csv",
                use_container_width=True
            )
            
    if os.path.exists(BODY_COMP_CSV_FILE):
        with open(BODY_COMP_CSV_FILE, "rb") as f:
            st.download_button(
                label="📥 Exportar Composición Corporal (CSV)",
                data=f,
                file_name="body_comp_log.csv",
                mime="text/csv",
                use_container_width=True
            )

# 1. Status Bar Header
st.markdown("""
<style>
/* Streamlit Hack: Make the first columns block (stHorizontalBlock) fixed like a native sticky header */
div[data-testid="stHorizontalBlock"]:first-of-type {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999999;
    background: rgba(14, 17, 23, 0.85) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    padding: 10px 1rem;
    border-radius: 0 0 12px 12px;
    border-bottom: 1px solid rgba(57, 255, 20, 0.4);
    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    /* Attempt to center the content like the main app container */
    margin: 0 auto;
    max-width: 100%;
}
@media (min-width: 768px) {
    div[data-testid="stHorizontalBlock"]:first-of-type {
        max-width: 730px;
        left: 50%;
        transform: translateX(-50%);
    }
}
.status-text {
    font-size: 0.8rem;
    color: #E0E0CE;
    font-family: 'Roboto Mono', monospace;
    text-align: center;
    line-height: 1.2;
}
.status-val {
    color: #39FF14;
    font-weight: bold;
    font-size: 0.95rem;
}
/* Ensure the block container has enough padding to scroll under the sticky header */
.block-container {
    padding-top: 1rem !important; 
}
</style>
""", unsafe_allow_html=True)

if 'current_muscle_group' not in st.session_state:
    st.session_state.current_muscle_group = 'Pecho'

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"<div class='status-text'>⚖️ Peso<br><span class='status-val'>{USER_PROFILE['current_weight']} kg</span></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='status-text'>🎯 Meta<br><span class='status-val'>{USER_PROFILE['goal_body_fat']}% Grasa</span></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='status-text'>⚡ Sesión<br><span class='status-val'>{st.session_state.current_muscle_group}</span></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Entrenamiento", "Composición Corporal", "Progreso Visual", "Nutrición"])

with tab1:
    # 2. Workout Entry Form
    st.markdown("<h3 style='font-family: sans-serif; font-size: 1.3rem; color: #E0E0CE; margin-bottom: 0;'>Registrar Set</h3>", unsafe_allow_html=True)

    # Exercise Selector
    EXERCISE_CATALOG = {
        "Pecho": [
            "Press Banca Plano", "Press Banca Inclinado", "Press Banca Declinado",
            "Aperturas con Mancuernas", "Cruce en Poleas", "Fondos de Pecho",
            "Pullover", "Press en Máquina", "Flexiones (Push-ups)"
        ],
        "Espalda": [
            "Dominadas (Pull Ups)", "Dominadas Supinas (Chin Ups)", "Remo con Barra",
            "Remo con Mancuerna", "Jalón al Pecho", "Remo en Polea Baja",
            "Remo en T", "Pullover en Polea", "Peso Muerto (Espalda)", "Encogimientos (Trapecio)"
        ],
        "Piernas": [
            "Sentadilla (Squat)", "Prensa Piernas", "Zancadas (Lunges)",
            "Sentadilla Búlgara", "Peso Muerto Rumano", "Curl Femoral Tumbado",
            "Curl Femoral Sentado", "Extensión de Cuádriceps", "Elevación de Talones de Pie",
            "Elevación de Talones Sentado", "Sentadilla Hack", "Hip Thrust"
        ],
        "Hombros": [
            "Press Militar (Overhead)", "Press Arnold", "Elevaciones Laterales",
            "Elevaciones Frontales", "Pájaros (Deltoides Posterior)", "Face Pull",
            "Press Tras Nuca", "Elevaciones Laterales en Polea"
        ],
        "Brazos": [
            "Curl Bíceps con Barra", "Curl Bíceps con Mancuernas", "Curl Martillo",
            "Curl en Banco Scott", "Curl Concentrado", "Extensión Tríceps en Polea",
            "Press Francés", "Fondos de Tríceps", "Patada de Tríceps",
            "Extensión Tríceps Tras Nuca"
        ],
        "Core / Otros": [
            "Crunch Abdominal", "Plancha (Plank)", "Elevación de Piernas Colgado",
            "Rueda Abdominal", "Russian Twists", "Woodchoppers", "Paseo del Granjero"
        ]
    }

    grupo_muscular = st.selectbox("Grupo Muscular", list(EXERCISE_CATALOG.keys()), key="current_muscle_group")

    # Initialize timer state
    if "start_timer" not in st.session_state:
        st.session_state.start_timer = False

    with st.form("workout_form", clear_on_submit=True):
        ejercicio = st.selectbox("Ejercicio", EXERCISE_CATALOG[grupo_muscular])
        
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
                st.session_state.start_timer = True # Trigger timer on save
                
    # --- Rest Timer Section ---
    st.divider()
    st.subheader("⏱️ Temporizador de Descanso")
    
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        rest_time = st.number_input("Segundos", min_value=10, max_value=300, value=90, step=10)
    with col_t2:
        # Extra styling to make the button giant
        st.markdown("""
        <style>
        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #FF4B4B;
            color: white;
            height: 4rem;
            font-size: 1.5rem;
            border-radius: 15px;
            width: 100%;
            margin-top: 25px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        manual_start = st.button("INICIAR TEMPORIZADOR", type="primary")
        
    if manual_start:
        st.session_state.start_timer = True
        
    # Render timer logic if triggered
    if st.session_state.start_timer:
        timer_html = f"""
        <div id="timer-container" style="
            background-color: #1E1E1E; 
            border: 2px solid #333; 
            border-radius: 15px; 
            padding: 20px; 
            text-align: center;
            margin-top: 10px;
            transition: background-color 0.3s;
        ">
            <h1 id="timer-display" style="
                font-size: 4rem; 
                margin: 0; 
                color: #FFFFFF;
                font-family: monospace;
            ">{rest_time}</h1>
            <p id="timer-msg" style="color: #888; margin-top: 5px; font-size: 1.2rem;">Descansando...</p>
        </div>

        <script>
            var timeLeft = {rest_time};
            var timerDisplay = document.getElementById("timer-display");
            var timerContainer = document.getElementById("timer-container");
            var timerMsg = document.getElementById("timer-msg");
            
            var countdown = setInterval(function() {{
                timeLeft--;
                timerDisplay.innerText = timeLeft;
                
                if (timeLeft <= 0) {{
                    clearInterval(countdown);
                    timerDisplay.innerText = "0";
                    timerMsg.innerText = "¡Siguiente Serie!";
                    timerMsg.style.color = "#FFFFFF";
                    timerMsg.style.fontWeight = "bold";
                    
                    // Try to vibrate phone (Android mainly)
                    if (navigator.vibrate) {{
                        navigator.vibrate([500, 300, 500, 300, 500]);
                    }}
                    
                    // Flashing effect
                    var flashCount = 0;
                    var flashInterval = setInterval(function() {{
                        timerContainer.style.backgroundColor = (flashCount % 2 === 0) ? "#FF4B4B" : "#1E1E1E";
                        flashCount++;
                        if (flashCount > 10) {{
                            clearInterval(flashInterval);
                            timerContainer.style.backgroundColor = "#1E1E1E"; // reset
                        }}
                    }}, 300);
                }}
            }}, 1000);
        </script>
        """
        import streamlit.components.v1 as components
        components.html(timer_html, height=200)
        
        # Reset state so it doesn't auto-start on next UI interaction unless clicked again
        st.session_state.start_timer = False

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
                col_card, col_btn = st.columns([5, 1])
                with col_card:
                    if isinstance(row['Fecha'], str):
                        fecha_str = row['Fecha']
                    else:
                        fecha_str = row['Fecha'].strftime('%d/%m %H:%M')
                    
                    # 1RM Calculation (Brzycki)
                    peso_val = float(row['Peso'])
                    reps_val = int(row['Reps'])
                    # If reps is 0, 1RM is essentially 0 or N/A, handle gracefully:
                    if reps_val == 0:
                        rm_est = 0
                    elif reps_val == 1:
                        rm_est = peso_val
                    else:
                        # Cap at 36 reps to prevent division by zero or negative denominator
                        reps_for_calc = min(reps_val, 36)
                        rm_est = peso_val / (1.0278 - (0.0278 * reps_for_calc))
                        
                    st.markdown(f"""
                    <div class="industrial-card">
                        <div style="font-weight: bold; font-size: 1.1em; color: #39FF14;">{row['Ejercicio']}</div>
                        <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                            <span class="mono-text">⚖️ {row['Peso']} kg x {row['Reps']} reps</span>
                            <span class="mono-text" style="color: #00FFFF; font-size: 0.9em; border: 1px solid #00FFFF; padding: 2px 6px; border-radius: 4px;">🎯 1RM Est: {rm_est:.1f} kg</span>
                        </div>
                        <div style="font-size: 0.8em; color: #888; margin-top: 5px;">{fecha_str} | {row['Notas']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    if st.button("🗑️", key=f"del_{index}"):
                        delete_workout(index)
                        st.rerun()
    else:
        st.info("No hay registros aún. ¡Empieza a entrenar!")

with tab2:
    st.header("Composición Corporal")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        altura = st.number_input("Altura (cm)", min_value=100.0, max_value=250.0, value=170.0, step=1.0)
    with col_b:
        peso_comp = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, value=75.0, step=0.1, key="peso_comp")
    with col_c:
        cintura = st.number_input("Cintura (cm)", min_value=50.0, max_value=150.0, value=85.0, step=1.0)
        
    calc_pressed = st.button("CALCULAR Y GUARDAR 📊")
    
    if calc_pressed:
        peso_lbs = peso_comp * 2.20462
        cintura_in = cintura / 2.54
        
        is_male = USER_PROFILE.get("gender", "Hombre").lower() == "hombre"
        
        # Fórmula YMCA para porcentaje de grasa corporal
        if is_male:
            grasa_pct = (4.15 * cintura_in - 0.082 * peso_lbs - 98.42) / peso_lbs * 100
        else:
            grasa_pct = (4.15 * cintura_in - 0.082 * peso_lbs - 76.76) / peso_lbs * 100
            
        grasa_pct = max(1.0, min(60.0, grasa_pct))
        
        masa_magra_kg = peso_comp * (1 - (grasa_pct / 100))
        altura_m = altura / 100
        ffmi = masa_magra_kg / (altura_m ** 2)
        
        # Save to history
        save_body_comp(peso_comp, grasa_pct, ffmi)
        
        st.divider()
        st.subheader("Resultados")
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric(label="% Grasa Corporal", value=f"{grasa_pct:.1f}%")
        with c2:
            st.metric(label="FFMI (Masa Libre de Grasa)", value=f"{ffmi:.1f}")
            
        st.info("💡 **FFMI:** Un valor de 18-20 es normal/promedio. 21-22 es excelente. >25 es el límite natural teórico para hombres.")
        st.caption("Fórmula utilizada: Estimación YMCA para Grasa Corporal y FFMI estándar.")
        st.success("✅ Datos guardados en el historial.")

with tab3:
    st.header("Progreso Visual")
    
    # --- Gráfico 1: Evolución de Peso y Grasa ---
    st.subheader("Evolución de Composición Corporal")
    df_comp = load_body_comp_data()
    
    if not df_comp.empty and len(df_comp) > 0:
        # Sort by date
        df_comp['Fecha'] = pd.to_datetime(df_comp['Fecha'])
        df_comp = df_comp.sort_values(by='Fecha')
        
        # Create figure with secondary y-axis
        fig_comp = go.Figure()
        
        # Add Peso trace (primary Y)
        fig_comp.add_trace(go.Scatter(
            x=df_comp['Fecha'], y=df_comp['Peso'],
            name='Peso (kg)',
            mode='lines+markers',
            line=dict(color='#00FFFF', width=3),
            marker=dict(size=8, color='#00FFFF', line=dict(width=1, color='#0E1117'))
        ))
        
        # Add Grasa trace (secondary Y)
        fig_comp.add_trace(go.Scatter(
            x=df_comp['Fecha'], y=df_comp['Grasa_pct'],
            name='% Grasa',
            mode='lines+markers',
            yaxis='y2',
            line=dict(color='#39FF14', width=3, dash='dot'),
            marker=dict(size=8, color='#39FF14', line=dict(width=1, color='#0E1117'))
        ))
        
        # Update layout for secondary Y-axis and mobile responsiveness
        fig_comp.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#E0E0CE")),
            margin=dict(l=0, r=0, t=30, b=0),
            yaxis=dict(title='Peso (kg)', title_font=dict(color='#00FFFF'), tickfont=dict(color='#00FFFF'), gridcolor='#1A1D24'),
            yaxis2=dict(title='% Grasa', title_font=dict(color='#39FF14'), tickfont=dict(color='#39FF14'), anchor='x', overlaying='y', side='right', gridcolor='#1A1D24'),
            xaxis=dict(gridcolor='#1A1D24', tickfont=dict(color='#E0E0CE')),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Calcula y guarda tu composición corporal en la pestaña anterior para ver tu progreso.")
        
    st.divider()
    
    # --- Gráfico 2: Volumen Semanal por Grupo Muscular ---
    st.subheader("Volumen Semanal por Grupo Muscular")
    df_train = load_data()
    
    if not df_train.empty:
        # Map exercise to category
        def get_category(ejercicio):
            for cat, ejercicios in EXERCISE_CATALOG.items():
                if ejercicio in ejercicios:
                    return cat
            return "Otros"
            
        df_train['Grupo Muscular'] = df_train['Ejercicio'].apply(get_category)
        df_train['Volumen'] = df_train['Peso'] * df_train['Reps']
        
        # Ensure 'Fecha' is datetime
        df_train['Fecha'] = pd.to_datetime(df_train['Fecha'])
        
        # Group by week and muscle group
        # Using week period allows nice alignment on charts
        df_train['Semana'] = df_train['Fecha'].dt.to_period('W').apply(lambda r: r.start_time)
        
        df_grouped = df_train.groupby(['Semana', 'Grupo Muscular'])['Volumen'].sum().reset_index()
        
        # Create bar chart
        if not df_grouped.empty:
            cyan_neon_palette = ['#00FFFF', '#39FF14', '#FF00FF', '#FFFF00', '#FF3914', '#9D00FF']
            fig_vol = px.bar(
                df_grouped, 
                x="Semana", 
                y="Volumen", 
                color="Grupo Muscular",
                title="Volumen (Peso x Reps)",
                barmode='stack', # Stacked is usually better to see total weekly volume
                color_discrete_sequence=cyan_neon_palette
            )
            
            fig_vol.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#E0E0CE")),
                margin=dict(l=0, r=0, t=30, b=0),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title="", gridcolor='#1A1D24', tickfont=dict(color='#E0E0CE')),
                yaxis=dict(title="Volumen (kg)", gridcolor='#1A1D24', tickfont=dict(color='#E0E0CE')),
                title_font=dict(color="#E0E0CE")
            )
            
            # Reduce brightness of bars a bit to fit dark theme, or add borders
            fig_vol.update_traces(marker_line_width=1, marker_line_color='#0E1117')
            
            st.plotly_chart(fig_vol, use_container_width=True)
        else:
            st.info("No hay datos de entrenamiento suficientes para mostrar el volumen semanal.")
    else:
        st.info("Registra algunos sets de entrenamiento para ver tu volumen semanal.")

with tab4:
    st.header("Calculadora Nutricional")
    
    # 1. Fetch latest body comp data
    df_comp = load_body_comp_data()
    if not df_comp.empty:
        latest_comp = df_comp.iloc[-1]
        peso_actual = float(latest_comp['Peso'])
        grasa_actual = float(latest_comp['Grasa_pct'])
        st.caption(f"Usando registro más reciente: **{peso_actual} kg** a **{grasa_actual:.1f}% Grasa**")
    else:
        peso_actual = USER_PROFILE.get("current_weight", 80.0)
        grasa_actual = 20.0 # Default guess if no data
        st.warning("⚠️ No hay historial de composición corporal. Ve a la Pestaña 2 y guarda tus datos para un cálculo preciso.")
        st.caption(f"Usando valores por defecto: **{peso_actual} kg** a **{grasa_actual:.1f}% Grasa**")

    # 2. Activity Multiplier
    ACTIVITY_LEVELS = {
        "Sedentario (Poco o nada de ejercicio)": 1.2,
        "Ligero (Ejercicio ligero 1-3 días/sem)": 1.375,
        "Moderado (Ejercicio moderado 3-5 días/sem)": 1.55,
        "Activo (Ejercicio fuerte 6-7 días/sem)": 1.725,
        "Muy Activo (Ejercicio muy fuerte, doble sesión)": 1.9
    }
    
    actividad = st.selectbox("Nivel de Actividad:", list(ACTIVITY_LEVELS.keys()), index=2) # Default Moderado
    multiplicador = ACTIVITY_LEVELS[actividad]
    
    # 3. Katch-McArdle Calculation
    lbm_kg = peso_actual * (1 - (grasa_actual / 100))
    bmr = 370 + (21.6 * lbm_kg)
    tdee = bmr * multiplicador
    
    # Recomp Goal: Moderate deficit
    cal_meta = tdee - 300
    
    # Macros estimation (Recomp - High Protein)
    pro_meta = 2.2 * lbm_kg # 2.2g per kg of LBM (or total weight, LBM is safer for high body fat)
    fat_meta = 0.8 * peso_actual # 0.8g per kg of bodyweight
    
    # Remaining cals for carbs
    cal_from_pro_fat = (pro_meta * 4) + (fat_meta * 9)
    carb_meta = max(0, (cal_meta - cal_from_pro_fat) / 4)
    
    st.subheader("Tus Metas Diarias (Recomposición)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kcal", f"{cal_meta:.0f}")
    c2.metric("Proteína", f"{pro_meta:.0f}g")
    c3.metric("Grasas", f"{fat_meta:.0f}g")
    c4.metric("Carbos", f"{carb_meta:.0f}g")
    
    # 4. IA Food Lens
    st.divider()
    st.subheader("📸 IA Food Lens (Nutrición con IA)")
    st.write("Sube una foto de tu comida o tómale una foto. La IA analizará los ingredientes, estimará la porción y extraerá los macros para ti.")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.warning("⚠️ No se encontró la variable de entorno `GEMINI_API_KEY`. Por favor configúrala en tu sistema para usar esta función.")
    else:
        genai.configure(api_key=api_key)
        
        with st.expander("Abrir Escáner de Comida", expanded=False):
            img_file_buffer = st.camera_input("Toma una foto de tu comida")
            uploaded_file = st.file_uploader("O sube una imagen de tu galería", type=['png', 'jpg', 'jpeg'])
            
            image_to_analyze = img_file_buffer if img_file_buffer else uploaded_file
            
            if image_to_analyze:
                image = Image.open(image_to_analyze)
                st.image(image, caption="Comida a analizar", use_container_width=True)
                
                if st.button("Analizar Comida con IA 🤖", type="primary"):
                    with st.spinner("Analizando plato... calculando macros..."):
                        try:
                            # Use Gemini 1.5 Flash (vision capable) - standard robust model
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            prompt = """
                            Eres un experto nutricionista predictivo. Analiza la imagen de esta comida.
                            Identifica los alimentos presentes y trata de estimar el tamaño de la porción visualmente.
                            A partir de eso, calcula los macronutrientes aproximados totales del plato.
                            Tu ÚNICA salida debe ser un objeto JSON estrictamente válido, usando las siguientes claves.
                            No devuelvas texto plano, ni bloques de código markdown extra (como ```json), SOLO el JSON puro:
                            {
                                "food_name": "Nombre descriptivo resumido del plato (ej. Ensalada con Pollo, 2 Huevos Fritos con Pan)",
                                "calories": <número entero>,
                                "protein": <número entero gramos>,
                                "fats": <número entero gramos>,
                                "carbs": <número entero gramos>
                            }
                            Si la imagen no parece ser comida, devuelve 0 en los valores y "No es comida" como nombre.
                            """
                            response = model.generate_content([prompt, image])
                            
                            # Clean up the response in case it returned markdown formatting anyway
                            raw_text = response.text.replace("```json", "").replace("```", "").strip()
                            
                            food_data = json.loads(raw_text)
                            
                            # Store in session state to auto-populate the form below
                            st.session_state.temp_food_name = food_data.get("food_name", "Desconocido")
                            st.session_state.temp_cal = int(food_data.get("calories", 0))
                            st.session_state.temp_p = int(food_data.get("protein", 0))
                            st.session_state.temp_g = int(food_data.get("fats", 0))
                            st.session_state.temp_c = int(food_data.get("carbs", 0))
                            
                            st.success("¡Análisis completado! Los datos se han copiado a tu formulario abajo.")
                            
                        except Exception as e:
                            st.error(f"Error al analizar la imagen: {e}")

    st.divider()
    
    # 5. Daily Simulator (Ephemeral state)
    st.subheader("Simulador Diario")
    st.write("Añade alimentos para ver cómo encajan en tus macros de hoy. Si usaste IA Food Lens, revisa o edita los datos aquí antes de agregar.")
    
    if "consumed_foods" not in st.session_state:
        st.session_state.consumed_foods = []
        
    # Get values from session state if they exist, otherwise default to empty/0
    default_name = st.session_state.pop("temp_food_name", "")
    default_cal = st.session_state.pop("temp_cal", 0)
    default_p = st.session_state.pop("temp_p", 0)
    default_g = st.session_state.pop("temp_g", 0)
    default_c = st.session_state.pop("temp_c", 0)
    
    # Sub-form for food
    with st.form("food_entry", clear_on_submit=False):
        f1, f2 = st.columns([2, 1])
        with f1:
            food_name = st.text_input("Comida (ej. 2 Huevos revueltos)", value=default_name)
        with f2:
            food_cal = st.number_input("Kcal", min_value=0, step=10, value=default_cal)
            
        m1, m2, m3 = st.columns(3)
        with m1:
            food_p = st.number_input("Prot (g)", min_value=0, step=1)
        with m2:
            food_g = st.number_input("Grasa (g)", min_value=0, step=1)
        with m3:
            food_c = st.number_input("Carbo (g)", min_value=0, step=1)
            
        add_food = st.form_submit_button("Añadir 🍳")
        
        if add_food and food_name != "":
            st.session_state.consumed_foods.append({
                "nombre": food_name, "cal": food_cal, "p": food_p, "g": food_g, "c": food_c
            })
            
    # Calculate consumed
    cons_cal = sum(f["cal"] for f in st.session_state.consumed_foods)
    cons_p = sum(f["p"] for f in st.session_state.consumed_foods)
    cons_g = sum(f["g"] for f in st.session_state.consumed_foods)
    cons_c = sum(f["c"] for f in st.session_state.consumed_foods)
    
    st.markdown("### Restante Hoy")
    
    def render_progress(label, consumed, goal, color):
        rem = max(0, goal - consumed)
        pct = min(1.0, consumed / goal) if goal > 0 else 0
        st.markdown(f"**{label}:** Consumido {consumed:.0f} / Meta {goal:.0f} (Te quedan **{rem:.0f}**)")
        st.progress(pct)
        
    render_progress("🔥 Calorías", cons_cal, cal_meta, "normal")
    render_progress("🍗 Proteína (g)", cons_p, pro_meta, "normal")
    render_progress("🥑 Grasas (g)", cons_g, fat_meta, "normal")
    render_progress("🍚 Carbos (g)", cons_c, carb_meta, "normal")
    
    if len(st.session_state.consumed_foods) > 0:
        with st.expander("Ver lista de alimentos hoy"):
            for idx, f in enumerate(st.session_state.consumed_foods):
                st.write(f"- **{f['nombre']}**: {f['cal']} kcal (P:{f['p']} G:{f['g']} C:{f['c']})")
                
            if st.button("Limpiar Registro"):
                st.session_state.consumed_foods = []
                st.rerun()

# Footer spacing
st.write("")
st.write("") 
st.write("") 
