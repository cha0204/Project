import streamlit as st
import pandas as pd
import numpy as np
import os
import folium
from streamlit_folium import st_folium
import requests

# [1] 페이지 설정
st.set_page_config(page_title="고용 분석 대시보드", layout="wide")
st.title("📊 대한민국 지역/연령/산업 고용 분석 대시보드")

# [2] 데이터 로드 및 전처리 (캐싱)
@st.cache_data
def load_all_data():
    # 데이터 파일 경로 설정
    files = {
        "biz": "number of businesses.csv",
        "youth": "youth_population.csv",
        "age": "Administrative Districts_Cities_and_Provinces__Employed by Age.csv",
        "hours": "행정구역_시도__취업시간별_취업자_20260622021330.csv"
    }
    
    data = {}
    for key, file in files.items():
        if os.path.exists(file):
            # 한글 인코딩 문제 방지를 위해 utf-8-sig 또는 cp949 시도
            try:
                data[key] = pd.read_csv(file, encoding='utf-8-sig')
            except:
                data[key] = pd.read_csv(file, encoding='cp949')
    return data

data = load_all_data()

# [3] 탭 구성
tabs = st.tabs(["📉 종합 고용 지표", "🎯 전공별 추천", "👥 연령별 분석", "⏱️ 취업시간 패턴"])

# [탭 1: 종합 고용]
with tabs[0]:
    st.subheader("종합 고용 현황 데이터")
    if "biz" in data:
        df = data["biz"]
        st.dataframe(df.head(20), use_container_width=True)
        # 산업별 사업체 수 차트
        st.bar_chart(df.groupby('산업별')['2024'].sum())
    else:
        st.error("데이터 파일을 찾을 수 없습니다.")

# [탭 2: 전공별 추천]
with tabs[1]:
    st.subheader("산업별 데이터 분석")
    if "biz" in data:
        industries = data["biz"]['산업별'].unique()
        selected = st.multiselect("분석할 산업군 선택", industries, default=industries[:3])
        df_filt = data["biz"][data["biz"]['산업별'].isin(selected)]
        st.line_chart(df_filt.groupby('산업별').sum(numeric_only=True).T)

# [탭 3: 연령별 분석]
with tabs[2]:
    st.subheader("지역별/연령별 취업자")
    if "age" in data:
        df_age = data["age"]
        region = st.selectbox("지역 선택", df_age['시도별(1)'].unique())
        df_age_filt = df_age[df_age['시도별(1)'] == region]
        st.dataframe(df_age_filt, use_container_width=True)

# [탭 4: 취업시간]
with tabs[3]:
    st.subheader("취업시간별 데이터")
    if "hours" in data:
        df_h = data["hours"]
        st.dataframe(df_h, use_container_width=True)
        # 예시 차트
        st.area_chart(df_h.groupby('취업시간별').sum(numeric_only=True).T)

# [4] 하단 공지
st.sidebar.info("데이터 로딩 완료. 파일을 수정하려면 GitHub 저장소를 확인하세요.")
