import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os, json, requests
from datetime import datetime

# 基本配置
st.set_page_config(page_title="高雄開發足跡地圖", layout="wide")
DATA = "visited.csv"
# 使用 g0v 最標準且穩定的原始資料網址
GEO_URL = "https://raw.githubusercontent.com/g0v/tw-town-geojson/master/town.json"

# 初始化資料檔
if not os.path.exists(DATA):
    pd.DataFrame(columns=["T", "C", "time"]).to_csv(DATA, index=False)

@st.cache_data(show_spinner="正在載入台灣地圖數據...")
def get_valid_map():
    try:
        # 直接從網路上抓取最正確的格式
        resp = requests.get(GEO_URL, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # 確保它是標準的 FeatureCollection
            if data.get("type") == "FeatureCollection":
                for f in data.get('features', []):
                    p = f['properties']
                    p['CN'] = p.get('COUNTYNAME') or '未知'
                    p['TN'] = p.get('TOWNNAME') or '未知'
                return data
    except Exception as e:
        st.error(f"地圖讀取失敗：{e}")
    return None

st.title("🗺️ 台灣鄉鎮市區足跡地圖")
v_df = pd.read_csv(DATA)
geo = get_valid_map()

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
            st.subheader(f"📍 選取區域：{c} {t}")
            if st.button(f"🚩 在 {t} 打卡", use_container_width=True):
                if not ((v_df['T'] == t) & (v_df['C'] == c)).any():
                    new = pd.DataFrame([[t, c, datetime.now().strftime("%Y-%m-%d %H:%M")]], columns=["T", "C", "time"])
                    pd.concat([v_df, new], ignore_index=True).to_csv(DATA, index=False)
                    st.rerun()
        except:
            st.warning("請精準點擊區域中心色塊")
    else:
        st.info("👆 請在地圖上點擊妳去過的「行政區塊」進行打卡。")
    
    st.write("---")
    st.metric("已解鎖區域", f"{len(v_df)} / 368")
else:
    st.error("❌ 系統目前無法讀取地圖數據。")
    st.info("💡 建議：請到 Streamlit 管理介面按下 'Reboot App' 試試看！")
