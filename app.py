import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Настройка страницы
st.set_page_config(
    page_title="TrafficFlow AI — Алматы",
    page_icon="🚦",
    layout="wide"
)

# Кастомные стили (Темная тема)
st.markdown("""
    <style>
    .main {
        background-color: #030712;
        color: #f8fafc;
    }
    .stMetric {
        background-color: #0f172a;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #1e293b;
    }
    </style>
""", unsafe_allow_html=True)

# Заголовок
st.title("🚦 TrafficFlow AI — Прогноз плотности транспортного потока г. Алматы")
st.markdown("Интерактивная аналитическая система мониторинга и ИИ-моделирования трафика на перекрестках")

# Боковая панель (Навигация)
st.sidebar.header("🎛️ Меню управления")
tab = st.sidebar.radio("Выберите раздел:", ["🗺️ Мониторинг узлов", "🤖 ИИ-Симулятор", "📊 Аналитика & Smart TL"])

# Генерация данных перекрестков Алматы
@st.cache_data
def load_intersections():
    streets = [
        'пр. Аль-Фараби / ул. Достык', 'пр. Абая / ул. Сейфуллина', 
        'пр. Райымбека / ул. Суюнбая', 'ул. Саина / пр. Абая', 
        'пр. Аль-Фараби / ул. Розыбакиева (ТРЦ Mega)', 'пр. Достык / ул. Жолдасбекова (Dostyk Plaza)', 
        'ул. Толе би / ул. Байтурсынова', 'пр. Рыскулова / ул. Кудерина', 
        'пр. Абылай хана / ул. Гоголя', 'ул. Тимирязева / ул. Ауэзова', 
        'ВОАД / ул. Халиуллина', 'пр. Сейфуллина / ул. Макатаева (ТРЦ MEGA Park)'
    ]
    np.random.seed(42)
    data = []
    for i in range(1, 46):
        name = streets[(i - 1) % len(streets)] + (f" (Узел #{i})" if i > len(streets) else "")
        lanes = np.random.choice([4, 6, 8])
        has_smart_tl = np.random.choice([True, False], p=[0.65, 0.35])
        mall_dist = np.random.randint(100, 2800)
        
        density = int(1200 + (8 - lanes) * 250 + np.random.randint(0, 800))
        if mall_dist < 500:
            density += int(900 + np.random.randint(0, 600))
        if has_smart_tl:
            density = int(density * 0.78)
            
        status = "Критический затор" if density > 2600 else ("Плотный поток" if density > 1800 else "Свободно")
        
        data.append({
            "ID": 100 + i,
            "Название": name,
            "Полосы": lanes,
            "Smart TL": "Активен" if has_smart_tl else "Отсутствует",
            "Расстояние до ТРЦ (м)": mall_dist,
            "Плотность (авто/ч)": density,
            "Задержка (сек)": int(density / 30 + (12 if has_smart_tl else 45)),
            "Скорость (км/ч)": max(10, int(70 - (density / 60))),
            "Статус": status
        })
    return pd.DataFrame(data)

df_nodes = load_intersections()

# ==================== РАЗДЕЛ 1: МОНИТОРИНГ УЗЛОВ ====================
if tab == "🗺️ Мониторинг узлов":
    st.subheader("🏙️ Мониторинг дорожной сети Алматы")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        lane_filter = st.selectbox("Фильтр по полосам:", ["Все", 4, 6, 8])
    with col2:
        smart_filter = st.selectbox("Умные светофоры:", ["Все", "Активен", "Отсутствует"])
    with col3:
        mall_filter = st.selectbox("Близость к ТРЦ:", ["Все", "Вблизи (< 500м)", "Удалено (> 500м)"])
        
    filtered_df = df_nodes.copy()
    if lane_filter != "Все":
        filtered_df = filtered_df[filtered_df["Полосы"] == lane_filter]
    if smart_filter != "Все":
        filtered_df = filtered_df[filtered_df["Smart TL"] == smart_filter]
    if mall_filter == "Вблизи (< 500м)":
        filtered_df = filtered_df[filtered_df["Расстояние до ТРЦ (м)"] < 500]
    elif mall_filter == "Удалено (> 500м)":
        filtered_df = filtered_df[filtered_df["Расстояние до ТРЦ (м)"] >= 500]
        
    st.markdown(f"**Найдено узлов:** {len(filtered_df)}")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# ==================== РАЗДЕЛ 2: ИИ-СИМУЛЯТОР ====================
