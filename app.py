import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
from geopy.geocoders import Nominatim
from datetime import datetime
import os

# --- 基礎配置 ---
st.set_page_config(page_title="專業開發踩點 App", layout="centered")
DATA_FILE = "my_points.csv"
geolocator = Nominatim(user_agent="my_travel_app_v1")

# 初始化資料檔
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["name", "lat", "lon", "time"]).to_csv(DATA_FILE, index=False)

def load_data():
    return pd.read_csv(DATA_FILE)

def save_point(name, lat, lon):
    df = load_data()
    new_row = pd.DataFrame([[name, lat, lon, datetime.now().strftime("%Y-%m-%d %H:%M")]], 
                            columns=["name", "lat", "lon", "time"])
    pd.concat([df, new_row], ignore_index=True).to_csv(DATA_FILE, index=False)

# --- 主介面 ---
st.title("📍 智慧地標搜尋打卡")

# --- 第一部分：搜尋與定位 ---
st.subheader("🔍 尋找目的地")
search_query = st.text_input("輸入地址或地標 (例如：高雄展覽館)", placeholder="輸入後按 Enter 搜尋")

# 預設座標（若沒搜尋也沒定位，預設在高雄）
target_lat, target_lon = 22.62, 120.30
target_name = ""

if search_query:
    try:
        # 使用 geopy 進行地理編碼搜尋
        location = geolocator.geocode(search_query)
        if location:
            target_lat = location.latitude
            target_lon = location.longitude
            target_name = search_query
            st.success(f"找到位置：{location.address}")
        else:
            st.error("找不到該地點，請嘗試更詳細的地址。")
    except Exception as e:
        st.error(f"搜尋出錯：{e}")

# --- 第二部分：打卡功能 ---
with st.container():
    st.write("---")
    st.info(f"📍 準備打卡點：{target_name if target_name else '當前中心點'}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("緯度", f"{target_lat:.6f}")
    with col2:
        st.metric("經度", f"{target_lon:.6f}")

    if st.button("📌 在此位置打卡存檔", use_container_width=True):
        final_name = target_name if target_name else f"未命名地點_{datetime.now().strftime('%H%M')}"
        save_point(final_name, target_lat, target_lon)
        st.balloons()
        st.rerun()

# --- 第三部分：地圖顯示 (Google 衛星混合圖) ---
st.subheader("🗺️ 足跡地圖")
df_display = load_data()

# 建立地圖
m = folium.Map(
    location=[target_lat, target_lon], 
    zoom_start=17, 
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
    attr='Google'
)

# 標記「正在搜尋的點」 (藍色)
if search_query:
    folium.Marker(
        [target_lat, target_lon], 
        popup="搜尋目標",
        icon=folium.Icon(color="blue", icon="search")
    ).add_to(m)

# 標記「歷史已打卡的點」 (紅色)
for _, row in df_display.iterrows():
    folium.Marker(
        [row['lat'], row['lon']], 
        popup=f"{row['name']}<br>{row['time']}",
        icon=folium.Icon(color="red", icon="check")
    ).add_to(m)

st_folium(m, width="100%", height=450)

# 歷史清單
if st.checkbox("查看歷史打卡記錄"):
    st.dataframe(df_display.sort_values(by="time", ascending=False), use_container_width=True)
