import streamlit as st
import pandas as pd
import os

# [1] 페이지 설정
st.set_page_config(page_title="고용 분석 대시보드", layout="wide")
st.title("📊 대한민국 고용 분석 대시보드 (막대 그래프 버전)")

# [2] 데이터 로드 (Encoding을 cp949로 우선 설정하여 한글 깨짐 방지)
@st.cache_data
def load_data():
    files = {
        "biz": "number of businesses.csv",
        "age": "Administrative Districts_Cities_and_Provinces__Employed by Age.csv",
        "hours": "행정구역_시도__취업시간별_취업자_20260622021330.csv"
    }
    data = {}
    for key, file in files.items():
        if os.path.exists(file):
            try:
                data[key] = pd.read_csv(file, encoding='cp949')
            except:
                data[key] = pd.read_csv(file, encoding='utf-8')
    return data

data = load_data()

# [3] 탭 구성 (모두 막대 그래프 사용)
tabs = st.tabs(["📉 산업별 사업체 분석", "👥 지역별 연령 분석", "⏱️ 취업시간 패턴 분석"])

# [탭 1: 산업별]
with tabs[0]:
    st.subheader("산업별 사업체 수 비교")
    if "biz" in data:
        df = data["biz"]
        # 산업별 2024년 사업체 수 합계 막대 그래프
        chart_data = df.groupby('산업별')['2024'].sum().sort_values(ascending=False)
        st.bar_chart(chart_data)
    else:
        st.error("데이터 파일 확인 필요")

# [탭 2: 연령별]
with tabs[1]:
    st.subheader("지역별 연령 구조 (막대 그래프)")
    if "age" in data:
        df_age = data["age"]
        regions = df_age['시도별(1)'].unique()
        selected_region = st.selectbox("지역 선택", regions)
        df_filt = df_age[df_age['시도별(1)'] == selected_region]
        
        # 지역 내 연령별 2025년 데이터 막대 그래프
        age_data = df_filt.set_index('연령계층별(1)')['2025']
        st.bar_chart(age_data)

# [탭 3: 취업시간]
with tabs[2]:
    st.subheader("취업시간별 취업자 분포")
    if "hours" in data:
        df_h = data["hours"]
        # 취업시간별 2025년 데이터 막대 그래프
        hours_data = df_h.groupby('취업시간별')['2025'].sum().sort_values(ascending=False)
        st.bar_chart(hours_data)
    else:
        st.error("데이터 파일 확인 필요")

st.sidebar.write("막대 그래프 모드로 최적화 완료되었습니다.")
