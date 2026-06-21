import streamlit as st
import pandas as pd
import numpy as np
import os

# --- [1] 페이지 설정 ---
st.set_page_config(page_title="고용 분석 대시보드", layout="wide")
st.title("📊 대한민국 고용 분석 종합 대시보드")

# --- [2] 모든 데이터 로드 (파일 8개 자동 감지) ---
@st.cache_data
def load_all_files():
    # 파일명 매핑
    files = {
        "biz": "number of businesses.csv",
        "youth": "youth_population.csv",
        "age_dist": "Administrative Districts_Cities_and_Provinces__Employed by Age.csv",
        "status": "Employed people by employment status.csv",
        "gender_age": "Employed Persons by Gender and Age.csv",
        "gender_ind": "Employed by Gender and Industry.csv",
        "hours": "행정구역_시도__취업시간별_취업자_20260622021330.csv"
    }
    data = {}
    for key, filename in files.items():
        if os.path.exists(filename):
            try:
                data[key] = pd.read_csv(filename, encoding='cp949') # 한글 처리
            except:
                data[key] = pd.read_csv(filename, encoding='utf-8')
    return data

data = load_all_files()

# 콤마 처리용 함수
def format_df(df):
    return df.style.format(thousands=',')

# --- [3] 탭 구성 ---
tabs = st.tabs(["📉 종합 고용/산업", "🎯 전공/연령 분석", "👥 성별/연령 분석", "⏱️ 취업시간 패턴"])

# 탭 1: 종합 고용/산업
with tabs[0]:
    st.subheader("종합 고용 현황")
    if "biz" in data:
        df = data["biz"]
        st.dataframe(format_df(df), use_container_width=True)
        # 막대 그래프: 산업별 2024년 사업체 수
        if '산업별' in df.columns:
            st.bar_chart(df.groupby('산업별')['2024'].sum())

# 탭 2: 전공/연령 분석
with tabs[1]:
    st.subheader("지역별/연령별 고용")
    if "age_dist" in data:
        df = data["age_dist"]
        region = st.selectbox("지역 선택", df['시도별(1)'].unique())
        df_filt = df[df['시도별(1)'] == region]
        st.dataframe(format_df(df_filt), use_container_width=True)
        # 막대 그래프
        st.bar_chart(df_filt.set_index('연령계층별(1)')['2025'])

# 탭 3: 성별/연령 분석
with tabs[2]:
    st.subheader("성별 고용 상태")
    if "gender_age" in data:
        df = data["gender_age"]
        st.dataframe(format_df(df), use_container_width=True)
        st.bar_chart(df.groupby('성별')['2025'].sum())

# 탭 4: 취업시간
with tabs[3]:
    st.subheader("취업시간 패턴")
    if "hours" in data:
        df = data["hours"]
        st.dataframe(format_df(df), use_container_width=True)
        st.bar_chart(df.groupby('취업시간별')['2025'].sum())

st.sidebar.success("데이터 로딩 및 분석 완료")
