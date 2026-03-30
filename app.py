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
    # 避免重複紀錄
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
            # 修正所有可能的欄位名稱
            for feature in data['features']:
                p = feature['properties']
                p['T_NAME'] = p.get('TOWNNAME') or p.get('townname') or p.get('T_Name') or '未知'
                p['C_NAME'] = p.get('COUNTYNAME') or p.get('countyname') or p.get('C_Name') or '未知'
            return data
    return None

# --- 主介面 ---
st.title("🗺️ 台灣鄉鎮市區足跡地圖")

visited_df = load_data()
geojson_data = get_local_geojson()

if geojson_data:
    # 1. 建立地圖：預設高雄中心
    m = folium.Map(
        location=[22.62, 120.30], 
        zoom_start=11, 
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
        attr='Google'
    )

    # 2. 設置塗色樣式
    def style_func(feature):
        t = feature['properties']['T_NAME']
        c = feature['properties']['C_NAME']
        is_visited = ((visited_df['TOWNNAME'] == t) & (visited_df['COUNTYNAME'] == c)).any()
        
        return {
            'fillColor': '#FF8C00' if is_visited else '#FFFFFF',
            'color': '#FF8C00' if is_visited else 'white',
            'weight': 2,
            'fillOpacity': 0.6 if is_visited else 0.1,
        }

    # 3. 加入 GeoJSON 層
    folium.GeoJson(
        geojson_data,
        style_function=style_func,
        tooltip=folium.GeoJsonTooltip(fields=['C_NAME', 'T_NAME'], aliases=['縣市:', '鄉鎮:'])
    ).add_to(m)

    # 4. 渲染地圖 (重點：使用 key="taiwan_map" 並回傳所有點擊資料)
    output = st_folium(m, width="100%", height=500, key="taiwan_map")

    # --- 5. 處理點擊邏輯 ---
    st.write("---")
    
    # 嘗試從多個可能的回傳欄位抓取資訊
    clicked_props = None
    if output.get("last_active_drawing"):
        clicked_props = output["last_active_drawing"].get("properties")
    elif output.get("last_object_clicked_tooltip"):
        # 如果是 tooltip，嘗試解析字串
        try:
            info = output["last_object_clicked_tooltip"]
            # 範例: "縣市: 高雄市, 鄉鎮: 苓雅區"
            c = info.split(',')[0].split(':')[-1].strip()
            t = info.split(',')[1].split(':')[-1].strip()
            clicked_props = {"C_NAME": c, "T_NAME": t}
        except:
            pass

    # 顯示打卡按鈕
    if clicked_props:
        c_name = clicked_props.get('C_NAME', '未知')
        t_name = clicked_props.get('T_NAME', '未知')
        
        st.subheader(f"📍 您選取了：{c_name} {t_name}")
        
        if t_name != '未知':
            if st.button(f"🚩 確認在 {t_name} 打卡", use_container_width=True):
                if save_visit(t_name, c_name):
                    st.success(f"成功！{t_name} 已塗色。")
                    st.balloons()
                    st.rerun()
        else:
            st.warning("抓取不到區域名稱，請再點擊一次區塊中心。")
    else:
        st.info("👆 **請直接點擊地圖上的行政區區塊**，下方就會出現打卡按鈕。")

    # 6. 進度統計
    st.write("---")
    count = len(visited_df)
    st.metric("已解鎖鄉鎮數量", f"{count} 個區域")
    if not visited_df.empty:
        with st.expander("查看我的足跡清單"):
            st.write(visited_df.sort_values(by="visited_time", ascending=False))

else:
    st.error("❌ 找不到地圖檔 town.json")