elif tab == "🤖 ИИ-Симулятор":
    st.subheader("🧠 Параметрический ИИ-симулятор плотности потока")
    
    col_ctrl, col_res = st.columns(2)
    
    with col_ctrl:
        st.markdown("### Настройка параметров")
        sim_lanes = st.slider("Количество полос движения", 2, 8, 4)
        sim_hour = st.slider("Время суток (Час)", 0, 23, 8)
        sim_mall = st.slider("Расстояние до ТРЦ (м)", 100, 3000, 300, 50)
        sim_smart = st.toggle("Умные светофоры (Smart TL)", value=True)
        
    # Расчет регрессионной модели
    time_factor = 1.75 if (7 <= sim_hour <= 9 or 17 <= sim_hour <= 19) else (1.15 if 10 <= sim_hour <= 16 else 0.4)
    mall_factor = 1.5 if sim_mall <= 300 else (1.28 if sim_mall <= 800 else 1.0)
    
    base_density = (3200 / sim_lanes) * time_factor * mall_factor
    if sim_smart:
        base_density *= 0.75
        
    total_density = int(base_density)
    density_index = min(10.0, max(1.0, round(total_density / 400, 1)))
    delay_sec = int(density_index * 4.0 + (6 if sim_smart else 28))
    speed_kmh = max(10, int(70 - density_index * 5.5))
    
    with col_res:
        st.markdown("### Результаты прогноза")
        m1, m2 = st.columns(2)
        m1.metric("Плотность потока", f"{total_density:,} авто/ч")
        m2.metric("Индекс загруженности", f"{density_index} / 10")
        
        st.markdown(f"**Задержка транспорта:** {delay_sec} сек")
        st.markdown(f"**Скорость потока:** {speed_kmh} км/ч")
        
        # Суточный график
        hours = list(range(24))
        profile = []
        for h in hours:
            tf = 1.75 if (7 <= h <= 9 or 17 <= h <= 19) else (1.15 if 10 <= h <= 16 else 0.4)
            val = (3100 / sim_lanes) * tf * mall_factor
            if sim_smart:
                val *= 0.75
            profile.append(int(val))
            
        fig = px.line(x=[f"{h:02d}:00" for h in hours], y=profile, labels={"x": "Время", "y": "авто/ч"}, title="Суточный профиль трафика Алматы")
        fig.update_layout(template="plotly_dark", height=250, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

# ==================== РАЗДЕЛ 3: АНАЛИТИКА ====================
elif tab == "📊 Аналитика & Smart TL":
    st.subheader("📈 Анализ эффективности умных светофоров в Алматы")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Задержка транспорта («До» и «После» Smart TL)")
        eff_df = pd.DataFrame({
            "Время": ["Утро (08:30)", "День (14:00)", "Вечер (18:30)", "Ночь (02:00)"],
            "Без Smart TL": [92, 55, 105, 22],
            "С Smart TL (ИИ)": [52, 32, 58, 14]
        })
        fig_bar = px.bar(eff_df, x="Время", y=["Без Smart TL", "С Smart TL (ИИ)"], barmode="group", template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col2:
        st.markdown("#### Влияние факторов на пробки Алматы")
        radar_df = pd.DataFrame({
            "Фактор": ["Число полос", "Время суток", "Близость ТРЦ", "Умный светофор", "Ширина проезжей части"],
            "Влияние (%)": [88, 98, 85, 92, 80]
        })
        fig_radar = px.line_polar(radar_df, r="Влияние (%)", theta="Фактор", line_close=True, template="plotly_dark")
        fig_radar.update_traces(fill="toself")
        st.plotly_chart(fig_radar, use_container_width=True)
        
    st.info("💡 **Рекомендация ИИ:** В радиусе до 300 м от ТРЦ Mega и Dostyk Plaza внедрение адаптивных светофоров сокращает заторы в часы пик в среднем на 28%.")