import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os, json, requests
from datetime import datetime

# 設定頁面
st.set_page_config(page_title="高雄開發足跡地圖", layout="wide")
DATA_FILE = "visited_towns.csv"
GEOJSON_FILE = "town_fixed.json"
URL = "https://raw.githubusercontent.com/chaoyihuang/Taiwan-GeoJSON/master/town.json"

# 初始化資料檔
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["TOWNNAME", "COUNTYNAME", "visited_time"]).to_csv(DATA_FILE, index=False)

@st.cache_data
def get_geojson():
    if os.path.exists(GEOJSON_FILE):
        with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        resp = requests.get(URL, timeout=15)
        data = resp.json()
        with open(GEOJSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    
    for feature in data['features']:
        p = feature['properties']
        p['C'] = p.get('COUNTYNAME') or p.get('C_Name') or '未知'
        p['T'] = p.get('TOWNNAME') or p.get('T_Name') or '未知'
    return data

st.title("🗺️ 台灣鄉鎮市區足跡地圖")
visited_df = pd.read_csv(DATA_FILE)
geojson_data = get_geojson()

if geojson_data:
    # 建立地圖
    m = folium.Map(location=[22.62, 120.30], zoom_start=11, tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')

    def style_f(f):
        t, c = f['properties']['T'], f['properties']['C']
        is_v = ((visited_df['TOWNNAME'] == t) & (visited_df['COUNTYNAME'] == c)).any()
        return {'fillColor': '#FF8C00' if is_v else '#FFFFFF', 'color': 'white', 'weight': 1, 'fillOpacity': 0.6 if is_v else 0.1}

    folium.GeoJson(geojson_data, style_function=style_f, tooltip=folium.GeoJsonTooltip(fields=['C', 'T'], aliases=['縣市:', '鄉鎮:'])).add_to(m)

    # 渲染地圖
    output = st_folium(m, width="100%", height=500, key="taiwan_map")

    # 點擊處理
    if output and output.get("last_object_clicked_tooltip"):
        try:
            info = output["last_object_clicked_tooltip"]
            c_name = info.split(',')[0].split(':')[-1].strip()
            t_name = info.split(',')[1].split(':')[-1].strip()
            st.write("---")
            st.subheader(f"📍 當前選取：{c_name} {t_name}")
            if st
