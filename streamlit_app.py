import streamlit as st
import pandas as pd
import numpy as np
import re
import os
import unicodedata
import requests
import folium
from streamlit_folium import st_folium

# --- [1] 페이지 설정 ---
st.set_page_config(page_title="전공군별 지역/연령/시간 고용 분석 대시보드", layout="wide")
st.title("📊 대한민국 전공·지역·연령·취업시간 통합 고용 분석 대시보드")

# --- [2] 유틸리티 및 정제 함수 ---
def clean_string(text):
    if pd.isna(text): return text
    text = str(text)
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'[\s\u3000\xa0\n\r]+', '', text)
    text = re.sub(r'^[\*\-]+', '', text)
    return text

# --- [2] 유틸리티 및 정제 함수 부분의 매핑 수정 ---

# 지역명 표준화 매핑 (GeoJSON과 CSV 간의 가교 역할)
region_name_map = {
    '서울': '서울특별시', 
    '부산': '부산광역시', 
    '대구': '대구광역시', 
    '인천': '인천광역시',
    '광주': '광주광역시', 
    '대전': '대전광역시', 
    '울산': '울산광역시', 
    '세종': '세종특별자치시',
    '경기': '경기도', 
    '강원': '강원특별자치도', 
    '충북': '충청북도', 
    '충남': '충청남도',
    '전북': '전북특별자치도', 
    '전남': '전라남도', 
    '경북': '경상북도', 
    '경남': '경상남도',  # <--- 여기에 "경남" 추가!
    '제주': '제주특별자치도',
    # 추가로 자주 쓰이는 줄임말들
    '경북': '경상북도',
    '경남': '경상남도',
    '전북': '전북특별자치도',
    '전남': '전라남도',
    '충북': '충청북도',
    '충남': '충청남도'
}


def normalize_region_name(name):
    name = clean_string(name)
    return region_name_map.get(name, name)

def find_file_by_keyword(default_name, keywords):
    if os.path.exists(default_name): return default_name
    clean_target_kws = [clean_string(kw) for kw in keywords]
    for f in os.listdir('.'):
        clean_f = clean_string(f)
        if all(kw in clean_f for kw in clean_target_kws): return f
    return default_name

# --- [3] 데이터 로딩 로직 ---
def load_and_clean_general(file_path, id_cols, keywords=None):
    try:
        resolved_path = find_file_by_keyword(file_path, keywords if keywords else [file_path.split('.')[0]])
        if not os.path.exists(resolved_path): return pd.DataFrame(columns=list(id_cols) + ['연도', '값'])
        df = pd.read_csv(resolved_path, encoding='utf-8')
        for col in df.columns[:len(id_cols)]:
            df[col] = df[col].astype(str).str.strip().replace(['nan', '', 'None', 'NaN'], np.nan)
        df.columns = list(id_cols) + list(df.columns[len(id_cols):])
        df[id_cols] = df[id_cols].ffill()
        for col in id_cols: df[col] = df[col].apply(clean_string)
        year_mapping = {}
        year_cols = []
        for col in df.columns:
            match = re.search(r'(\d{4})', str(col))
            if match:
                clean_year = match.group(1)
                year_mapping[col] = clean_year
                year_cols.append(col)
        df = df.rename(columns=year_mapping)
        pure_year_cols = [year_mapping[c] for c in year_cols]
        df_long = df.melt(id_vars=id_cols, value_vars=pure_year_cols, var_name='연도', value_name='값')
        df_long['값'] = pd.to_numeric(df_long['값'].astype(str).str.replace(',', ''), errors='coerce')
        return df_long
    except Exception as e:
        return pd.DataFrame(columns=list(id_cols) + ['연도', '값'])

