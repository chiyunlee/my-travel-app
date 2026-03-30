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
            # 修正欄位偵測邏輯，解決「未知」問題
            for feature in data['features']:
                p = feature['properties']
                # 自動尋找可能的縣市與鄉鎮 Key (有些 JSON 是小寫，有些是 C_Name)
                p['TOWN'] = p.get('TOWNNAME') or p.get('townname') or p.get('T_Name') or '未知'
                p['COUNTY'] = p.get('COUNTYNAME') or p.get('countyname') or p.get('C_Name') or '未知'
            return data
    return None

# --- 主介面 ---
st.title("🗺️ 台灣鄉鎮市區足跡地圖")

visited_df = load_data()
geojson_data = get_local_geojson()

if geojson_data:
    # 建立地圖
    m = folium.Map(
        location=[22.62, 120.30], 
        zoom_start=11, 
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
        attr='Google'
    )

    # 設置塗色樣式
    def style_func(feature):
        t_name = feature['properties']['TOWN']
        c_name = feature['properties']['COUNTY']
        is_visited = ((visited_df['TOWNNAME'] == t_name) & (visited_df['COUNTYNAME'] == c_name)).any()
        
        return {
            'fillColor': '#FF8C00' if is_visited else '#FFFFFF',
            'color': '#FF8C00' if is_visited else 'white',
            'weight': 2 if is_visited else 1,
            'fillOpacity': 0.6 if is_visited else 0.1,
        }

    folium.GeoJson(
        geojson_data,
        style_function=style_func,
        tooltip=folium.GeoJsonTooltip(fields=['COUNTY', 'TOWN'], aliases=['縣市:', '鄉鎮:'])
    ).add_to(m)

    # 渲染地圖
    out = st_folium(m, width="100%", height=500, key="map")

    # --- 關鍵修正：直接在地圖下方顯示打卡區域 ---
    st.write("---")
    if out and out.get('last_object_clicked_tooltip'):
        click_info = out['last_object_clicked_tooltip']
        try:
            # 解析地圖回傳的文字
            parts = click_info.split(',')
            c = parts[0].split(':')[-1].strip()
            t = parts[1].split(':')[-1].strip()
            
            st.subheader(f"📍 當前選取區域：{c} {t}")
            
            # 檢查是否已去過
            is_visited = ((visited_df['TOWNNAME'] == t) & (visited_df['COUNTYNAME'] == c)).any()
            
            if is_visited:
                st.warning(f"✅ 您已經在 {t} 留下足跡囉！")
            else:
                if st.button(f"🚩 確認在「{t}」打卡", use_container_width=True):
                    if save_visit(t, c):
                        st.success(f"成功記錄！恭喜解鎖 {t}。")
                        st.balloons()
                        st.rerun()
        except Exception as e:
            st.info("請點擊地圖上的區塊進行打卡。")
    else:
        st.info("👆 請在地圖上點擊妳去過的鄉鎮區塊，下方會出現打卡按鈕喔！")

    # 進度統計
    st.write("---")
    count = len(visited_df)
    st.metric("已解鎖鄉鎮數量", f"{count} 個區域")
    if not visited_df.empty:
        with st.expander("查看我的足跡清單"):
            st.dataframe(visited_df.sort_values(by="visited_time", ascending=False), use_container_width=True)

else:
    st.error("❌ 找不到地圖檔 town.json")
