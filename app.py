import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import json
import requests
from datetime import datetime

# --- 基礎配置 ---
st.set_page_config(page_title="高雄開發足跡地圖", layout="wide")
DATA_FILE = "visited_towns.csv"
GEOJSON_FILE = "town_fixed.json"
RAW_GEOJSON_URL = "https://raw.githubusercontent.com/chaoyihuang/Taiwan-GeoJSON/master/town.json"

# 初始化資料
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["TOWNNAME", "COUNTYNAME", "visited_time"]).to_csv(DATA_FILE, index=False)

@st.cache_data
def get_geojson():
    # 優先讀取本地，失敗則線上下載
    if os.path.exists(GEOJSON_FILE):
        try:
            with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for feature in data['features']:
                    p = feature['properties']
                    p['C_NAME'] = p.get('COUNTYNAME') or p.get('C_Name') or '未知'
                    p['T_NAME'] = p.get('TOWNNAME') or p.get('T_Name') or '未知'
                return data
        except: pass

    try:
        resp = requests.get(RAW_GEOJSON_URL, timeout=15)
        data = resp.json()
        with open(GEOJSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        for feature in data['features']:
            p = feature['properties']
            p['C_NAME'] = p.get('COUNTYNAME') or p.get('C_Name') or '未知'
            p['T_NAME'] = p.get('TOWNNAME') or p.get('T_Name') or '未知'
        return data
    except:
        return None

# --- 主程式 ---
st.title("🗺️ 台灣鄉鎮市區足跡地圖")

visited_df = pd.read_csv(DATA_FILE)
geojson_data = get_geojson()

if geojson_data:
    # 建立地圖：中心設在高雄
    m = folium.Map(
        location=[22.62, 120.30], 
        zoom_start=11, 
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
        attr='Google'
    )

    # 樣式設定
    def style_func(feature):
        t = feature['properties']['T_NAME']
        c = feature['properties']['C_NAME']
        is_visited = ((visited_df['TOWNNAME'] == t) & (visited_df['COUNTYNAME'] == c)).any()
        return {
            'fillColor': '#FF8C00' if is_visited else '#FFFFFF',
            'color': 'white',
            'weight': 1,
            'fillOpacity': 0.6 if is_visited else 0.1,
        }

    folium.GeoJson(
        geojson_data,
        style_function=style_func,
        tooltip=folium.GeoJsonTooltip(fields=['C_NAME', 'T_NAME'], aliases=['縣市:', '鄉鎮:'])
    ).add_to(m)

    # 顯示地圖
    output = st_folium(m