@st.cache_data
def load_youth_population():
    try:
        resolved_path = find_file_by_keyword("youth_population.csv", ["youth", "population"])
        if not os.path.exists(resolved_path): return pd.DataFrame(columns=['행정구역별', '항목', '연도', '연령계층', '값'])
        df = pd.read_csv(resolved_path, header=None)
        years_raw = df.iloc[0].ffill().astype(str)
        years = [re.search(r'(\d{4})', y).group(1) if re.search(r'(\d{4})', y) else clean_string(y) for y in years_raw]
        ages = df.iloc[1].fillna('').astype(str).apply(clean_string)
        col_names = []
        for y, a in zip(years, ages):
            if y == a or a == '': col_names.append(y)
            else: col_names.append(f"{y}_{a}")
        df.columns = col_names
        df = df.drop([0, 1]).reset_index(drop=True)
        df.columns = ['행정구역별', '항목'] + list(df.columns[2:])
        df['행정구역별'] = df['행정구역별'].ffill().apply(clean_string)
        df['항목'] = df['항목'].apply(clean_string)
        val_cols = [c for c in df.columns if '_' in c]
        df_long = df.melt(id_vars=['행정구역별', '항목'], value_vars=val_cols, var_name='연도_연령', value_name='값')
        df_long['연도'] = df_long['연도_연령'].apply(lambda x: x.split('_')[0])
        df_long['연령계층'] = df_long['연도_연령'].apply(lambda x: x.split('_')[1])
        df_long['값'] = pd.to_numeric(df_long['값'].astype(str).str.replace(',', ''), errors='coerce')
        return df_long.drop(columns=['연도_연령'])
    except Exception as e:
        return pd.DataFrame(columns=['행정구역별', '항목', '연도', '연령계층', '값'])

@st.cache_data
def load_number_of_businesses():
    try:
        resolved_path = find_file_by_keyword("number of businesses.csv", ["number", "businesses"])
        if not os.path.exists(resolved_path): return pd.DataFrame(columns=['행정구역별', '산업별', '사업체구분별', '연도', '지표구분', '값'])
        df = pd.read_csv(resolved_path, header=None)
        years_raw = df.iloc[0].ffill().astype(str)
        years = [re.search(r'(\d{4})', y).group(1) if re.search(r'(\d{4})', y) else clean_string(y) for y in years_raw]
        metrics = df.iloc[1].fillna('').astype(str).apply(clean_string)
        col_names = []
        for y, m in zip(years, metrics):
            if y == m or m == '': col_names.append(y)
            else: col_names.append(f"{y}_{m}")
        df.columns = col_names
        df = df.drop([0, 1]).reset_index(drop=True)
        id_cols = ['행정구역별', '산업별', '사업체구분별']
        df.columns = id_cols + list(df.columns[3:])
        for col in id_cols: df[col] = df[col].ffill().apply(clean_string)
        val_cols = [c for c in df.columns if '_' in c]
        df_long = df.melt(id_vars=id_cols, value_vars=val_cols, var_name='연도_지표', value_name='값')
        df_long['연도'] = df_long['연도_지표'].apply(lambda x: x.split('_')[0])
        df_long['지표구분'] = df_long['연도_지표'].apply(lambda x: x.split('_')[1])
        df_long['값'] = pd.to_numeric(df_long['값'].astype(str).str.replace(',', ''), errors='coerce')
        return df_long.drop(columns=['연도_지표'])
    except Exception as e:
        return pd.DataFrame(columns=['행정구역별', '산업별', '사업체구분별', '연도', '지표구분', '값'])

# --- [4] 지도 관련 데이터 ---
@st.cache_data
def get_korea_geojson():
    url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"
    try:
        response = requests.get(url)
        geojson = response.json()
        for feature in geojson['features']:
            raw_name = feature['properties']['name']
            feature['properties']['name'] = normalize_region_name(raw_name)
        return geojson
    except: return None

