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

# --- Mobile-First CSS Removed ---

ROUTINES_FILE = 'plantillas_rutinas.json'
EXERCISES_FILE = 'ejercicios_master.csv'
CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"unidad_preferida": "Kg"}

def save_config(config_dict):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=4)

APP_CONFIG = load_config()
UNIDAD_GLOBAL = APP_CONFIG.get("unidad_preferida", "Kg")

def convert_weight(weight, from_unit, to_unit):
    if from_unit == to_unit:
        return weight
    if from_unit == "Kg" and to_unit == "Lbs":
        return weight * 2.20462
    if from_unit == "Lbs" and to_unit == "Kg":
        return weight / 2.20462
    return weight

DEFAULT_EXERCISES = {
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

def load_routines():
    if os.path.exists(ROUTINES_FILE):
        with open(ROUTINES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_exercises():
    if os.path.exists(EXERCISES_FILE):
        df = pd.read_csv(EXERCISES_FILE)
        catalog = {}
        if 'Grupo Muscular' in df.columns and 'Nombre del Ejercicio' in df.columns:
            for grupo, group_df in df.groupby('Grupo Muscular'):
                catalog[grupo] = sorted(group_df['Nombre del Ejercicio'].tolist())
        return catalog
    else:
        records = []
        for grupo, ejercicios in DEFAULT_EXERCISES.items():
            for ej in ejercicios:
                records.append({"Nombre del Ejercicio": ej, "Grupo Muscular": grupo})
        df = pd.DataFrame(records)
        df.to_csv(EXERCISES_FILE, index=False)
        return {k: sorted(v) for k, v in DEFAULT_EXERCISES.items()}

def save_new_exercise(nombre, grupo):
    df_new = pd.DataFrame([{"Nombre del Ejercicio": nombre, "Grupo Muscular": grupo}])
    if os.path.exists(EXERCISES_FILE):
        df_exist = pd.read_csv(EXERCISES_FILE)
        df = pd.concat([df_exist, df_new], ignore_index=True)
    else:
        df = df_new
    df = df.drop_duplicates(subset=["Nombre del Ejercicio"])
    df.to_csv(EXERCISES_FILE, index=False)
def save_routine_template(nombre, ejercicios):
    routines = load_routines()
    routines[nombre] = ejercicios
    with open(ROUTINES_FILE, 'w', encoding='utf-8') as f:
        json.dump(routines, f, ensure_ascii=False, indent=4)

def delete_routine_template(nombre):
    routines = load_routines()
    if nombre in routines:
        del routines[nombre]
        with open(ROUTINES_FILE, 'w', encoding='utf-8') as f:
            json.dump(routines, f, ensure_ascii=False, indent=4)
        return True
    return False

EXERCISE_CATALOG = load_exercises()

# --- Data Persistence ---
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        if 'Rutina_Nombre' not in df.columns:
            df['Rutina_Nombre'] = 'Legacy'
        if 'ID_Sesion' not in df.columns:
            df['ID_Sesion'] = 'N/A'
        if 'Unidad' not in df.columns:
            df['Unidad'] = 'Kg' # Legacy default
        return df
    else:
        return pd.DataFrame(columns=["Fecha", "Rutina_Nombre", "ID_Sesion", "Ejercicio", "Peso", "Reps", "Unidad", "Notas"])

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

def save_workout(ejercicio, peso, reps, notas, unidad_input, rutina_nombre="Libre", id_sesion="N/A"):
    # Convert right away to global unit
    peso_convertido = convert_weight(peso, unidad_input, UNIDAD_GLOBAL)

    df = load_data()
    new_entry = {
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Rutina_Nombre": rutina_nombre,
        "ID_Sesion": id_sesion,
        "Ejercicio": ejercicio,
        "Peso": round(peso_convertido, 2),
        "Reps": reps,
        "Unidad": UNIDAD_GLOBAL,
        "Notas": notas
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    return True

def save_routine(rutina_nombre, id_sesion, df_sets):
    df = load_data()
    records = []
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    for s in df_sets:
        # Expected df_sets dict has 'Unidad'
        unidad_input = s.get('Unidad', UNIDAD_GLOBAL)
        peso_orig = s['Peso']
        peso_convertido = convert_weight(peso_orig, unidad_input, UNIDAD_GLOBAL)
        
        records.append({
            "Fecha": fecha,
            "Rutina_Nombre": rutina_nombre,
            "ID_Sesion": id_sesion,
            "Ejercicio": s['Ejercicio'],
            "Peso": round(peso_convertido, 2),
            "Reps": s['Reps'],
            "Unidad": UNIDAD_GLOBAL,
            "Notas": s['Notas']
        })
    df = pd.concat([df, pd.DataFrame(records)], ignore_index=True)
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
if 'current_muscle_group' not in st.session_state:
    st.session_state.current_muscle_group = 'Pecho'

current_weight_display = USER_PROFILE['current_weight']
if UNIDAD_GLOBAL == "Lbs":
    current_weight_display = round(current_weight_display * 2.20462, 1)

st.info(f"⚖️ **Peso:** {current_weight_display} {UNIDAD_GLOBAL} | 🎯 **Meta:** {USER_PROFILE['goal_body_fat']}% Grasa | ⚡ **Sesión:** {st.session_state.current_muscle_group}")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Entrenamiento", "Composición Corporal", "Progreso Visual", "Nutrición", "⚙️ Configuración", "🛠️ Crear Rutina"])

with tab1:
    # 2. Workout Entry Form
    st.subheader("Entrenamiento Activo")

    # Exercise Catalog for "Libre" mode uses the global EXERCISE_CATALOG

    routines = load_routines()
    rutina_opciones = [r for r in routines.keys() if r != "Libre (Histórico)"] + ["Libre"]
    
    rutina_seleccionada = st.selectbox("Rutina Activa", rutina_opciones, key="current_muscle_group")

    # Initialize timer state
    if "start_timer" not in st.session_state:
        st.session_state.start_timer = False

    if rutina_seleccionada == "Libre":
        grupo_muscular_libre = st.selectbox("Grupo Muscular", list(EXERCISE_CATALOG.keys()))
        with st.form("workout_form", clear_on_submit=True):
            ejercicio = st.selectbox("Ejercicio", EXERCISE_CATALOG[grupo_muscular_libre])
            
            c1, c1b, c2 = st.columns([2, 1, 2])
            with c1:
                peso = st.number_input("Peso", min_value=0.0, step=2.5, format="%.1f")
            with c1b:
                unidad_libre = st.selectbox("Unidad", ["Kg", "Lbs"], index=0 if UNIDAD_GLOBAL=="Kg" else 1)
            with c2:
                reps = st.number_input("Reps", min_value=0, step=1, value=10)
                
            notas = st.text_area("Notas (RPE, sensaciones...)", height=80)
            
            submitted = st.form_submit_button("LOG SET 📝", use_container_width=True)
            
            if submitted:
                if save_workout(ejercicio, peso, reps, notas, unidad_libre):
                    st.success(f"✅ Guardado: {ejercicio} - {peso}{unidad_libre} x {reps}")
                    st.session_state.start_timer = True # Trigger timer on save
    else:
        routine_exercises = routines[rutina_seleccionada]
        with st.form(f"routine_form_{rutina_seleccionada}", clear_on_submit=False):
            routine_results = {}
            for i, ex_name in enumerate(routine_exercises):
                sets_count = 3
                reps_meta = []
                
                st.markdown(f"**{i+1}. {ex_name}**")
                
                initial_data = []
                for s in range(sets_count):
                    meta_str = f"{reps_meta[s]} reps" if s < len(reps_meta) else "-"
                    initial_data.append({
                        "Set": s + 1,
                        "Meta": meta_str,
                        "Peso": 0.0,
                        "Unidad": UNIDAD_GLOBAL,
                        "Reps": 0,
                        "Notas": ""
                    })
                
                df_initial = pd.DataFrame(initial_data)
                
                edited_df = st.data_editor(
                    df_initial,
                    column_config={
                        "Set": st.column_config.NumberColumn(disabled=True),
                        "Meta": st.column_config.TextColumn(disabled=True),
                        "Peso": st.column_config.NumberColumn(min_value=0.0, step=2.5, format="%.1f"),
                        "Unidad": st.column_config.SelectboxColumn(options=["Kg", "Lbs"], default=UNIDAD_GLOBAL),
                        "Reps": st.column_config.NumberColumn(min_value=0, step=1)
                    },
                    hide_index=True,
                    key=f"editor_{rutina_seleccionada}_{i}",
                    use_container_width=True
                )
                routine_results[ex_name] = edited_df
                st.write("") # spacing
                
            submitted_routine = st.form_submit_button("FINALIZAR Y GUARDAR RUTINA 💾", use_container_width=True)
            if submitted_routine:
                id_sesion = datetime.now().strftime("%Y%m%d%H%M%S")
                all_sets = []
                for ex_name, df_res in routine_results.items():
                    valid_sets = df_res[(df_res['Peso'] > 0) | (df_res['Reps'] > 0)]
                    for _, row in valid_sets.iterrows():
                        all_sets.append({
                            'Ejercicio': ex_name,
                            'Peso': row['Peso'],
                            'Unidad': row.get('Unidad', UNIDAD_GLOBAL),
                            'Reps': row['Reps'],
                            'Notas': row['Notas'] if pd.notna(row['Notas']) else ''
                        })
                
                if all_sets:
                    save_routine(rutina_seleccionada, id_sesion, all_sets)
                    st.success(f"✅ Rutina '{rutina_seleccionada}' guardada con éxito.")
                    st.session_state.start_timer = True
                else:
                    st.warning("⚠️ No se registraron sets (todos tenían 0 peso y 0 reps).")
                
    # --- Rest Timer Section ---
    st.divider()
    st.subheader("⏱️ Temporizador de Descanso")
    
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        rest_time = st.number_input("Segundos", min_value=10, max_value=300, value=90, step=10)
    with col_t2:
        # Minimalist approach: basic Streamlit button formatting used instead of CSS injection
        
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
                        
                    # Get saved unit to format correctly
                    uni_historica = row.get('Unidad', "Kg")
                    if pd.isna(uni_historica): uni_historica = "Kg"
                        
                    rotulo_rutina = row.get('Rutina_Nombre', 'Legacy')
                    if pd.isna(rotulo_rutina): rotulo_rutina = "Libre"
                        
                    with st.container(border=True):
                        st.markdown(f"**{row['Ejercicio']}** _({rotulo_rutina})_")
                        st.markdown(f"⚖️ {row['Peso']} {uni_historica} x {row['Reps']} reps | 🎯 1RM Est: {rm_est:.1f} {uni_historica}")
                        st.caption(f"{fecha_str} | {row['Notas']}")
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
            yaxis=dict(title=f'Peso ({UNIDAD_GLOBAL})', title_font=dict(color='#00FFFF'), tickfont=dict(color='#00FFFF'), gridcolor='#1A1D24'),
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
                yaxis=dict(title=f"Volumen ({UNIDAD_GLOBAL})", gridcolor='#1A1D24', tickfont=dict(color='#E0E0CE')),
                title_font=dict(color="#E0E0CE")
            )
            
            # Reduce brightness of bars a bit to fit dark theme, or add borders
            fig_vol.update_traces(marker_line_width=1, marker_line_color='#0E1117')
            
            st.plotly_chart(fig_vol, use_container_width=True)
        else:
            st.info("No hay datos de entrenamiento suficientes para mostrar el volumen semanal.")
    else:
        st.info("Registra algunos sets de entrenamiento para ver tu volumen semanal.")

    st.divider()
    
    # --- Gráfico 3: Volumen Histórico por Rutina ---
    st.subheader("Evolución de Volumen por Rutina")
    if not df_train.empty and 'Rutina_Nombre' in df_train.columns:
        rutinas_disponibles = [r for r in df_train['Rutina_Nombre'].unique() if r not in ["Legacy", "Libre"] and pd.notna(r)]
        
        if rutinas_disponibles:
            rutina_filtro = st.selectbox("Seleccionar Rutina", rutinas_disponibles)
            df_rutina = df_train[df_train['Rutina_Nombre'] == rutina_filtro].copy()
            
            if not df_rutina.empty:
                df_rutina['Fecha'] = pd.to_datetime(df_rutina['Fecha'])
                df_rutina['Día'] = df_rutina['Fecha'].dt.date
                df_rutina['Volumen'] = df_rutina['Peso'] * df_rutina['Reps']
                
                volumen_por_sesion = df_rutina.groupby('Día')['Volumen'].sum().reset_index()
                
                fig_rutina = px.line(
                    volumen_por_sesion, 
                    x='Día', 
                    y='Volumen',
                    title=f"Volumen Total Levantado: {rutina_filtro}",
                    markers=True
                )
                
                fig_rutina.update_traces(line=dict(color='#FF00FF', width=3), marker=dict(size=8, color='#FF00FF', line=dict(width=1, color='#0E1117')))
                fig_rutina.update_layout(
                    margin=dict(l=0, r=0, t=40, b=0),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(title="", gridcolor='#1A1D24', tickfont=dict(color='#E0E0CE')),
                    yaxis=dict(title=f"Volumen ({UNIDAD_GLOBAL})", gridcolor='#1A1D24', tickfont=dict(color='#E0E0CE')),
                    title_font=dict(color="#E0E0CE")
                )
                
                st.plotly_chart(fig_rutina, use_container_width=True)
            else:
                st.info("No hay datos suficientes para esta rutina.")
        else:
            st.info("Completa una rutina guardada para ver su evolución.")
    else:
        st.info("No hay datos de rutinas registrados aún.")

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

with tab5:
    st.header("⚙️ Configuraciones Generales")
    st.subheader("Preferencias de la App")
    
    nueva_unidad = st.selectbox(
        "Unidad de Peso Preferida (Global)", 
        ["Kg", "Lbs"], 
        index=0 if UNIDAD_GLOBAL == "Kg" else 1,
        help="Los históricos y gráficos se mostrarán en esta unidad. Si pesas en la otra, la app hará la conversión por ti."
    )
    
    if nueva_unidad != UNIDAD_GLOBAL:
        APP_CONFIG["unidad_preferida"] = nueva_unidad
        save_config(APP_CONFIG)
        st.success(f"Preferencia guardada: {nueva_unidad}. Aplica en el próximo reinicio o interacción.")
        st.rerun()
        
    st.divider()
    
    st.header("Gestión de Diccionario de Ejercicios")
    st.write("Añade nuevos ejercicios o gestiona los que ya no utilices. Los cambios se reflejarán instantáneamente en la pestaña de Entrenamiento.")
    
    with st.form("add_exercise_form", clear_on_submit=True):
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            nuevo_ejercicio = st.text_input("Nombre del Ejercicio", placeholder="Ej: Hip Thrust")
        with col_e2:
            grupos_existentes = sorted(list(EXERCISE_CATALOG.keys()))
            grupo_sel = st.selectbox("Grupo Muscular", grupos_existentes + ["Otro..."])
            nuevo_grupo = st.text_input("Si elegiste 'Otro...', especifica:")
            
        submit_ejercicio = st.form_submit_button("Añadir Ejercicio ➕", use_container_width=True)
        
        if submit_ejercicio and nuevo_ejercicio:
            target_group = nuevo_grupo if grupo_sel == "Otro..." and nuevo_grupo else grupo_sel
            if target_group == "Otro..." and not nuevo_grupo:
                st.error("Por favor, especifica el nuevo grupo muscular.")
            else:
                save_new_exercise(nuevo_ejercicio, target_group)
                st.success(f"Ejercicio '{nuevo_ejercicio}' añadido al grupo '{target_group}'.")
                st.rerun()
                
    st.divider()
    st.subheader("Catálogo Actual")
    
    if os.path.exists(EXERCISES_FILE):
        df_ej = pd.read_csv(EXERCISES_FILE)
        df_ej = df_ej.sort_values(by=["Grupo Muscular", "Nombre del Ejercicio"])
        
        st.write("💡 Selecciona una fila para eliminarla (selecciona a la izquierda y presiona tecla Delete/Retroceso) o modifica el texto. Presiona 'Guardar Cambios' para aplicar.")
        edited_ej = st.data_editor(
            df_ej,
            num_rows="dynamic",
            use_container_width=True,
            key="exercises_editor_table"
        )
        
        if st.button("Guardar Cambios 💾", type="primary"):
            edited_ej.to_csv(EXERCISES_FILE, index=False)
            st.success("Diccionario actualizado exitosamente.")
            st.rerun()

with tab6:
    st.header("Creador de Rutinas")
    st.write("Crea plantillas personalizadas agrupando ejercicios de tu diccionario.")
    
    with st.form("create_routine_form", clear_on_submit=True):
        rutina_nombre = st.text_input("Nombre de la Rutina", placeholder="Ej: Día de Empuje")
        
        # Flatten the catalog to a simple list for the multiselect
        all_exercises = []
        for v in EXERCISE_CATALOG.values():
            all_exercises.extend(v)
        all_exercises = sorted(all_exercises)
        
        ejercicios_seleccionados = st.multiselect("Ejercicios", all_exercises)
        
        submit_rutina = st.form_submit_button("Guardar Rutina 💾", use_container_width=True)
        
        if submit_rutina:
            if not rutina_nombre or not ejercicios_seleccionados:
                st.error("Por favor, ingresa un nombre y selecciona al menos un ejercicio.")
            else:
                save_routine_template(rutina_nombre, ejercicios_seleccionados)
                st.success(f"Rutina '{rutina_nombre}' guardada con éxito.")
                st.rerun()
                
    st.divider()
    st.subheader("Tus Rutinas Guardadas")
    
    rutinas_guardadas = load_routines()
    rutinas_filtradas = {k: v for k, v in rutinas_guardadas.items() if k != "Libre (Histórico)"}
    
    if rutinas_filtradas:
        for r_name, r_ejs in rutinas_filtradas.items():
            with st.container(border=True):
                col_r1, col_r2 = st.columns([4, 1])
                with col_r1:
                    st.markdown(f"**{r_name}**")
                    st.caption(", ".join(r_ejs))
                with col_r2:
                    if st.button("🗑️", key=f"del_rutina_{r_name}", use_container_width=True):
                        delete_routine_template(r_name)
                        st.rerun()
    else:
        st.info("No tienes rutinas personalizadas creadas aún.")

