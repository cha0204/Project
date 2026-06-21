import streamlit as st
import pandas as pd
import numpy as np
import os
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="고용 분석 대시보드", layout="wide")
st.title("📊 내 전공은 이건데 어디로 가야하지?")

# --- [1] 데이터 로드 ---
@st.cache_data
def load_data():
    files = {
        "biz": "number of businesses.csv",
        "youth": "youth_population.csv",
        "age": "Administrative Districts_Cities_and_Provinces__Employed by Age.csv",
        "hours": "행정구역_시도__취업시간별_취업자_20260622021330.csv"
    }
    data = {}
    for key, f in files.items():
        if os.path.exists(f):
            data[key] = pd.read_csv(f, encoding='cp949' if 'csv' in f else 'utf-8')
    return data

data = load_data()

# --- [2] 콤마가 포함된 포맷팅 함수 ---
def get_formatted_df(df):
    return df.style.format(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)

# --- [3] 탭 구성 ---
tabs = st.tabs(["🗺️ 종합 지도 및 고용 지표", "🎯 전공별 추천 지역", "👥 지역별 연령 구조", "⏱️ 취업시간 패턴"])

# 탭 1: 지도 및 종합 지표 (원래 사용하시던 그 지도!)
with tabs[0]:
    st.subheader("대한민국 지역별 고용 현황 지도")
    m = folium.Map(location=[36.2, 127.8], zoom_start=7, tiles="CartoDB positron")
    # 여기에 원래 쓰시던 지도 마커/Choropleth 로직을 넣으시면 됩니다.
    map_output = st_folium(m, width='stretch', height=500)
    
    if "biz" in data:
        st.dataframe(get_formatted_df(data["biz"].head(10)), use_container_width=True)
        # 막대 그래프로만 시각화
        st.bar_chart(data["biz"].groupby('산업별')['2024'].sum())

# 탭 2: 전공별 추천
with tabs[1]:
    st.subheader("전공 계열별 분석")
    if "biz" in data:
        df = data["biz"]
        st.bar_chart(df.groupby('산업별')['2024'].sum().sort_values(ascending=False))

# 탭 3: 연령별
with tabs[2]:
    st.subheader("지역별 연령 구조")
    if "age" in data:
        df = data["age"]
        st.dataframe(get_formatted_df(df.head(10)), use_container_width=True)
        st.bar_chart(df.set_index('연령계층별(1)')['2025'])

# 탭 4: 취업시간
with tabs[3]:
    st.subheader("취업시간별 분포")
    if "hours" in data:
        df = data["hours"]
        st.bar_chart(df.groupby('취업시간별')['2025'].sum())
