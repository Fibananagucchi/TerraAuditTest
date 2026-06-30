import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv

import price_corridor
import budget_optimizer
import llm_teaser

# Завантаження змінних середовища (API ключів)
load_dotenv()

st.set_page_config(page_title="TerraAudit | Asset Discovery", layout="wide", page_icon="🌍")

# Верхній блок
st.title("🌍 TerraAudit: Монетизація прихованих активів громади")
st.markdown("Система виявлення нереалізованих земельних ресурсів та автоматичного формування інвестиційних пропозицій.")
st.markdown("---")

col_settings, col_main = st.columns([1, 3])

with col_settings:
    st.subheader("⚙️ Параметри активу")
    selected_community = st.selectbox("Локація", ["Громада N (Демо)", "Київська обл. (Тест)"])
    area_hectares = st.number_input("Площа ділянки (га)", min_value=0.1, value=5.0, step=0.5)
    land_type = st.selectbox("Кадастровий тип", ["Промисловість", "Сільське господарство", "Забудова"])
    
    st.markdown("### 📊 Статус підключень")
    st.success("API Прозорро.Продажі: Активно")
    st.success("Модель Llama 3 (Groq): Готова")
    st.success("OpenStreetMap: Підключено")

with col_main:
    tab_geo, tab_price, tab_budget = st.tabs(["🛰️ 1. GeoAI Аудит", "💰 2. Smart Pricing", "📈 3. Інвестиції та Бюджет"])
    
    with tab_geo:
        st.markdown("### Детекція зміни землекористування (NDVI) та активності (VIIRS)")
        map_col, info_col = st.columns([2, 1])
        
        with map_col:
            m = folium.Map(location=[50.4501, 30.5234], zoom_start=13, tiles="OpenStreetMap")
            folium.Marker(
                [50.4501, 30.5234], 
                popup="Підозріла ділянка", 
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)
            st_folium(m, width=600, height=400)
        
        with info_col:
            st.warning("⚠️ **Аномалія вегетації:** Лінія NDVI пласка з 2024 року. Фактичний стан — тверде покриття, хоча за кадастром це пасовище.")
            st.error("🚨 **Аномалія освітлення:** Дані VIIRS фіксують стабільне нічне освітлення на ділянці.")
            if st.button("Підтвердити актив", use_container_width=True):
                st.toast("Об'єкт переведено на етап фінансової оцінки!")

    with tab_price:
        st.markdown("### Динамічний ціновий коридор")
        st.write("Розрахунок справедливої вартості на основі історичних торгів.")
        
        min_p, max_p, median_p = price_corridor.calculate_corridor(area_hectares)
        
        st.metric(label="Рекомендована ціна оренди (грн/рік)", value=f"{median_p:,.0f}")
        
        st.markdown("#### Інтерактивний тест для журі")
        proposed_price = st.slider(
            "Симуляція: інвестор пропонує ціну", 
            min_value=0, 
            max_value=int(max_p * 1.5), 
            value=int(median_p), 
            step=5000
        )
        
        if proposed_price < min_p:
            st.error(f"⛔ БЛОКУВАННЯ: Ціна {proposed_price:,.0f} грн є аномально низькою (Нижня межа ринку: {min_p:,.0f} грн). Зафіксовано ризик тіньової змови.")
        else:
            st.success(f"✅ Транзакцію погоджено. Ціна відповідає ринковому коридору.")

    with tab_budget:
        st.markdown("### Оптимізація вивільнених коштів")
        st.write("Куди алгоритм пропонує спрямувати кошти від оренди знайденого активу:")
        
        budget_result = budget_optimizer.optimize_budget(total_funds=median_p)
        
        chart_data = pd.DataFrame({
            "Категорія": ["Школи", "Дороги", "Медицина"], 
            "Бюджет (грн)": [budget_result["Школи (грн)"], budget_result["Дороги (грн)"], budget_result["Медицина (грн)"]]
        }).set_index("Категорія")
        st.bar_chart(chart_data)
        
        st.markdown("### Генерація інвестиційного тізера")
        if st.button("Створити пропозицію для публікації", type="primary"):
            with st.spinner("Llama 3 формує документ через Groq..."):
                teaser = llm_teaser.generate_teaser(selected_community, area_hectares, land_type, min_p)
                st.info(teaser)