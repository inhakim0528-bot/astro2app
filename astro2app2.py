import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

# --- [0] 기본 설정 및 세션 스테이트 초기화 ---
st.set_page_config(page_title="DIY 케플러 법칙 실험실", layout="wide")

if 'planet_data' not in st.session_state:
    st.session_state.planet_data = []

def add_planet(name, period, is_inner, max_elongation=None, semi_major_axis=None):
    if is_inner and max_elongation is not None:
        # 내행성의 거리는 최대이각(alpha)을 통해 r = sin(alpha)로 결정됩니다.
        a = math.sin(math.radians(max_elongation))
    else:
        a = semi_major_axis
        
    p2 = period ** 2
    a3 = a ** 3 if a is not None else 0
    k = p2 / a3 if a3 != 0 else 0
    
    st.session_state.planet_data.append({
        '행성명': name,
        '분류': '내행성' if is_inner else '외행성',
        '공전주기 P (년)': period,
        '최대이각 α (도)': max_elongation if is_inner else '-',
        '궤도장반경 a (AU)': round(a, 4),
        'P²': round(p2, 4),
        'a³': round(a3, 4),
        '상수 k (P²/a³)': round(k, 4)
    })

# --- [1] 메인 화면 구성 ---
st.title("🔭 DIY 천문 실험실: 최대이각과 케플러 법칙 유도")
st.markdown("""
이 시뮬레이터는 관측 데이터를 바탕으로 행성의 궤도 반경을 직접 계산하고, 케플러 법칙을 증명하는 과정을 따라갑니다.
* Kepler는 태양 중심 모델(heliocentric model)을 뒷받침하는 수학적이고 엄밀한 증거를 제시했습니다[cite: 1].
* 내행성(수성과 금성)의 상대적 거리는 최대이각($\\alpha$)을 측정하여 결정할 수 있습니다[cite: 1]. 
* 외행성의 거리를 결정하는 상황은 더 까다로우며, 행성의 1 항성주기 간격으로 분리된 두 번의 관측이 필요합니다[cite: 1].
* 케플러 제3법칙에 따르면 행성의 공전주기 제곱($P^2$)은 궤도 장반경의 세제곱($a^3$)에 비례하며, $P^2 = ka^3$ ($k$는 상수)의 수식으로 표현됩니다[cite: 1].
""")

# --- [2] 사이드바: 데이터 입력 ---
st.sidebar.header("📝 관측 데이터 입력")

st.sidebar.subheader("1. 내행성 데이터 입력")
st.sidebar.markdown("거리는 $r = \sin \\alpha$ 공식을 사용하여 천문단위(AU)로 계산됩니다[cite: 1].")
with st.sidebar.form("inner_planet_form"):
    i_name = st.text_input("행성 이름 (예: 수성, 금성)")
    i_period = st.number_input("공전주기 P (지구 년 단위)", min_value=0.01, value=0.24, step=0.01)
    i_elong = st.number_input("최대이각 α (도)", min_value=0.0, max_value=90.0, value=22.0, step=0.1)
    submit_inner = st.form_submit_button("내행성 추가")
    if submit_inner and i_name:
        add_planet(i_name, i_period, True, max_elongation=i_elong)
        st.sidebar.success(f"{i_name} 추가 완료!")

st.sidebar.divider()

st.sidebar.subheader("2. 외행성 데이터 입력")
st.sidebar.markdown("외행성의 거리 측정은 복잡한 삼각법을 요하므로, 이미 유도된 거리 $a$ (AU) 값을 직접 입력합니다.")
with st.sidebar.form("outer_planet_form"):
    o_name = st.text_input("행성 이름 (예: 화성, 목성)")
    o_period = st.number_input("공전주기 P (지구 년 단위)", min_value=0.1, value=1.88, step=0.1)
    o_axis = st.number_input("궤도장반경 a (AU)", min_value=0.1, value=1.52, step=0.1)
    submit_outer = st.form_submit_button("외행성 추가")
    if submit_outer and o_name:
        add_planet(o_name, o_period, False, semi_major_axis=o_axis)
        st.sidebar.success(f"{o_name} 추가 완료!")

