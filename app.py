import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import requests
from datetime import datetime

# --- 基礎配置 ---
st.set_page_config(page_title="台灣鄉鎮足跡地圖", layout="wide")
DATA_FILE = "visited_towns.csv"

# 更換為更穩定的台灣鄉鎮 GeoJSON 來源 (包含縣市與鄉鎮名稱)
GEOJSON_URL = "https://raw.githubusercontent.com/chaoyihuang/Taiwan-GeoJSON/master/town.json"

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["TOWNNAME", "COUNTYNAME", "visited_time"]).to_csv(DATA_FILE, index=False)

@st.cache_data
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

@st.cache_data(show_spinner="正在載入地圖資料...")
def get_geojson_data():
    try:
        # 加入 headers 模擬瀏覽器請求，避免被 GitHub 拒絕
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(GEOJSON_URL, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"下載失敗，錯誤代碼：{response.status_code}")
            return None
    except Exception as e:
        st.error(f"發生錯誤：{e}")
        return None

# --- 主介面 ---
st.title("🗺️ 台灣鄉鎮市區足跡地圖")
st.info("💡 點擊地圖上的區域即可「打卡」塗色。")

visited_df = load_data()
geojson_data = get_geojson_data()

if geojson_data:
    # 建立地圖：預設高雄中心
    m = folium.Map(
        location=[22.62, 120.30], 
        zoom_start=11, 
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
        attr='Google'
    )

    # 設置塗色樣式
    def style_func(feature):
        # 注意：不同資料源的屬性名稱可能略有不同，這裡對應的是 TOWNNAME 和 COUNTYNAME
        t_name = feature['properties'].get('TOWNNAME', '')
        c_name = feature['properties'].get('COUNTYNAME', '')
        
        is_visited = ((visited_df['TOWNNAME'] == t_name) & (visited_df['COUNTYNAME'] == c_name)).any()
        
        return {
            'fillColor': '#FF5722' if is_visited else '#FFFFFF', 
            'color': '#FF5722' if is_visited else 'gray',
            'weight': 1.5 if is_visited else 0.5,
            'fillOpacity': 0.5 if is_visited else 0.1,
        }

    # 顯示 GeoJSON
    g = folium.GeoJson(
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
                st.subheader(f"📍 選取區域：{c}{t}")
                if st.button("確認打卡", use_container_width=True):
                    if save_visit(t, c):
                        st.success("紀錄成功！")
                        st.rerun()
                    else:
                        st.warning("這裡已經去過囉！")

    # 進度統計
    st.write("---")
    total = len(geojson_data['features'])
    count = len(visited_df)
    st.metric("已解鎖鄉鎮", f"{count} / {total}", f"{count/total*100:.1f}%")
    st.progress(count/total if total > 0 else 0)

else:
    st.warning("地圖載入中或資料暫時無法取得，請稍後再試。")
