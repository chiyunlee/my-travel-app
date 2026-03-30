import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os, json
from datetime import datetime

# 基本配置
st.set_page_config(page_title="高雄開發足跡地圖", layout="wide")
DATA = "visited.csv"
# 直接指向妳 GitHub 上的檔案
GEO_FILE = "town.json"

# 初始化資料檔
if not os.path.exists(DATA):
    pd.DataFrame(columns=["T", "C", "time"]).to_csv(DATA, index=False)

@st.cache_data
def get_local_map():
    # 檢查本地檔案是否存在
    if os.path.exists(GEO_FILE):
        with open(GEO_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 統一欄位名稱 (針對 g0v 或政府 Opendata 格式)
        for f in data.get('features', []):
            p = f['properties']
            p['CN'] = p.get('COUNTYNAME') or p.get('C_Name') or '未知'
            p['TN'] = p.get('TOWNNAME') or p.get('T_Name') or '未知'
        return data
    return None

st.title("🗺️ 台灣鄉鎮市區足跡地圖")
v_df = pd.read_csv(DATA)
geo = get_local_map()

if geo:
    # 預設高雄中心
    m = folium.Map(location=[22.62, 120.30], zoom_start=11, 
                   tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                   attr='Google')

    def style_f(f):
        t, c = f['properties']['TN'], f['properties']['CN']
        is_v = ((v_df['T'] == t) & (v_df['C'] == c)).any()
        return {'fillColor': '#FF8C00' if is_v else '#FFFFFF', 
                'color': 'white', 'weight': 1, 'fillOpacity': 0.6 if is_v else 0.1}

    folium.GeoJson(geo, style_function=style_f, 
                   tooltip=folium.GeoJsonTooltip(fields=['CN', 'TN'], aliases=['縣市:', '鄉鎮:'])
                  ).add_to(m)
    
    out = st_folium(m, width="100%", height=500, key="map")

    if out and out.get("last_object_clicked_tooltip"):
        info = out["last_object_clicked_tooltip"]
        try:
            parts = info.split(',')
            c = parts[0].split(':')[-1].strip()
            t = parts[1].split(':')[-1].strip()
            
            st.write("---")
            st.subheader(f"📍 選取：{c} {t}")
            if st.button(f"🚩 在 {t} 打卡", use_container_width=True):
                if not ((v_df['T'] == t) & (v_df['C'] == c)).any():
                    new = pd.DataFrame([[t, c, datetime.now().strftime("%Y-%m-%d %H:%M")]], columns=["T", "C", "time"])
                    pd.concat([v_df, new], ignore_index=True).to_csv(DATA, index=False)
                    st.rerun()
        except:
            st.warning("請點擊區塊中心")
    else:
        st.info("👆 請點擊地圖上的行政區進行打卡")
    
    st.write("---")
    st.metric("解鎖進度", f"{len(v_df)} / 368")
else:
    st.error(f"❌ 找不到 {GEO_FILE} 檔案！")
    st.info("請確認妳已經將地圖檔上傳至 GitHub，且檔名完全符合「town.json」。")
