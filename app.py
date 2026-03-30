import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime
import os

# --- 基礎配置 ---
st.set_page_config(page_title="我的足跡地圖", layout="centered", initial_sidebar_state="collapsed")
DATA_FILE = "footprints.csv"

# 初始化資料檔
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["name", "lat", "lon", "time"]).to_csv(DATA_FILE, index=False)

def load_data():
    return pd.read_csv(DATA_FILE)

def save_point(name, lat, lon):
    df = load_data()
    new_data = pd.DataFrame([[name, lat, lon, datetime.now().strftime("%Y-%m-%d %H:%M")]], 
                            columns=["name", "lat", "lon", "time"])
    pd.concat([df, new_data], ignore_index=True).to_csv(DATA_FILE, index=False)

# --- 主介面 ---
st.title("📍 衛星雲端踩點 App")

# 1. GPS 自動定位功能 (手機開啟時會要求權限)
st.subheader("🚀 快速打卡")
loc = streamlit_js_eval(js_expressions="target.geolocation.getCurrentPosition(x => x.coords)", want_output=True)

with st.expander("展開打卡表單", expanded=True):
    loc_name = st.text_input("地點名稱 (例如：某某建案、私房景點)")
    
    if loc:
        curr_lat = loc['latitude']
        curr_lon = loc['longitude']
        st.info(f"當前 GPS：{curr_lat:.6f}, {curr_lon:.6f}")
        
        if st.button("確認踩點", use_container_width=True):
            if loc_name:
                save_point(loc_name, curr_lat, curr_lon)
                st.success(f"✅ {loc_name} 踩點成功！")
                st.rerun()
            else:
                st.error("請輸入地點名稱")
    else:
        st.warning("正在取得 GPS 定位中... 請確保手機已開啟定位權限。")

# 2. 地圖顯示區域
st.subheader("🗺️ 我的足跡地圖")
df_display = load_data()

# 設定地圖中心點（預設在高雄）
center = [22.62, 120.30] if df_display.empty else [df_display.iloc[-1]['lat'], df_display.iloc[-1]['lon']]

# 建立地圖：使用 Google 衛星混合圖
m = folium.Map(
    location=center, 
    zoom_start=15,
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', # Google Hybrid (衛星+路名)
    attr='Google'
)

# 加入底圖切換器（讓你隨時換回標準地圖）
folium.TileLayer('openstreetmap', name='標準地圖').add_to(m)
folium.LayerControl().add_to(m)

# 標記所有踩點位置
for _, row in df_display.iterrows():
    folium.Marker(
        [row['lat'], row['lon']], 
        popup=f"{row['name']}<br>{row['time']}",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

# 渲染地圖至 Streamlit
st_folium(m, width="100%", height=500)

# 3. 數據清單
if not df_display.empty:
    with st.expander("查看歷史足跡清單"):
        st.dataframe(df_display.sort_values(by="time", ascending=False), use_container_width=True)
