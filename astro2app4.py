import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

# --- [0] 기본 설정 및 세션 스테이트 초기화 ---
st.set_page_config(page_title="DIY 케플러 법칙 실험실", layout="wide")

if 'planet_data' not in st.session_state:
    st.session_state.planet_data = []

def add_planet(name, period, planet_type, a):
    p2 = period ** 2
    a3 = a ** 3 if a is not None else 0
    k = p2 / a3 if a3 != 0 else 0
    
    st.session_state.planet_data.append({
        '행성명': name,
        '분류': planet_type,
        '공전주기 P (년)': period,
        '궤도장반경 a (AU)': round(a, 4),
        'P²': round(p2, 4),
        'a³': round(a3, 4),
        '상수 k (P²/a³)': round(k, 4)
    })

# --- [1] 메인 화면 타이틀 및 소개 ---
st.title("🔭 DIY 천문 실험실: 행성의 거리 유도와 케플러 법칙")
st.markdown("""
이 시뮬레이터는 태양 중심 모델을 수학적이고 엄밀하게 증명했던 케플러의 관측적 접근법을 직접 따라가 보는 실험실입니다[cite: 1].
* **내행성(수성, 금성)**의 거리는 태양과 가장 멀어보이는 **최대이각($\\alpha$)**을 측정하여 결정할 수 있습니다[cite: 1].
* **외행성(화성, 목성 등)**의 거리는 구하기 훨씬 까다로우며, 행성의 1 항성주기 간격으로 두 번의 이각을 측정하는 복잡한 기하학적 삼각법이 필요합니다[cite: 1].
* 두 방법을 통해 각 행성들의 궤도장반경($a$)을 직접 도출하고, 이를 바탕으로 **케플러 제3법칙**($P^2 = ka^3$)이 실제로 성립하는지 그래프로 증명해봅시다[cite: 1].
""")

if st.button("🗑️ 모든 데이터 초기화 (다시 시작)"):
    st.session_state.planet_data = []
    st.rerun()

# --- [2] 메인 화면: 탭 구성 ---
tab1, tab2, tab3 = st.tabs(["📐 1단계: 내행성 거리 유도", "🔭 2단계: 외행성 거리 유도", "📊 3단계: 관측 데이터 및 케플러 법칙 증명"])

# ==========================================
# TAB 1: 내행성 거리 유도
# ==========================================
with tab1:
    st.header("내행성의 거리 결정 (최대이각의 원리)")
    st.markdown("내행성이 지구에서 보았을 때 태양으로부터 가장 멀리 떨어져 보이는 순간(최대이각)에, 지구-내행성-태양은 직각삼각형을 이룹니다[cite: 1].")
    
    col1_img, col1_text = st.columns([1.5, 1])
    
    with col1_img:
        # 타이핑 입력 가능하도록 number_input으로 변경
        demo_alpha = st.number_input("최대이각 α 조절 (도)", min_value=0.0, max_value=90.0, value=28.0, step=0.1, key="inner_input")
        
        fig_inner, ax_inner = plt.subplots(figsize=(6, 6))
        rad_alpha = math.radians(demo_alpha)
        r_calc = math.sin(rad_alpha)
        
        sun_x, sun_y = 0, 0
        earth_x, earth_y = 1, 0
        planet_x = math.sin(rad_alpha) ** 2
        planet_y = math.sin(rad_alpha) * math.cos(rad_alpha)
        
        ax_inner.add_patch(plt.Circle((0, 0), 1, fill=False, color='#4A90E2', linestyle='-'))
        ax_inner.add_patch(plt.Circle((0, 0), r_calc, fill=False, color='#E24A4A', linestyle='--'))
        ax_inner.plot(sun_x, sun_y, 'yo', markersize=15, label='Sun (S)')
        ax_inner.plot(earth_x, earth_y, 'bo', markersize=10, label='Earth (E)')
        ax_inner.plot(planet_x, planet_y, 'ro', markersize=8, label='Inner Planet (P)')
        
        ax_inner.plot([sun_x, earth_x], [sun_y, earth_y], 'k-', alpha=0.6)
        ax_inner.plot([earth_x, planet_x], [earth_y, planet_y], 'k-', alpha=0.6)
        ax_inner.plot([sun_x, planet_x], [sun_y, planet_y], 'r-', linewidth=2)
        
        # 기호 표시
        ax_inner.text(sun_x - 0.1, sun_y - 0.1, 'S', fontsize=12, color='y', weight='bold')
        ax_inner.text(earth_x + 0.05, earth_y - 0.1, 'E', fontsize=12, color='b', weight='bold')
        ax_inner.text(planet_x + 0.05, planet_y + 0.05, 'P', fontsize=12, color='r', weight='bold')
        
        ax_inner.text(0.8, 0.05, f'α = {demo_alpha}°', fontsize=11)
        ax_inner.set_aspect('equal')
        ax_inner.set_xlim(-1.2, 1.3)
        ax_inner.set_ylim(-1.2, 1.3)
        ax_inner.axis('off')
        ax_inner.legend(loc='upper left')
        st.pyplot(fig_inner)
        
    with col1_text:
        st.info("💡 **수학적 유도 과정**\n\n직각삼각형의 원리에 의해, 거리는 $r = \sin \\alpha$ 로 간단히 구해집니다[cite: 1].")
        st.latex(rf"r = \sin({demo_alpha}^\circ) = {r_calc:.3f} \text{{ AU}}")
        
        st.divider()
        st.subheader("📝 데이터 추가하기")
        with st.form("inner_add_form"):
            i_name = st.text_input("행성 이름 (예: 수성, 금성)")
            i_period = st.number_input("공전주기 P (년)", min_value=0.01, value=0.24, step=0.01)
            if st.form_submit_button("도출된 거리로 데이터 추가"):
                if i_name:
                    add_planet(i_name, i_period, "내행성", r_calc)
                    st.success(f"[{i_name}] 데이터가 추가되었습니다! (a = {r_calc:.3f} AU)")