coordinate_map = {
    '서울특별시': [37.5665, 126.9780], '경기도': [37.4138, 127.5183], '부산광역시': [35.1796, 129.0756],
    '경상남도': [35.2373, 128.6922], '인천광역시': [37.4563, 126.7052], '경상북도': [36.5760, 128.5056],
    '대구광역시': [35.8714, 128.6014], '충청남도': [36.6588, 126.6728], '전라남도': [34.8160, 126.4629],
    '전북특별자치도': [35.8204, 127.1087], '충청북도': [36.6356, 127.4913], '강원특별자치도': [37.8853, 127.7298],
    '대전광역시': [36.3504, 127.3848], '광주광역시': [35.1595, 126.8526], '울산광역시': [35.5389, 129.3114],
    '제주특별자치도': [33.4996, 126.5312], '세종특별자치시': [36.4800, 127.2890]
}

# --- [5] 메인 실행부 ---
with st.spinner("데이터셋 안전하게 융합 중..."):
    df_status = load_and_clean_general("Employed people by employment status.csv", ['종사상지위별'], ["employment", "status"])
    df_age_raw = load_and_clean_general("Administrative Districts_Cities_and_Provinces__Employed by Age.csv", ['시도별', '연령계층별1', '연령계층별2'], ["Employed", "Age"])
    df_youth_pop = load_youth_population()
    df_biz = load_number_of_businesses()
    df_hours_new = load_and_clean_general("행정구역_시도__취업시간별_취업자_20260622021330.csv", ['시도별', '취업시간별'], keywords=["취업시간별", "취업자"])

tabs = st.tabs(["📉 종합 고용 지표", "🎯 전공별 추천 지역 분석", "👥 지역별 연령 구조 분석", "⏱️ 지역별 취업시간 패턴", "🏢 원본 데이터"])

# --- TAB 1: 종합 고용 지표 ---
with tabs[0]:
    st.subheader("🗺️ 대한민국 시도별 청년(25세~39세) 인구 분석 및 지도 클릭 조회")
    st.markdown("💡 **지도의 특정 지역을 마우스로 클릭해 보세요! 오른쪽의 차트가 즉시 전환됩니다.**")
    
    if not df_youth_pop.empty:
        df_base = df_youth_pop[(df_youth_pop['행정구역별'] != '전국') & (df_youth_pop['항목'].str.contains('인구|계', na=False))].copy()
        df_base['행정구역별'] = df_base['행정구역별'].apply(normalize_region_name)
        
        if 'clicked_region' not in st.session_state:
            st.session_state.clicked_region = "서울특별시"
            
        years_available = sorted(list(df_base['연도'].unique()), reverse=True)
        selected_year = st.selectbox("📅 기준 연도 선택", years_available, index=0)
        
        df_map_agg = df_base[df_base['연도'] == selected_year].groupby('행정구역별')['값'].sum().reset_index()
        df_map_agg = df_map_agg.rename(columns={'행정구역별': '시도별'})
        
        col_map_side, col_chart_side = st.columns([1.1, 0.9])
        
        with col_map_side:
            geo_data = get_korea_geojson()
            m = folium.Map(location=[36.2, 127.8], zoom_start=7, tiles="CartoDB positron")
            
            if geo_data:
                folium.Choropleth(
                    geo_data=geo_data, data=df_map_agg, columns=["시도별", "값"],
                    key_on="feature.properties.name", fill_color="YlOrRd", fill_opacity=0.7, line_opacity=0.8, line_color="white"
                ).add_to(m)
                for key in list(m._children.keys()):
                    if key.startswith('color_scale'): del m._children[key]

            for idx, row in df_map_agg.iterrows():
                region = row['시도별']
                if region in coordinate_map:
                    lat, lon = coordinate_map[region]
                    # 텍스트가 깨지지 않도록 white-space: nowrap 추가 및 그림자 효과 적용
                    html_str = f"""<div style="font-size:12px; font-weight:800; text-align:center; white-space:nowrap; color:#000; text-shadow:-1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;">{region}<br>{int(row['값']):,}명</div>"""
                    folium.map.Marker([lat, lon], icon=folium.DivIcon(icon_size=(120, 40), icon_anchor=(60, 20), html=html_str)).add_to(m)
            
            map_output = st_folium(m, width='stretch', height=550, key="youth_map", returned_objects=["last_active_geojson"])
            
            if map_output and map_output.get("last_active_geojson"):
                new_region = normalize_region_name(map_output["last_active_geojson"]["properties"]["name"])
                if new_region != st.session_state.clicked_region:
                    st.session_state.clicked_region = new_region
                    st.rerun()
        
        current_region = st.session_state.clicked_region
        with col_chart_side:
            st.success(f"📍 현재 지역: **{current_region}**")
            df_region_trend = df_base[df_base['행정구역별'] == current_region].groupby('연도')['값'].sum().reset_index().sort_values('연도')
            if not df_region_trend.empty:
                st.bar_chart(data=df_region_trend, x='연도', y='값', color='#ff4b4b')
                st.dataframe(df_region_trend.rename(columns={'연도': '조회 연도', '값': '인구수'}), hide_index=True, use_container_width=True)
            else:
                st.info("지역을 클릭하면 데이터가 표시됩니다.")

