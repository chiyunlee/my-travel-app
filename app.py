import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import os
import json
import requests

# --- 基础配置 ---
st.set_page_config(page_title="台湾乡镇踩点地图", layout="wide", initial_sidebar_state="collapsed")
DATA_FILE = "visited_towns.csv"

# 台湾乡镇 GeoJSON 数据链接 (由台湾政府公开资料整理)
# 这个链接包含了全台湾所有乡镇市区的边界轮廓
GEOJSON_URL = "https://raw.githubusercontent.com/g0v/tw-town-geojson/master/town.json"

# 初始化已造访数据
if not os.path.exists(DATA_FILE):
    # 栏位：TOWNNAME (乡镇名), COUNTYNAME (县市名), visited_time (时间)
    pd.DataFrame(columns=["TOWNNAME", "COUNTYNAME", "visited_time"]).to_csv(DATA_FILE, index=False)

@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE)

def save_visit(town_name, county_name):
    df = load_data()
    # 检查是否重复打卡
    if not ((df['TOWNNAME'] == town_name) & (df['COUNTYNAME'] == county_name)).any():
        from datetime import datetime
        new_row = pd.DataFrame([[town_name, county_name, datetime.now().strftime("%Y-%m-%d %H:%M")]], 
                                columns=["TOWNNAME", "COUNTYNAME", "visited_time"])
        pd.concat([df, new_row], ignore_index=True).to_csv(DATA_FILE, index=False)
        return True
    return False

# --- 核心：下载并缓存 GeoJSON 地图数据 ---
@st.cache_data
def get_geojson_data():
    try:
        response = requests.get(GEOJSON_URL)
        return response.json()
    except Exception as e:
        st.error(f"无法下载地图数据：{e}")
        return None

# --- 主界面 ---
st.title("🗺️ 台湾乡镇市区足迹地图")
st.markdown("在地圖上點擊你**「去過的鄉鎮」**，它就會自動塗上顏色！")

# 加载数据
visited_df = load_data()
geojson_data = get_geojson_data()

if geojson_data:
    # 建立 Folium 地图 (預設以高雄為中心)
    m = folium.Map(
        location=[22.62, 120.30], 
        zoom_start=11, 
        # 使用 Google 卫星混合图作为背景
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
        attr='Google'
    )

    # 定义已造访行政区的样式 (例如：半透明橙色)
    def style_function(feature):
        town_name = feature['properties']['TOWNNAME']
        county_name = feature['properties']['COUNTYNAME']
        
        # 检查这个乡镇是否在已造访清单中
        is_visited = ((visited_df['TOWNNAME'] == town_name) & (visited_df['COUNTYNAME'] == county_name)).any()
        
        return {
            'fillColor': '#ff7800' if is_visited else '#ffffff00', # 去过涂橘色，没去过透明
            'color': '#ff7800' if is_visited else 'gray',          # 边界颜色
            'weight': 1.5 if is_visited else 0.5,                  # 边界粗细
            'fillOpacity': 0.7 if is_visited else 0,               # 透明度
        }

    # 将 GeoJSON 地图层加入 Folium
    geo_json_layer = folium.GeoJson(
        geojson_data,
        name="台湾乡镇边界",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(fields=['COUNTYNAME', 'TOWNNAME'], aliases=['县市', '乡镇'])
    ).add_to(m)

    # 渲染地图至 Streamlit，并开启点击事件捕获
    map_data = st_folium(m, width="100%", height=600, key="taiwan_map", returned_objects=["last_active_drawing"])

    # --- 处理地图点击事件 ---
    if map_data['last_active_drawing']:
        # 获取点击的乡镇属性
        props = map_data['last_active_drawing']['properties']
        clicked_town = props['TOWNNAME']
        clicked_county = props['COUNTYNAME']
        
        with st.sidebar:
            st.subheader(f"📍 您点击了：{clicked_county}{clicked_town}")
            
            # 检查是否已造访
            is_visited = ((visited_df['TOWNNAME'] == clicked_town) & (visited_df['COUNTYNAME'] == clicked_county)).any()
            
            if is_visited:
                st.warning("⚠️ 此地点已在您的足迹清单中。")
            else:
                st.info("确认将此地点加入您的足迹地图吗？")
                if st.button("确认打卡", use_container_width=True):
                    if save_visit(clicked_town, clicked_county):
                        st.success(f"✅ 已记录：{clicked_county}{clicked_town}")
                        st.balloons()
                        # 重新加载页面以更新地图颜色
                        st.rerun()

    # --- 统计区域 ---
    st.write("---")
    total_towns = len(geojson_data['features'])
    visited_count = len(visited_df)
    progress_percentage = (visited_count / total_towns) * 100 if total_towns > 0 else 0
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("已解锁乡镇", f"{visited_count} / {total_towns}")
        st.write(f"解锁进度：{progress_percentage:.1f}%")
    with col2:
        st.progress(progress_percentage / 100)

    # 显示已造访清单
    if not visited_df.empty:
        with st.expander("查看已造访乡镇清单"):
            st.dataframe(visited_df.sort_values(by="visited_time", ascending=False), use_container_width=True)

else:
    st.error("无法加载地图数据，请检查网络连接或 GeoJSON 链接。")
