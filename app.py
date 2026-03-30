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
GEOJSON_FILE = "town.json"
# 正確的台灣鄉鎮 GeoJSON 原始資料網址
RAW_GEOJSON_URL = "https://raw.githubusercontent.com/g0v/tw-town-geojson/master/town.json"

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

@st.cache_data(show_spinner="正在載入地圖數據（初次載入約需 10 秒）...")
def get_geojson():
    # 邏輯：如果本地檔案無效或不存在，就重新下載
    need_download = True
    if os.path.exists(GEOJSON_FILE):
        try:
            with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'features' in data:
                    need_download = False
                    # 預處理欄位
                    for feature in data['features']:
                        p = feature['properties']
                        p['C_NAME'] = p.get('COUNTYNAME', '未知')
                        p['T_NAME'] = p.get('TOWNNAME', '未知')
                    return data
        except:
            need_download = True

    if need_download:
        try:
            resp = requests.get(RAW_GEOJSON_URL)
            data = resp.json()
            # 存檔供下次使用
            with open(GEOJSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            for feature in data['features']:
                p = feature['properties']
                p['C_NAME'] = p.get('COUNTYNAME', '未知')
                p['T_NAME'] = p.get('TOWNNAME', '未知')
            return data
        except Exception as e:
            st.error(f"地圖下載失敗：{e}")
            return None

# --- 主介面 ---
st.title("🗺️ 台灣鄉鎮市區足跡地圖")

visited_df = load_data()
geojson_data = get_geojson()

if geojson_data:
    m = folium.Map(
        location=[22.62, 120.30], 
        zoom_start=11, 
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
        attr='Google'
    )

    def style_func(feature):
        t = feature['properties']['T_NAME']
        c = feature['properties']['C_NAME']
        is_visited = ((visited_df['TOWNNAME'] == t) & (visited_df['COUNTYNAME'] == c)).any()
        return {
            'fillColor': '#FF8C00' if is_visited else '#FFFFFF',
            'color': '#FF8C00' if is_visited else 'white',
            'weight': 1.5,
            'fillOpacity': 0.6 if is_visited else 0.1,
        }

    folium.GeoJson(
        geojson_data,
        style_function=style_func,
        tooltip=folium.GeoJsonTooltip(fields=['C_NAME', 'T_NAME'], aliases=['縣市:', '鄉鎮:'])
    ).add_to(m)

    output = st_folium(m, width="100%", height=500, key="taiwan_map")

    st.write("---")
    
    # 點擊處理
    selected_t, selected_c = None, None
    if output.get("last_object_clicked_tooltip"):
        try:
            info = output["last_object_clicked_tooltip"]
            parts = info.split(',')
            selected_c = parts[0].split(':')[-1].strip()
            selected_t = parts[1].split(':')[-1].strip()
        except: pass

    if selected_t and selected_t != "未知":
        st.subheader(f"📍 您選取了：{selected_c} {selected_t}")
        if st.button(f"🚩 確認在 {selected_t} 打卡", use_container_width=True):
            if save_visit(selected_t, selected_c):
                st.success(f"紀錄成功！{selected_t} 已點亮。")
                st.balloons()
                st.rerun()
    else:
        st.info("👆 **請在地圖上點擊妳去過的區域**（例如點一下鳳山市區的色塊）。")

    st.write("---")
    st.metric("已解鎖鄉鎮數量", f"{len(visited_df)} / 368")
    if not visited_df.empty:
        with st.expander("查看我的足跡清單"):
            st.dataframe(visited_df.sort_values(by="visited_time", ascending=False), use_container_width=True)
