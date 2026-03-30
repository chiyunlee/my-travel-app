import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import os

# --- 配置與資料初始化 ---
DATA_FILE = "my_footprints.csv"

# 如果檔案不存在，建立一個空的資料表
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["name", "lat", "lon", "time"])
    df.to_csv(DATA_FILE, index=False)

def load_data():
    return pd.read_csv(DATA_FILE)

def save_point(name, lat, lon):
    df = load_data()
    new_data = pd.DataFrame([[name, lat, lon, datetime.now().strftime("%Y-%m-%d %H:%M")]], 
                            columns=["name", "lat", "lon", "time"])
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

# --- UI 介面 ---
st.set_page_config(page_title="我的足跡地圖", layout="centered")
st.title("📍 極簡旅行踩點")

# 1. 側邊欄：手動輸入踩點資訊
with st.sidebar:
    st.header("新增踩點")
    loc_name = st.text_input("地點名稱", placeholder="例如：駁二特區")
    # 簡易版先手動輸入，進階版可抓取瀏覽器 GPS
    lat = st.number_input("緯度 (Lat)", value=22.627, format="%.4f")
    lon = st.number_input("經度 (Lon)", value=120.301, format="%.4f")
    
    if st.button("確認打卡"):
        if loc_name:
            save_point(loc_name, lat, lon)
            st.success(f"已記錄：{loc_name}")
            st.rerun()

# 2. 主畫面：顯示地圖
df_display = load_data()
st.subheader(f"目前足跡：共 {len(df_display)} 個地點")

# 建立地圖中心點（預設以最後一個點為中心）
center = [22.62, 120.30] if df_display.empty else [df_display.iloc[-1]['lat'], df_display.iloc[-1]['lon']]
m = folium.Map(location=center, zoom_start=13)

# 將所有點標記在地圖上
for _, row in df_display.iterrows():
    folium.Marker(
        [row['lat'], row['lon']], 
        popup=f"{row['name']} ({row['time']})",
        icon=folium.Icon(color="red", icon="check")
    ).add_to(m)

st_folium(m, width=700, height=450)

# 3. 數據清單
if st.checkbox("顯示足跡清單"):
    st.table(df_display.sort_values(by="time", ascending=False))