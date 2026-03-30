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
GEOJSON_FILE = "town.json"  # 指向妳上傳的檔案

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

# --- 讀取本地地圖資料 ---
@st.cache_data
def get_local_geojson():
    if os.path.exists(GEOJSON_FILE):
        with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return None

# --- 主介面 ---
st.title("🗺️ 台灣鄉鎮市區足跡地圖")
st.info("💡 檔案已本地化，不再擔心網路斷線或 404！點擊區域即可打卡。")

visited_df = load_data()
geojson_data = get_local_geojson()

if geojson_data:
    # 建立地圖：預設高雄中心 (緯度 22.6, 經度 120.3)
    m = folium.Map(
        location=[22.62, 120.30], 
        zoom_start=11, 
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
        attr='Google'
    )

    # 設置塗色樣式
    def style_func(feature):
        # 根據 GeoJSON 的屬性抓取名稱
        t_name = feature['properties'].get('TOWNNAME', '')
        c_name = feature['properties'].get('COUNTYNAME', '')
        
        is_visited = ((visited_df['TOWNNAME'] == t_name) & (visited_df['COUNTYNAME'] == c_name)).any()
        
        return {
            'fillColor': '#FF8C00' if is_visited else '#FFFFFF', # 橘色代表去過
            'color': '#FF8C00' if is_visited else 'gray',
            'weight': 1.5 if is_visited else 0.5,
            'fillOpacity': 0.6 if is_visited else 0.05, # 未去過設為極低透明度
        }

    # 顯示地圖層
    folium.GeoJson(
        geojson_data,
        style_function=style_func,
        tooltip=folium.GeoJsonTooltip(fields=['COUNTYNAME', 'TOWNNAME'], aliases=['縣市:', '鄉鎮:'])
    ).add_to(m)

    # 獲取點擊資訊
    out = st_folium(m, width="100%", height=600, key="map", returned_objects=["last_active_drawing"])

    # 側邊欄處理打卡
    if out and out.get('last_active_drawing'):
        props = out['last_active_drawing']['properties']
        t = props.get('TOWNNAME')
        c = props.get('COUNTYNAME')
        
        if t and c:
            with st.sidebar:
                st.subheader(f"📍 當前選取：{c}{t}")
                if st.button("確認打卡存檔", use_container_width=True):
                    if save_visit(t, c):
                        st.success(f"✅ {t} 打卡成功！")
                        st.rerun()
                    else:
                        st.warning("這個區域已經塗過顏色囉！")

    # 進度條
    st.write("---")
    total = len(geojson_data['features'])
    count = len(visited_df)
    st.metric("解鎖進度", f"{count} / {total} 個鄉鎮", f"{count/total*100:.1f}%")
    st.progress(count/total if total > 0 else 0)

else:
    st.error(f"❌ 找不到 {GEOJSON_FILE} 檔案！請確保妳已將地圖檔上傳至 GitHub 根目錄。")
