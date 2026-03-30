import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os, json, requests
from datetime import datetime

st.set_page_config(page_title="高雄開發足跡地圖", layout="wide")
DATA, GEO, URL = "visited.csv", "town_ok.json", "https://raw.githubusercontent.com/chaoyihuang/Taiwan-GeoJSON/master/town.json"

if not os.path.exists(DATA):
    pd.DataFrame(columns=["T", "C", "time"]).to_csv(DATA, index=False)

@st.cache_data
def get_map():
    if os.path.exists(GEO):
        with open(GEO, 'r', encoding='utf-8') as f: data = json.load(f)
    else:
        data = requests.get(URL).json()
        with open(GEO, 'w', encoding='utf-8') as f: json.dump(data, f)
    for f in data['features']:
        f['properties']['CN'] = f['properties'].get('COUNTYNAME', '未知')
        f['properties']['TN'] = f['properties'].get('TOWNNAME', '未知')
    return data

st.title("🗺️ 台灣鄉鎮市區足跡地圖")
v_df = pd.read_csv(DATA)
geo = get_map()

if geo:
    m = folium.Map(location=[22.62, 120.30], zoom_start=11, tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')
    def style_f(f):
        t, c = f['properties']['TN'], f['properties']['CN']
        is_v = ((v_df['T'] == t) & (v_df['C'] == c)).any()
        return {'fillColor': '#FF8C00' if is_v else '#FFFFFF', 'color': 'white', 'weight': 1, 'fillOpacity': 0.6 if is_v else 0.1}

    folium.GeoJson(geo, style_function=style_f, tooltip=folium.GeoJsonTooltip(fields=['CN', 'TN'], aliases=['縣市:', '鄉鎮:'])).add_to(m)
    out = st_folium(m, width="100%", height=500, key="map")

    if out and out.get("last_object_clicked_tooltip"):
        info = out["last_object_clicked_tooltip"]
        try:
            c = info.split(',')[0].split(':')[-1].strip()
            t = info.split(',')[1].split(':')[-1].strip()
            st.subheader(f"📍 選取：{c} {t}")
            if st.button(f"🚩 在 {t} 打卡"):
                if not ((v_df['T'] == t) & (v_df['C'] == c)).any():
                    new = pd.DataFrame([[t, c, datetime.now().strftime("%Y-%m-%d %H:%M")]], columns=["T", "C", "time"])
                    pd.concat([v_df, new], ignore_index=True).to_csv(DATA, index=False)
                    st.rerun()
        except: st.warning("請再點一次區塊中心")
    else:
        st.info("👆 請點擊地圖區塊進行打卡")
    st.metric("解鎖進度", f"{len(v_df)} / 368")