# --- TAB 2: 전공별 추천 지역 분석 ---
with tabs[1]:
    st.subheader("🎯 내 전공에 알맞은 취업 유망 지역 매칭 분석")
    major_mapping = {
        "상경·사회 계열": ["금융", "보험", "전문,과학", "기술서비스", "사업시설관리", "사업지원"],
        "공학 계열": ["제조업", "정보통신업"],
        "의료·보건 계열": ["보건업", "사회복지"],
        "문화·예술·체육 계열": ["예술", "스포츠", "여가", "정보통신업"],
        "서비스·관광 계열": ["도소매업", "숙박", "음식점업"]
    }
    selected_major = st.selectbox("🎓 전공 계열 선택", list(major_mapping.keys()))
    if not df_biz.empty:
        latest_year = sorted(df_biz['연도'].unique(), reverse=True)[0]
        df_target = df_biz[(df_biz['연도'] == latest_year) & (df_biz['사업체구분별'] == '계')]
        df_filtered = df_target[df_target['산업별'].apply(lambda x: any(kw in x for kw in major_mapping[selected_major]))]
        if not df_filtered.empty:
            region_ranking = df_filtered.groupby('행정구역별')['값'].sum().reset_index().sort_values(by='값', ascending=False)
            st.bar_chart(data=region_ranking, x='행정구역별', y='값')
            st.dataframe(region_ranking, use_container_width=True)

# --- TAB 3: 지역별 연령 구조 분석 ---
with tabs[2]:
    st.subheader("목표 지역의 취업 연령대 구조 분석")
    if not df_age_raw.empty:
        region_list = [r for r in df_age_raw['시도별'].unique() if r != '계']
        chosen_region = st.selectbox("📍 분석할 지역 선택", region_list)
        df_age_filt = df_age_raw[(df_age_raw['시도별'] == chosen_region) & (df_age_raw['연령계층별2'] == '소계')]
        if not df_age_filt.empty:
            st.bar_chart(data=df_age_filt, x='연도', y='값', color='연령계층별1')

# --- TAB 4: 지역별 취업시간 패턴 ---
with tabs[3]:
    st.subheader("⏱️ 지역별 근로 시간 스타일 분석")
    if not df_hours_new.empty:
        hr_regions = [r for r in df_hours_new['시도별'].unique() if r != '계']
        sel_hr_reg = st.selectbox("📍 지역 선택", hr_regions)
        df_hr_filt = df_hours_new[df_hours_new['시도별'] == sel_hr_reg]
        st.line_chart(data=df_hr_filt, x='연도', y='값')

# --- TAB 5: 원본 데이터 ---
with tabs[4]:
    st.subheader("원본 데이터셋")
    st.dataframe(df_hours_new, use_container_width=True)