if st.sidebar.button("🗑️ 모든 데이터 초기화"):
    st.session_state.planet_data = []
    st.rerun()

# --- [3] 메인 화면: 데이터 및 그래프 표시 ---
tab1, tab2 = st.tabs(["📊 수집된 관측 데이터", "📈 케플러 제3법칙 분석"])

with tab1:
    st.subheader("관측 및 계산 결과표")
    if st.session_state.planet_data:
        df = pd.DataFrame(st.session_state.planet_data)
        st.dataframe(df, use_container_width=True)
        
        st.info("💡 **확인 포인트:** 모든 행성에서 상수 $k (P^2 / a^3)$ 값이 거의 일정한지 확인해보세요. 일정한 값을 가진다면 케플러 제3법칙이 성립함을 의미합니다.")
    else:
        st.warning("왼쪽 사이드바에서 관측 데이터를 추가해주세요.")

with tab2:
    st.subheader("케플러 제3법칙 (조화의 법칙) 그래프 증명")
    st.markdown("수집된 행성들의 거리($a$)와 공전주기($P$) 데이터를 바탕으로 $P^2 = ka^3$ 비례 관계를 확인합니다[cite: 1].")
    
    if len(st.session_state.planet_data) >= 2:
        df = pd.DataFrame(st.session_state.planet_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 1. P^2 vs a^3 선형 그래프
            fig1, ax1 = plt.subplots(figsize=(5, 4))
            ax1.scatter(df['a³'], df['P²'], color='red', s=50, zorder=5)
            
            # 원점을 지나는 추세선
            x_vals = np.array([0, max(df['a³']) * 1.1])
            mean_k = df['상수 k (P²/a³)'].mean()
            ax1.plot(x_vals, mean_k * x_vals, 'b--', alpha=0.6, label=f'Trend (k≈{mean_k:.2f})')
            
            for i, txt in enumerate(df['행성명']):
                ax1.annotate(txt, (df['a³'].iloc[i], df['P²'].iloc[i]), xytext=(5, 5), textcoords='offset points')
                
            ax1.set_xlabel('a³ (AU³)')
            ax1.set_ylabel('P² (Years²)')
            ax1.set_title('P² vs a³ Relationship')
            ax1.legend()
            ax1.grid(True, linestyle=':', alpha=0.6)
            st.pyplot(fig1)
            
        with col2:
            # 2. Log-Log 그래프 (기울기 확인)
            fig2, ax2 = plt.subplots(figsize=(5, 4))
            log_a = np.log10(df['궤도장반경 a (AU)'])
            log_P = np.log10(df['공전주기 P (년)'])
            
            ax2.scatter(log_a, log_P, color='green', s=50)
            
            # 회귀선 계산
            m, c = np.polyfit(log_a, log_P, 1)
            ax2.plot(log_a, m * log_a + c, 'b--', alpha=0.6, label=f'Slope ≈ {m:.2f}')
            
            for i, txt in enumerate(df['행성명']):
                ax2.annotate(txt, (log_a.iloc[i], log_P.iloc[i]), xytext=(5, 5), textcoords='offset points')
                
            ax2.set_xlabel('log a')
            ax2.set_ylabel('log P')
            ax2.set_title('Log(P) vs Log(a)')
            ax2.legend()
            ax2.grid(True, linestyle=':', alpha=0.6)
            st.pyplot(fig2)
            
        st.success(f"🎉 **분석 결과:** Log-Log 그래프의 기울기가 **약 {m:.2f}**로 도출되었습니다. 이상적인 값인 1.5 ($\log P = 1.5 \log a$)에 가깝다면 수집된 데이터가 케플러의 제3법칙을 잘 따르고 있음을 증명합니다.")
        
    else:
        st.info("정확한 회귀선과 그래프를 분석하려면 최소 2개 이상의 행성 데이터를 입력해주세요. (수성, 금성, 지구, 화성 등을 입력해보세요)")
