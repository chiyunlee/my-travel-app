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
# 確保路徑在雲端環境也能正確執行
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
            # 強制清理數據：確保每個物件都有必要的屬性，避免渲染錯誤
            for feature in data['features']:
                p = feature['properties']
                # 統一屬性名稱，防止大小寫或格式不一
                p['TOWNNAME'] = p.get('TOWNNAME', p.get('townname', '未知'))
                p['COUNTYNAME'] = p.get('COUNTYNAME', p.get('countyname', '未知'))
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
        t_name = feature['properties']['TOWNNAME']
        c_name = feature['properties']['COUNTYNAME']
        is_visited = ((visited_df['TOWNNAME'] == t_name) & (visited_df['COUNTYNAME'] == c_name)).any()
        
        return {
            'fillColor': '#FF8C00' if is_visited else '#FFFFFF',
            'color': '#FF8C00' if is_visited else 'gray',
            'weight': 1.5 if is_visited else 0.5,
            'fillOpacity': 0.6 if is_visited else 0.01,
        }

    # 顯示地圖層
    fg = folium.FeatureGroup(name="鄉鎮區域")
    folium.GeoJson(
        geojson_data,
        style_function=style_func,
        tooltip=folium.GeoJsonTooltip(fields=['COUNTYNAME', 'TOWNNAME'], aliases=['縣市:', '鄉鎮:'])
    ).add_to(fg)
    fg.add_to(m)

    # 渲染地圖 (修正關鍵：減少傳回的對象，避免 AssertionError)
    out = st_folium(m, width="100%", height=600, key="map")

    # 處理點擊 (st_folium 預設點擊會傳回在 last_object_clicked_tooltip)
    if out and out.get('last_object_clicked_tooltip'):
        # 這裡從 tooltip 的文字解析出縣市與鄉鎮
        click_info = out['last_object_clicked_tooltip']
        # 預期格式: "縣市: 高雄市, 鄉鎮: 苓雅區"
        try:
            parts = click_info.split(',')
            c = parts[0].split(':')[-1].strip()
            t = parts[1].split(':')[-1].strip()
            
            with st.sidebar:
                st.subheader(f"📍 選取：{c}{t}")
                if st.button("確認打卡", use_container_width=True):
                    if save_visit(t, c):
                        st.success(f"✅ {t} 打卡成功！")
                        st.rerun()
        except:
            pass

    # 進度統計
    st.write("---")
    count = len(visited_df)
    st.metric("已解鎖鄉鎮", f"{count} 個區域")

else:
    st.error("❌ 找不到地圖檔，請確認 town.json 已上傳至 GitHub。")
