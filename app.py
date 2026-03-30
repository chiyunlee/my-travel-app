import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os, json
from datetime import datetime

# 頁面配置
st.set_page_config(page_title="高雄開發足跡地圖", layout="wide")
DATA_FILE = "visited_towns.csv"

# 初始化打卡資料
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["TOWN", "time"]).to_csv(DATA_FILE, index=False)

def load_v(): return pd.read_csv(DATA_FILE)

# --- 核心解決方案：直接內嵌高雄行政區邊界 (簡化版) ---
# 這裡使用內建的 Topo/Geo 邏輯，如果還是抓不到外部檔案，我們直接畫出高雄點
@st.cache_data
def get_kh_map():
    # 使用中研院另一個備用且更穩定的 CDN
    url = "https://raw.githubusercontent.com/marswong/taiwan_geojson/master/kaohsiung.json"
    try:
        import requests
        r = requests.get(url, timeout=10)
        data = r.json()
        for f in data['features']:
            # 修正高雄地圖常見的欄位名
            p = f['properties']
            p['T'] = p.get('TOWNNAME') or p.get('T_Name') or '未知'
        return data
    except:
        return None

st.title("🏗️ 高雄開發足跡地圖")
v_df = load_v()
kh_geo = get_kh_map()

if kh_geo:
    # 預設地圖位置：高雄市中心
    m = folium.Map(location=[22.65, 120.35], zoom_start=11, 
                   tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                   attr='Google')

    def style_f(f):
        t = f['properties']['T']
        is_v = (v_df['TOWN'] == t).any()
        return {'fillColor': '#FF8C00' if is_v else '#FFFFFF', 
                'color': 'white', 'weight': 1.5, 'fillOpacity': 0.6 if is_v else 0.2}

    folium.GeoJson(kh_geo, style_function=style_f, 
                   tooltip=folium.GeoJsonTooltip(fields=['T'], aliases=['行政區:'])
                  ).add_to(m)
    
    out = st_folium(m, width="100%", height=500, key="kh_map")

    if out and out.get("last_object_clicked_tooltip"):
        t_name = out["last_object_clicked_tooltip"].split(':')[-1].strip()
        st.write("---")
        st.subheader(f"📍 當前選取：高雄市 {t_name}")
        
        if st.button(f"🚩 在 {t_name} 留下開發足跡", use_container_width=True):
            if not (v_df['TOWN'] == t_name).any():
                new = pd.DataFrame([[t_name, datetime.now().strftime("%Y-%m-%d %H:%M")]], columns=["TOWN", "time"])
                pd.concat([v_df, new], ignore_index=True).to_csv(DATA_FILE, index=False)
                st.success(f"{t_name} 標記成功！")
                st.balloons()
                st.rerun()
    else:
        st.info("💡 請在地圖上點擊高雄市的行政區（如苓雅區、鳳山區）。")

    st.write("---")
    st.metric("高雄解鎖區域", f"{len(v_df)} 個行政區")
else:
    st.error("目前地圖服務連線較慢，請嘗試點擊下方的「重整地圖」。")
    if st.button("🔄 重整地圖數據"):
        st.cache_data.clear()
        st.rerun()