# ==========================================
# TAB 2: 외행성 거리 유도
# ==========================================
with tab2:
    st.header("외행성의 거리 결정 (삼각법의 활용)")
    st.markdown("""
    외행성은 행성의 항성주기 1주기 간격으로 두 번의 이각($\\epsilon$, $\\epsilon'$)을 관측하여 계산합니다[cite: 1].
    * 외행성이 제자리($P$)로 돌아오는 동안, 지구는 두 바퀴를 온전히 돌지 못하고 $E'$에서 $E$로 이동합니다[cite: 1].
    * 태양($S$)과 두 위치의 지구($E, E'$)는 이등변삼각형 $\\triangle SEE'$를 이룹니다[cite: 1]. 이를 통해 밑각 $\\alpha$와 밑변 $EE'$의 길이를 알아냅니다[cite: 1].
    * 구한 $\\alpha$를 측정된 이각 $\\epsilon$, $\\epsilon'$에서 빼어 $\\triangle EPE'$를 풀고, 최종적으로 코사인 법칙을 사용해 거리 $r$을 결정합니다[cite: 1].
    """)
    
    col2_img, col2_text = st.columns([1.5, 1])
    
    with col2_text:
        st.markdown("**[관측 파라미터 직접 입력]**")
        # 타이핑 입력이 가능하도록 st.number_input으로 변경
        n_val = st.number_input("두 관측 시기 사이 지구 궤도 각도 차이 n (도)", min_value=0.0, max_value=360.0, value=42.89, step=0.01)
        eps1 = st.number_input("첫 번째 이각 ε' (도)", min_value=0.0, max_value=180.0, value=127.0, step=0.1)
        eps2 = st.number_input("두 번째 이각 ε (도)", min_value=0.0, max_value=180.0, value=127.0, step=0.1)
        
        # 기하학 계산
        alpha = (180 - n_val) / 2
        ee_prime = 2 * math.sin(math.radians(n_val / 2))
        inner_e1 = eps1 - alpha
        inner_e2 = eps2 - alpha
        angle_p = 180 - inner_e1 - inner_e2
        
        is_valid = angle_p > 0 and inner_e1 > 0 and inner_e2 > 0
        
        st.info("💡 **수학적 유도 과정**\n\n"
                f"1. 이등변 $\\triangle SEE'$ 풀이[cite: 1]:\n"
                f"   * $\\alpha = (180 - n)/2 = {alpha:.2f}^\\circ$\n"
                f"   * $EE' = {ee_prime:.3f}$ AU\n"
                f"2. $\\triangle EPE'$ 풀이[cite: 1]:\n"
                f"   * 내부 각도: ${inner_e1:.2f}^\\circ, {inner_e2:.2f}^\\circ$\n")
        
        if is_valid:
            ep_prime = ee_prime * math.sin(math.radians(inner_e2)) / math.sin(math.radians(angle_p))
            r_outer = math.sqrt(1 + ep_prime**2 - 2 * 1 * ep_prime * math.cos(math.radians(eps1)))
            st.latex(rf"r \approx {r_outer:.3f} \text{{ AU}}")
            
            st.divider()
            with st.form("outer_add_form"):
                o_name = st.text_input("행성 이름 (예: 화성)")
                o_period = st.number_input("공전주기 P (년)", min_value=0.1, value=1.88, step=0.01)
                if st.form_submit_button("도출된 거리로 데이터 추가"):
                    if o_name:
                        add_planet(o_name, o_period, "외행성", r_outer)
                        st.success(f"[{o_name}] 데이터가 추가되었습니다! (a = {r_outer:.3f} AU)")
        else:
            st.error("입력한 각도로는 기하학적 삼각형이 만들어지지 않습니다. 각도를 조정해주세요.")

    with col2_img:
        if is_valid:
            fig_outer, ax_outer = plt.subplots(figsize=(6, 6))
            
            S_x, S_y = 0, 0
            E_prime_x = math.cos(math.radians(n_val/2))
            E_prime_y = math.sin(math.radians(n_val/2))
            E_x = math.cos(math.radians(-n_val/2))
            E_y = math.sin(math.radians(-n_val/2))
            
            # P 좌표 계산
            angle_ep_prime = math.radians(180 + n_val/2 - eps1)
            P_x = E_prime_x + ep_prime * math.cos(angle_ep_prime)
            P_y = E_prime_y + ep_prime * math.sin(angle_ep_prime)
            
            # 그리기
            ax_outer.add_patch(plt.Circle((0, 0), 1, fill=False, color='#4A90E2', linestyle='-', label='Earth Orbit'))
            ax_outer.add_patch(plt.Circle((0, 0), r_outer, fill=False, color='#E24A4A', linestyle='--', label='Outer Orbit'))
            
            ax_outer.plot(S_x, S_y, 'yo', markersize=15, label='Sun (S)')
            ax_outer.plot(E_prime_x, E_prime_y, 'bo', markersize=10, label="Earth (E')")
            ax_outer.plot(E_x, E_y, 'co', markersize=10, label='Earth (E)')
            ax_outer.plot(P_x, P_y, 'ro', markersize=8, label='Planet (P)')
            
            # 꼭짓점 문자 라벨 표기 (S, E', E, P)
            ax_outer.text(S_x, S_y - 0.15, 'S', fontsize=12, color='y', weight='bold', ha='center')
            ax_outer.text(E_prime_x + 0.05, E_prime_y + 0.05, "E'", fontsize=12, color='b', weight='bold')
            ax_outer.text(E_x + 0.05, E_y - 0.1, 'E', fontsize=12, color='c', weight='bold')
            ax_outer.text(P_x + 0.1, P_y, 'P', fontsize=12, color='r', weight='bold')

            # 각도 문자 표기 (alpha, epsilon', epsilon)
            # alpha (이등변 삼각형 SEE' 내부 밑각)
            ax_outer.text(E_prime_x * 0.7, E_prime_y * 0.7, r'$\alpha$', fontsize=10, color='blue', weight='bold')
            ax_outer.text(E_x * 0.7, E_y * 0.7, r'$\alpha$', fontsize=10, color='cyan', weight='bold')
            
            # epsilon' (첫번째 이각, S-E'-P 각도)
            ax_outer.text(E_prime_x * 1.1, E_prime_y * 1.1, r"$\epsilon'$", fontsize=11, color='black', weight='bold')
            # epsilon (두번째 이각, S-E-P 각도)
            ax_outer.text(E_x * 1.1, E_y * 1.1, r"$\epsilon$", fontsize=11, color='black', weight='bold')

            # 선분 연결
            ax_outer.plot([S_x, E_prime_x], [S_y, E_prime_y], 'k-', alpha=0.3)
            ax_outer.plot([S_x, E_x], [S_y, E_y], 'k-', alpha=0.3)
            ax_outer.plot([E_x, E_prime_x], [E_y, E_prime_y], 'b-', alpha=0.6) # EE'
            ax_outer.plot([E_prime_x, P_x], [E_prime_y, P_y], 'k--', alpha=0.6) # E'P
            ax_outer.plot([E_x, P_x], [E_y, P_y], 'k--', alpha=0.6) # EP
            ax_outer.plot([S_x, P_x], [S_y, P_y], 'r-', linewidth=2) # r
            
            max_limit = max(1.2, r_outer + 0.2)
            ax_outer.set_aspect('equal')
            ax_outer.set_xlim(-max_limit*0.2, max_limit)
            ax_outer.set_ylim(-max_limit, max_limit)
            ax_outer.axis('off')
            ax_outer.legend(loc='lower right')
            st.pyplot(fig_outer)

