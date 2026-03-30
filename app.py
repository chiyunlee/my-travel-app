import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import json
from datetime import datetime

st.set_page_config(page_title="除錯診斷地圖", layout="wide")
GEOJSON_FILE = os.path.join(os.path.dirname(__file__), "town.json")

# --- 診斷區域：直接印出 JSON 結構 ---
st.subheader("🛠️ 檔案欄位診斷")
if os.path.exists(GEOJSON_FILE):
    with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
        try:
            temp_data = json.load(f)
            first_feature_props = temp_data['features'][0]['properties']
            st.write("偵測到您的 JSON 檔案欄位如下：")
            st.code(list(first_feature_props.keys()))
            st.write("第一個物件內容範例：", first_feature_props)
        except Exception as e:
            st.error(f"JSON 解析失敗：{e}")
else:
    st.error("找不到 town.json")

# --- 核心邏輯 (加入更多預期欄位) ---
@st.cache_data
def get_local_geojson():
    if os.path.exists(GEOJSON_FILE):
        with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for feature in data['features']:
                p = feature['properties']
                # 這裡涵蓋了台灣常見 GeoJSON 的所有可能欄位名
                p['FINAL_TOWN'] = p.get('TOWNNAME') or p.get('T_Name') or p.get('townname') or p.get('TOWN') or '未知'
                p['FINAL_COUNTY'] = p.get('COUNTYNAME') or p.get('C_Name') or p.get('countyname') or p.get('COUNTY') or '未知'
            return data
    return None

geojson_data = get_local_geojson()
if geojson_data:
    m = folium.Map(location=[22.62, 120.30], zoom_start=11, tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')
    
    folium.GeoJson(
        geojson_data,
        style_function=lambda x: {'fillColor': 'white', 'color': 'orange', 'weight': 1, 'fillOpacity': 0.1},
        tooltip=folium.GeoJsonTooltip(fields=['FINAL_COUNTY', 'FINAL_TOWN'], aliases=['縣市:', '鄉鎮:'])
    ).add_to(m)

    out = st_folium(m, width="100%", height=400, key="debug_map")

    # 點擊除錯資訊
    if out.get("last_object_clicked_tooltip"):
        st.success(f"抓取到 Tooltip 資訊：{out['last_object_clicked_tooltip']}")
    elif out.get("last_active_drawing"):
        st.write("抓取到 Drawing 屬性：", out["last_active_drawing"].get("properties"))
