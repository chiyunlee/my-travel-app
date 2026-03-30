import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import json
from datetime import datetime

# --- 基礎配置 ---
st.set_page_config(page_title="高雄開發足跡地圖", layout="wide")
DATA_FILE = "visited_towns.csv"
base_path = os.path.dirname(__file__)
GEOJSON_FILE = os.path.join(base_path, "town.json")

# 初始化已造訪紀錄
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["TOWNNAME", "COUNTYNAME", "visited_time"]).to_csv(DATA_FILE, index=False)

def load_data():
    return pd.read_csv(DATA_FILE)

def save_visit(town_name, county_name):
    df = load_data()
    if not ((df['TOWNNAME'] == town_name) & (df['COUNTYNAME'] == county_name)).any():
        new_row = pd.DataFrame([[town_name, county_name, datetime.now().strftime("%Y-%m-%d %H:%M")]], 
                                columns=["TOWNNAME", "COUNTYNAME", "visited_time"])
        pd.concat([df, new_row], ignore_index=True).to_csv(DATA_FILE, index=False)
        return True
    return False

@st.cache_data
def get_local_geojson():
    if os.path.exists(GEOJSON_FILE):
        with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # --- 強大掃描邏輯：自動對應縣市與鄉鎮欄位 ---
            for feature in data['features']:
                p = feature['properties']
                # 遍歷所有欄位，找尋包含 "TOWN" 或 "COUNTY" 的關鍵字
                t_val = "未知"
                c_val = "未知"
                for key, value in p.items():
                    k_upper = key.upper()
                    if "TOWN" in k_upper and t_val == "未知": t_val = value
                    if ("COUNTY" in k_upper or "CITY" in k_upper) and c_val == "未知": c_val = value
                
                p['FINAL_TOWN'] = t_val
                p['FINAL_COUNTY'] = c_val
            return data
    return None

# --- 主介面 ---
st.title("🗺️ 台灣鄉鎮市區足跡地圖")

visited_df = load_data()
geojson_data = get_local_geojson()

if geojson_data:
    m = folium.Map(
        location=[22.62, 120.30], 
        zoom_start=11, 
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
        attr='Google'
    )

    def style_func(feature):
        t = feature['properties']['FINAL_TOWN']
        c = feature['properties']['FINAL_COUNTY']
        is_visited = ((visited_df['TOWNNAME'] == t) & (visited_df['COUNTYNAME'] == c)).any()
        return {
            'fillColor': '#FF8C00' if is_visited else '#FFFFFF',
            'color': '#FF8C00' if is_visited else 'white',
            'weight': 2,
            'fillOpacity': 0.6 if is_visited else 0.1,
        }

    folium.GeoJson(
        geojson_data,
        style_function=style_func,
        tooltip=folium.GeoJsonTooltip(fields=['FINAL_COUNTY', 'FINAL_TOWN'], aliases=['縣市:', '鄉鎮:'])
    ).add_to(m)

    # 渲染地圖
    output = st_folium(m, width="100%", height=500, key="taiwan_map")

    # --- 點擊處理 ---
    st.write("---")
    
    selected_t = None
    selected_c = None

    # 優先從 tooltip 抓取資訊（這是最穩定的方式）
    if output.get("last_object_clicked_tooltip"):
        try:
            info = output["last_object_clicked_tooltip"]
            # 解析格式 "縣市: 高雄市, 鄉鎮: 苓雅區"
            parts = info.split(',')
            selected_c = parts[0].split(':')[-1].strip()
            selected_t = parts[1].split(':')[-1].strip()
        except:
            pass
    # 次要從 active_drawing 抓取
    elif output.get("last_active_drawing"):
        props = output["last_active_drawing"].get("properties", {})
        selected_t = props.get("FINAL_TOWN")
        selected_c = props.get("FINAL_COUNTY")

    if selected_t and selected_t != "未知":
        st.subheader(f"📍 您選取了：{selected_c} {selected_t}")
        if st.button(f"🚩 確認在 {selected_t} 打卡", use_container_width=True):
            if save_visit(selected_t, selected_c):
                st.success(f"紀錄成功！{selected_t} 已點亮。")
                st.balloons()
                st.rerun()
    else:
        st.info("👆 **請點擊地圖上的區塊**，按鈕就會出現囉！")

    # 進度統計
    st.write("---")
    st.metric("已解鎖鄉鎮數量", f"{len(visited_df)} 個區域")
    if not visited_df.empty:
        with st.expander("查看我的足跡清單"):
            st.write(visited_df.sort_values(by="visited_time", ascending=False))
else:
    st.error("❌ 找不到 town.json")
