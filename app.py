import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import json
import requests
from datetime import datetime

# --- 基礎配置 ---
st.set_page_config(page_title="高雄開發足跡地圖", layout="wide")
DATA_FILE = "visited_towns.csv"
GEOJSON_FILE = "town_fixed.json"
# 更換為更穩定的靜態鏡像網址 (避免 GitHub API 限制)
RAW_GEOJSON_URL = "https://raw.githubusercontent.com/chaoyihuang/Taiwan-GeoJSON/master/town.json"

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

@st.cache_data(show_spinner="正在載入台灣地圖數據...")
def get_geojson():
    # 嘗試讀取本地，若失敗則重新下載
    if os.path.exists(GEOJSON_FILE):
        try:
            with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                data = json.loads(content)
                if 'features' in data:
                    for feature in data['features']:
                        p = feature['properties']
                        p['C_NAME'] = p.get('COUNTYNAME') or p.get('C_Name') or '未知'
                        p['T_NAME'] = p.get('TOWNNAME') or p.get('T_Name') or '未知'
                    return data
        except: pass

    try:
        # 強制指定編碼，避免抓到亂碼字元
        resp = requests.get(RAW_GEOJSON_URL, timeout=10)
        resp.encoding = 'utf-8'
        raw_text = resp.text.strip()
        
        # 解決常見的 JSON 格式錯誤 (Extra data)
        data = json.loads(raw_text)
        
        with open(GEOJSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
        for feature in data['features']:
            p = feature['properties']
            p['C_NAME'] = p.get('COUNTYNAME') or p.get('C_Name') or '未知'
            p['T_NAME'] = p.get('TOWNNAME') or p.get('T_Name') or '未知'
        return data
    except Exception as e:
        st.error(f"地圖資料解析失敗：{e}")
        st.info("💡 建議：請確認 GitHub 專案中沒有壞掉的 town.json，或嘗試重啟 App。")
        return None

# --- 主介面 ---
st.title("🗺️ 台灣鄉鎮市區足跡地圖")

visited_df = load_data()
geojson_data = get_geojson()

if geojson_data:
    # 預設地圖位置（高雄）
    m = folium.Map(
        location=[22.