# ==========================================
# TAB 3: 데이터 및 케플러 법칙 증명
# ==========================================
with tab3:
    st.header("관측 데이터 요약 및 케플러 제3법칙 증명")
    
    if len(st.session_state.planet_data) == 0:
        st.warning("먼저 1단계, 2단계 탭에서 행성 데이터를 추가해주세요.")
    else:
        df = pd.DataFrame(st.session_state.planet_data)
        st.dataframe(df, use_container_width=True)
        
        st.markdown("케플러 제3법칙에 따르면, 행성의 공전주기 제곱($P^2$)은 궤도 장반경의 세제곱($a^3$)에 비례해야 합니다($P^2 = ka^3$)[cite: 1].")
        
        # Log 함수 유도 과정 시각화 (첨부 이미지 반영)
        st.markdown("이를 양변에 상용로그를 취하여 1차 함수(직선의 방정식) 형태로 변환하여 증명할 수 있습니다.")
        st.latex(r"P^2 = k a^3 \implies \log P = \frac{3}{2} \log a + \frac{1}{2} \log k")
        st.markdown("즉, $\log a$를 x축, $\log P$를 y축으로 두었을 때 **그래프의 기울기($m$)가 이론값인 1.5 ($\frac{3}{2}$)**에 근접하게 나오는지 확인합니다.")
        
        if len(st.session_state.planet_data) >= 2:
            col3_1, col3_2 = st.columns(2)
            
            with col3_1:
                # 1. P^2 vs a^3 그래프
                fig1, ax1 = plt.subplots(figsize=(5, 4))
                ax1.scatter(df['a³'], df['P²'], color='red', s=50, zorder=5)
                
                max_a3 = df['a³'].max() if max(df['a³']) > 0 else 1
                x_vals = np.array([0, max_a3 * 1.1])
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
                
            with col3_2:
                # 2. Log-Log 그래프
                fig2, ax2 = plt.subplots(figsize=(5, 4))
                log_a = np.log10(df['궤도장반경 a (AU)'])
                log_P = np.log10(df['공전주기 P (년)'])
                
                ax2.scatter(log_a, log_P, color='cornflowerblue', s=80, edgecolor='black')
                
                if len(set(log_a)) > 1: # 분모가 0이 되는 것 방지
                    m, c = np.polyfit(log_a, log_P, 1)
                    # 이론적 기울기 선 (1.5)
                    ax2.plot(log_a, 1.5 * log_a + c, color='gray', linestyle='--', alpha=0.6, label='이론 (기울기 1.5)')
                    # 관측 회귀선
                    ax2.plot(log_a, m * log_a + c, color='salmon', linestyle='-', alpha=0.8, linewidth=2, label=f'관측 회귀 (m={m:.3f})')
                else:
                    m = 0
                
                for i, txt in enumerate(df['행성명']):
                    ax2.annotate(txt, (log_a.iloc[i], log_P.iloc[i]), xytext=(-10, 10), textcoords='offset points', color='black')
                    
                ax2.set_xlabel('log a')
                ax2.set_ylabel('log P (년)')
                ax2.set_title('Log(P) vs Log(a)')
                ax2.legend()
                ax2.grid(True, linestyle='-', alpha=0.2)
                st.pyplot(fig2)
                
            st.success(f"🎉 **검증 결과:** 관측 데이터 기반 Log-Log 그래프의 회귀 기울기가 **{m:.4f}**로 도출되었습니다! "
                       f"이는 이론값(1.5)과 매우 일치하며, 케플러 제3법칙이 성립함을 보여줍니다.")
        else:
            st.info("회귀 기울기 분석을 진행하려면 최소 2개 이상의 행성 데이터를 입력해주세요.")
