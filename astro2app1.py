import streamlit as st
import numpy as np
import math
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# --- [0] 기본 상수 및 데이터 (astro.js 포팅) ---
D2R = math.pi / 180
R2D = 180 / math.pi
OBLIQ = 23.4393 * D2R
E_YEAR = 365.25

def norm360(x):
    return ((x % 360) + 360) % 360

# J2000 기준 원궤도 근사. L0 = 평균황경(deg) @ J2000
PLANETS = {
    'mercury': {'a': 0.387, 'T': 0.2408, 'L0': 252.25, 'name': '수성', 'inner': True},
    'venus':   {'a': 0.723, 'T': 0.6152, 'L0': 181.98, 'name': '금성', 'inner': True},
    'earth':   {'a': 1.000, 'T': 1.0000, 'L0': 100.46, 'name': '지구', 'inner': None},
    'mars':    {'a': 1.524, 'T': 1.8808, 'L0': 355.43, 'name': '화성', 'inner': False},
    'jupiter': {'a': 5.203, 'T': 11.862, 'L0': 34.40,  'name': '목성', 'inner': False},
    'saturn':  {'a': 9.537, 'T': 29.457, 'L0': 50.08,  'name': '토성', 'inner': False},
}

# --- [1] 천문 계산 로직 (astro.js / derive.js 포팅) ---
def days_since_j2000(dt):
    # J2000: 2000-01-01 12:00 UTC
    j2000 = datetime(2000, 1, 1, 12, 0, 0)
    delta = dt - j2000
    return delta.total_seconds() / 86400.0

def helio_lon(p, d):
    """태양 중심 황경 (deg)"""
    return norm360(PLANETS[p]['L0'] + 360 * d / (PLANETS[p]['T'] * 365.25))

def helio_xy(p, d):
    """태양 중심 직교좌표 (AU, 황도면)"""
    L = helio_lon(p, d) * D2R
    a = PLANETS[p]['a']
    return {'x': a * math.cos(L), 'y': a * math.sin(L)}

def geo_lon(p, d):
    """지구에서 본 겉보기 황경 (deg)"""
    P = helio_xy(p, d)
    E = helio_xy('earth', d)
    return norm360(math.atan2(P['y'] - E['y'], P['x'] - E['x']) * R2D)

def sun_lon(d):
    """태양의 겉보기 황경"""
    return norm360(helio_lon('earth', d) + 180)

def elongation(p, d):
    """이각: 태양과 행성의 겉보기 각거리. +동방 / −서방"""
    e = geo_lon(p, d) - sun_lon(d)
    return ((e + 540) % 360) - 180

def distance_au(p, d):
    """지구-행성 거리 (AU)"""
    P = helio_xy(p, d)
    E = helio_xy('earth', d)
    return math.hypot(P['x'] - E['x'], P['y'] - E['y'])

def phase(p, d):
    """위상: 밝은 면 비율 k (0=신월, 1=만월)"""
    a = PLANETS[p]['a']
    r = distance_au(p, d)
    R = 1.0
    cos_psi = (a * a + r * r - R * R) / (2 * a * r)
    return (1 + cos_psi) / 2

def orbital_period(S, is_inner):
    """회합주기(S)를 이용한 공전주기(T) 유도"""
    inv_T = (1 / E_YEAR + 1 / S) if is_inner else (1 / E_YEAR - 1 / S)
    return 1 / (inv_T * E_YEAR)

def radius_inner(max_elong_deg):
    """최대이각을 이용한 내행성 궤도 반경 (AU) 유도"""
    return math.sin(max_elong_deg * D2R)

def kepler_slope(points):
    """케플러 3법칙: log-log 회귀 기울기"""
    sxy = 0; sxx = 0
    for pt in points:
        x = math.log10(pt['a'])
        y = math.log10(pt['T'])
        sxy += x * y
        sxx += x * x
    return sxy / sxx if sxx != 0 else 0


# --- [2] Streamlit 앱 페이지 설정 ---
st.set_page_config(page_title="Solar Lab: 천문 역학 시뮬레이터", layout="wide")
st.title("🔭 Solar Lab: 천문 역학 및 케플러 법칙 시뮬레이터")
st.markdown("지구과학2 교과 연계: 회합주기와 최대이각 관측 데이터를 바탕으로 행성의 궤도 반경과 케플러 제3법칙을 증명합니다.")

# --- [3] 사이드바: 관측 설정 ---
st.sidebar.header("🧭 관측 설정 (Controls)")

# 날짜 선택
target_date = st.sidebar.date_input("관측 날짜 선택", datetime.today())
d_since_j2000 = days_since_j2000(datetime.combine(target_date, datetime.min.time()))

# 행성 선택
target_planet_key = st.sidebar.selectbox(
    "관측 대상 행성", 
    [k for k in PLANETS.keys() if k != 'earth'], 
    format_func=lambda x: PLANETS[x]['name']
)
p_data = PLANETS[target_planet_key]

st.sidebar.divider()
st.sidebar.subheader("관측자 정보 (가정)")
st.sidebar.text("위치: 태양계 북극 상공 (Top View)")
st.sidebar.text(f"기준일 (J2000): {d_since_j2000:.1f}일 경과")


