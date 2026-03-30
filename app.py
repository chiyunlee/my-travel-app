import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os, json, requests
from datetime import datetime

# 基本設定
st.set_page_config(page_title="高雄開發足跡地圖", layout="wide")
DATA = "visited.csv"
# 更換為更穩定的台灣鄉鎮資料來源 (中研院開放資料鏡像)
URL = "https://raw.githubusercontent.com/g0v/tw-town-geojson/master/town.json"

if not os.path.exists(DATA):
    pd.DataFrame(columns=["T", "C", "time"]).to_csv(DATA, index=False)

@st.cache_data(show_spinner="正在載入地圖數據...")
def get_map():
    try:
        resp = requests.get(URL, timeout=20)
        # 檢查是否成功抓取
        if resp.status_code == 200:
            data = resp.json()
            for f in data['features']:
                # 統一欄位名稱
                f['properties']['CN'] = f['properties'].get('COUNTYNAME', '未知')
                f['properties']['TN'] = f['properties'].get('TOWNNAME', '未知')
            return data
        else:
            st.error(f"地圖下載失敗，代碼：{resp.status_code}")
            return None
    except Exception as e:
        st.error(f"連線錯誤：{e}")
        return None

st.title("🗺️ 台灣鄉鎮市區足跡地圖")
v_df = pd.read_csv(DATA)
geo = get_map()

if geo:
    # 地圖中心點設在高雄
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
            # 修正解析邏輯
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
            st.warning("請精準點擊區域中心")
    else:
        st.info("👆 請點擊地圖上的行政區區塊進行打卡")
    
    st.write("---")
    st.metric("解鎖進度", f"{len(v_df)} / 368")
else:
    st.info("💡 暫時無法載入地圖，請確認您的網路環境或稍後重新整理。")