# --- [4] 메인 화면: 탭 구성 ---
tab1, tab2, tab3 = st.tabs(["궤도 시각화 (Top View)", "관측 데이터 (수학적 유도)", "📝 관측 노트 (의견)"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"태양계 궤도 및 이각 시각화 ({p_data['name']})")
        
        # Matplotlib을 이용한 Top View 그리기
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_facecolor('#0E1117')
        fig.patch.set_facecolor('#0E1117')
        
        # 태양
        ax.plot(0, 0, 'yo', markersize=15, label='Sun (태양)')
        
        # 궤도 그리기 (원 궤도 근사)
        earth_circle = plt.Circle((0,0), radius=1.0, fill=False, color='#4A90E2', linestyle='--', alpha=0.6)
        planet_circle = plt.Circle((0,0), radius=p_data['a'], fill=False, color='#E24A4A', linestyle='--', alpha=0.6)
        ax.add_patch(earth_circle)
        ax.add_patch(planet_circle)
        
        # 행성 위치 계산
        E = helio_xy('earth', d_since_j2000)
        P = helio_xy(target_planet_key, d_since_j2000)
        
        ax.plot(E['x'], E['y'], 'bo', markersize=8, label='Earth (지구)')
        ax.plot(P['x'], P['y'], 'ro', markersize=8, label=f"{p_data['name']}")
        
        # 시선 방향 (이각) 선 그리기
        ax.plot([E['x'], P['x']], [E['y'], P['y']], color='white', linestyle='-', alpha=0.5) # 지구-행성
        ax.plot([E['x'], 0], [E['y'], 0], color='yellow', linestyle='-', alpha=0.5) # 지구-태양
        
        # 설정 축
        ax.set_aspect('equal')
        max_limit = max(1.2, p_data['a'] + 0.2)
        ax.set_xlim(-max_limit, max_limit)
        ax.set_ylim(-max_limit, max_limit)
        ax.legend(loc='upper right', facecolor='black', labelcolor='white')
        ax.axis('off')
        
        st.pyplot(fig)

    with col2:
        st.subheader("실시간 물리량")
        current_elong = elongation(target_planet_key, d_since_j2000)
        dist = distance_au(target_planet_key, d_since_j2000)
        ph = phase(target_planet_key, d_since_j2000)
        
        st.metric(label="현재 이각 (Elongation)", value=f"{current_elong:.2f}°")
        st.metric(label="지구로부터 거리", value=f"{dist:.3f} AU")
        st.metric(label="위상 (Phase, 0~1)", value=f"{ph:.3f}")
        
        if p_data['inner']:
            st.info("💡 **내행성 관측:** 현재 이각이 동방(양수)이면 해진 후 서쪽 하늘에서, 서방(음수)이면 해뜨기 전 동쪽 하늘에서 보입니다.")
        else:
            st.info("💡 **외행성 관측:** 외행성은 최대이각이 존재하지 않으며, 이각이 180도일 때 '충'에 위치하여 밤새도록 관측 가능합니다.")

with tab2:
    st.header("수학적 유도 과정 (지구과학2 연계)")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("1. 궤도 반지름 유도 (최대이각)")
        if p_data['inner']:
            # 임의로 해당 행성의 최대 이각을 수식 계산을 위해 역산 
            max_e = math.asin(p_data['a']) * R2D
            st.markdown(f"**{p_data['name']}**의 평균 최대이각을 관측했다고 가정합니다: **$\\theta \\approx {max_e:.1f}^\\circ$**")
            st.latex(r"a = 1\text{AU} \times \sin(\theta)")
            calc_a = radius_inner(max_e)
            st.success(f"계산된 궤도 반지름 ($a$): **{calc_a:.3f} AU** (실제: {p_data['a']} AU)")
        else:
            st.warning("외행성은 최대이각을 통해 거리를 구하지 않고, 충에서 구(Quadrature)까지 걸리는 시간 등을 이용하여 공전 궤도 반경을 유도합니다.")

    with col_b:
        st.subheader("2. 케플러 제3법칙 (조화의 법칙)")
        st.markdown("수집된 행성들의 거리($a$)와 공전주기($T$) 데이터를 바탕으로 $T^2 = a^3$ 비례 관계를 확인합니다.")
        
        pts = [{'a': v['a'], 'T': v['T']} for k, v in PLANETS.items() if k != 'earth']
        slope = kepler_slope(pts)
        
        st.latex(r"\log T = \frac{3}{2} \log a")
        st.metric(label="계산된 회귀 기울기 (이상적인 값: 1.50)", value=f"{slope:.3f}")
        
        if abs(slope - 1.5) < 0.05:
            st.success("🎉 케플러 제3법칙이 완벽하게 성립함을 수치적으로 증명했습니다!")

with tab3:
    st.header("💬 관측 노트 및 코멘트")
    st.markdown("위 시뮬레이터를 통해 알게 된 케플러 법칙이나 이각 변화에 대한 깨달음을 남겨보세요.")
    
    if "obs_comments" not in st.session_state:
        st.session_state.obs_comments = []

    with st.form(key="obs_form"):
        name = st.text_input("관측자 이름")
        comment = st.text_area("관측 일지 내용")
        submitted = st.form_submit_button("일지 저장")

        if submitted:
            if name.strip() and comment.strip():
                st.session_state.obs_comments.append((name.strip(), comment.strip()))
                st.success("관측 일지가 저장되었습니다.")
            else:
                st.warning("이름과 내용을 모두 입력해주세요.")

    if st.session_state.obs_comments:
        st.divider()
        st.subheader("📋 전체 관측 일지")
        for i, (n, c) in enumerate(reversed(st.session_state.obs_comments), 1):
            st.markdown(f"**{i}. {n}**: {c}")
