"""
Solar Lab — 내행성 최대이각 관측자료 실습
=========================================
NJIT Physics 320, Lecture #4 (Kepler's Laws, Prof. Dale E. Gary) 기반

설계 원칙
---------
1. 앱은 '천문 관측 자료'(날짜 · 동/서방 · 최대이각)만 제공한다.
2. 학생이 그 표를 **직접 읽어서 손으로 입력**한다.
3. 입력한 값만으로 S → T,  sinθ → r,  r의 변동 → a와 e 를 유도한다.
4. 정답(a=0.387 등)은 오차 비교 용도로만 쓰이고, 유도에는 절대 개입하지 않는다.

실행:  streamlit run app.py
"""

import math
from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# 0. 상수 / 제공 자료
# ---------------------------------------------------------------------------
E_DAYS_DEFAULT = 365.25
D2R = math.pi / 180.0
R2D = 180.0 / math.pi

# 비교 전용 실제값 (NASA Planetary Fact Sheet). 유도에 사용되지 않음.
TRUTH = {
    "수성": {"a": 0.387, "e": 0.2056, "T_yr": 0.2408, "S": 115.88},
    "금성": {"a": 0.723, "e": 0.0068, "T_yr": 0.6152, "S": 583.92},
    "화성": {"a": 1.524, "T_yr": 1.8808},
    "목성": {"a": 5.203, "T_yr": 11.862},
    "토성": {"a": 9.537, "T_yr": 29.457},
}

# ── 제공 자료 ① 수성 최대이각 (강의자료 원문, JPL Calendar 2001–2002) ──────────
MERCURY_EVENTS = [
    ("2001-09-18", "동방", 26.0),
    ("2001-10-29", "서방", 18.0),
    ("2002-01-12", "동방", 19.0),
    ("2002-02-21", "서방", 27.0),
    ("2002-05-04", "동방", 20.0),
    ("2002-06-21", "서방", 22.0),
]

# ── 제공 자료 ② 금성 최대이각 (JPL 기준 근사값) ──────────────────────────────
VENUS_EVENTS = [
    ("2020-03-24", "동방", 46.1),
    ("2020-08-13", "서방", 45.8),
    ("2021-10-29", "동방", 47.0),
    ("2022-03-20", "서방", 46.6),
    ("2023-06-04", "동방", 45.4),
    ("2023-10-23", "서방", 46.4),
    ("2025-01-10", "동방", 47.2),
    ("2025-06-01", "서방", 45.9),
]

# ── 제공 자료 ③ 외행성 관측표 (케플러 검증 탭에서 함께 사용) ──────────────────
OUTER_OBS = [
    {"행성": "화성", "회합주기 S (일)": 779.94, "충→구 t (일)": 106.0},
    {"행성": "목성", "회합주기 S (일)": 398.88, "충→구 t (일)": 87.4},
    {"행성": "토성", "회합주기 S (일)": 378.09, "충→구 t (일)": 88.2},
]

EMPTY_ROWS = pd.DataFrame(
    {"날짜": [None] * 6, "방향": [None] * 6, "최대이각 θ (°)": [None] * 6}
)


# ---------------------------------------------------------------------------
# 1. 유도 함수
# ---------------------------------------------------------------------------
def synodic_from_events(df):
    """같은 방향(동방↔동방, 서방↔서방)의 연속된 최대이각 사이 간격 = 회합주기 S."""
    intervals = []
    for direction in ("동방", "서방"):
        sub = df[df["방향"] == direction].sort_values("날짜")
        ds = sub["날짜"].tolist()
        for i in range(len(ds) - 1):
            gap = (ds[i + 1] - ds[i]).days
            if gap > 0:
                intervals.append({"방향": direction, "이전": ds[i], "다음": ds[i + 1], "간격 (일)": gap})
    return pd.DataFrame(intervals)


def sidereal_from_synodic(S, E=E_DAYS_DEFAULT):
    """내행성:  1/T = 1/E + 1/S"""
    if S is None or S <= 0:
        return None
    return 1.0 / (1.0 / E + 1.0 / S)


def radius_from_elongation(theta_deg):
    """최대이각 순간에는 ∠(태양-행성-지구) = 90°  →  r = 1 AU × sin θ"""
    return math.sin(theta_deg * D2R)


def orbit_from_radii(r_list):
    """r 의 최댓값·최솟값 = 원일점 · 근일점 거리
       a = (r_max + r_min) / 2,   e = (r_max - r_min) / (r_max + r_min)
    """
    r_max, r_min = max(r_list), min(r_list)
    a = (r_max + r_min) / 2.0
    e = (r_max - r_min) / (r_max + r_min) if (r_max + r_min) > 0 else 0.0
    return a, e, r_max, r_min


def earth_longitude(d):
    """날짜(datetime.date) → 지구의 태양중심 황경(deg). J2000 기준 선형근사."""
    days = (d - date(2000, 1, 1)).days - 0.5
    return (100.46 + 0.98564736 * days) % 360.0


def sight_line(d, theta_deg, direction):
    """관측일 d, 최대이각 θ, 동/서방 → (지구 위치, 시선 방향, 접점=행성 위치).

    지구는 황경 λE 의 단위원 위. 태양의 겉보기 황경 λS = λE + 180°.
    동방이각이면 행성의 겉보기 황경 = λS + θ, 서방이면 λS − θ.
    그 시선 위에서 태양에 가장 가까운 점이 곧 최대이각 순간의 행성 위치.
    """
    lam_E = earth_longitude(d)
    Ex, Ey = math.cos(lam_E * D2R), math.sin(lam_E * D2R)
    lam_S = lam_E + 180.0
    lam_P = lam_S + (theta_deg if direction == "동방" else -theta_deg)
    dx, dy = math.cos(lam_P * D2R), math.sin(lam_P * D2R)
    s = -(Ex * dx + Ey * dy)           # 원점에서 시선에 내린 수선의 발까지의 거리
    Px, Py = Ex + s * dx, Ey + s * dy  # 행성 위치 (|OP| = sin θ 가 자동으로 성립)
    return (Ex, Ey), (dx, dy), (Px, Py)


def a_outer_from_quadrature(t_days, S_days):
    """외행성: Δ = 360·t/S,  a = 1/cos Δ"""
    delta = 360.0 * t_days / S_days
    if not (0 < delta < 90):
        return None
    return 1.0 / math.cos(delta * D2R)


def fit_loglog(a_list, T_list):
    x = np.log10(np.asarray(a_list, float))
    y = np.log10(np.asarray(T_list, float))
    m, b = np.polyfit(x, y, 1)
    yh = m * x + b
    ss_res = float(np.sum((y - yh) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return float(m), float(b), (1 - ss_res / ss_tot if ss_tot > 0 else float("nan"))


# ---------------------------------------------------------------------------
# 2. 페이지
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Solar Lab — 내행성 최대이각 실습", layout="wide")
st.title("🔭 Solar Lab — 내행성 최대이각 관측 실습")
st.caption(
    "제공된 **최대이각 관측 목록**을 직접 읽어 입력하면, 그 값만으로 회합주기 → 공전주기, "
    "그리고 sinθ 의 변동으로부터 궤도 반경 $a$ 와 이심률 $e$ 까지 유도합니다. "
    "(NJIT Physics 320, Lecture #4)"
)

with st.sidebar:
    st.header("⚙️ 설정")
    planet = st.radio("관측 대상", ["수성", "금성"], horizontal=True)
    E_days = st.number_input("지구 공전주기 E (일)", value=E_DAYS_DEFAULT, min_value=1.0,
                             step=0.01, format="%.2f")
    show_truth = st.checkbox("실제값과 비교", value=True)
    st.divider()
    st.markdown(
        "**실습 순서**\n\n"
        "1. ① 탭에서 관측 목록을 **눈으로 읽는다**\n"
        "2. ② 탭에 **직접 손으로 옮겨 적는다**\n"
        "3. 앱이 입력값만으로 $S,\\;T,\\;r,\\;a,\\;e$ 를 유도한다\n"
        "4. ③④ 탭에서 궤도 모양과 케플러 법칙을 확인한다"
    )

SRC = MERCURY_EVENTS if planet == "수성" else VENUS_EVENTS
key_df = f"input_{planet}"
if key_df not in st.session_state:
    st.session_state[key_df] = EMPTY_ROWS.copy()

t1, t2, t3, t4 = st.tabs(
    ["① 제공 천문 자료", "② 직접 입력 → 유도", "③ 궤도 복원", "④ 케플러 제3법칙"]
)

# ---------------------------------------------------------------------------
# ① 제공 자료 (읽기 전용)
# ---------------------------------------------------------------------------
with t1:
    st.subheader(f"📚 {planet} 최대이각 관측 목록")
    st.markdown(
        "아래 표는 **관측 결과만** 담고 있습니다. 거리도, 주기도 적혀 있지 않습니다. "
        "이 세 개의 열(날짜 · 방향 · 각도)만 보고 ② 탭에 옮겨 적으세요."
    )
    src_df = pd.DataFrame(SRC, columns=["날짜", "방향", "최대이각 θ (°)"])
    st.dataframe(src_df, use_container_width=True, hide_index=True)

    if planet == "수성":
        st.info(
            "📄 이 표는 강의자료(Lecture #4)에 실린 JPL Calendar 2001–2002 수성 최대이각 목록 그대로입니다. "
            "**이각이 18°에서 27°까지 들쭉날쭉하다는 점**을 눈여겨보세요. 이게 이 실습의 핵심입니다."
        )
    else:
        st.info(
            "💡 금성은 이각이 45°~47° 로 거의 일정합니다. 왜 수성과 다를까요? "
            "② 탭에서 $e$ 를 구해 보면 답이 나옵니다."
        )

    with st.expander("외행성 관측표 (④ 탭 케플러 검증에 함께 사용)"):
        st.dataframe(pd.DataFrame(OUTER_OBS), use_container_width=True, hide_index=True)
        st.caption("외행성은 최대이각이 없으므로 '충 → 구' 까지 걸린 시간 t 로 a = 1/cos(360·t/S) 를 씁니다.")

# ---------------------------------------------------------------------------
# ② 직접 입력 → 유도
# ---------------------------------------------------------------------------
with t2:
    st.subheader("✍️ 관측 자료 직접 입력")

    c1, c2 = st.columns([1, 4])
    if c1.button("표 비우기", use_container_width=True):
        st.session_state[key_df] = EMPTY_ROWS.copy()
        st.rerun()
    if c2.button("😅 도저히 못 하겠으면 — 자동 채우기", use_container_width=False):
        st.session_state[key_df] = pd.DataFrame(SRC, columns=["날짜", "방향", "최대이각 θ (°)"])
        st.session_state[key_df]["날짜"] = pd.to_datetime(st.session_state[key_df]["날짜"]).dt.date
        st.rerun()

    edited = st.data_editor(
        st.session_state[key_df],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "날짜": st.column_config.DateColumn("관측 날짜", format="YYYY-MM-DD"),
            "방향": st.column_config.SelectboxColumn("방향", options=["동방", "서방"]),
            "최대이각 θ (°)": st.column_config.NumberColumn(
                "최대이각 θ (°)", min_value=0.0, max_value=90.0, step=0.1, format="%.1f"
            ),
        },
        key=f"editor_{planet}",
    )
    st.session_state[key_df] = edited

    valid = edited.dropna(subset=["날짜", "방향", "최대이각 θ (°)"]).copy()
    if valid.empty:
        st.info("위 표에 관측값을 입력하면 아래에 유도 과정이 나타납니다.")
        st.stop()

    valid["날짜"] = pd.to_datetime(valid["날짜"]).dt.date
    valid = valid.sort_values("날짜").reset_index(drop=True)
    valid["r = sin θ (AU)"] = valid["최대이각 θ (°)"].apply(radius_from_elongation)

    st.divider()

    # ── 1단계 : 회합주기 ──────────────────────────────────────────────
    st.markdown("### 1단계 · 같은 방향 이각의 반복 간격 → 회합주기 $S$")
    iv = synodic_from_events(valid)
    if iv.empty:
        st.warning("같은 방향(동방↔동방 또는 서방↔서방) 관측이 2개 이상 있어야 S 를 구할 수 있습니다.")
        S_est = st.number_input("회합주기 S 를 직접 입력 (일)", value=115.88, min_value=1.0)
    else:
        st.dataframe(iv, use_container_width=True, hide_index=True)
        S_est = float(iv["간격 (일)"].mean())
        cA, cB = st.columns(2)
        cA.metric("측정 간격 평균 = 회합주기 S", f"{S_est:.2f} 일",
                  delta=f"± {iv['간격 (일)'].std():.2f} (표준편차)" if len(iv) > 1 else None)
        if show_truth and planet in TRUTH:
            cB.metric("실제 S", f"{TRUTH[planet]['S']:.2f} 일",
                      delta=f"{S_est - TRUTH[planet]['S']:+.2f} 일 오차")

    # ── 2단계 : 공전주기 ──────────────────────────────────────────────
    st.markdown("### 2단계 · 회합주기 → 공전주기 $T$")
    st.latex(r"\frac{1}{T}=\frac{1}{E}+\frac{1}{S}\qquad(\text{내행성})")
    T_days = sidereal_from_synodic(S_est, E_days)
    T_yr = T_days / E_days
    cA, cB = st.columns(2)
    cA.metric("유도된 공전주기 T", f"{T_days:.2f} 일  ({T_yr:.4f} 년)")
    if show_truth and planet in TRUTH:
        true_T = TRUTH[planet]["T_yr"] * E_days
        cB.metric("실제 T", f"{true_T:.2f} 일",
                  delta=f"{(T_days - true_T) / true_T * 100:+.2f} %")

    # ── 3단계 : 각 관측 → 거리 ────────────────────────────────────────
    st.markdown("### 3단계 · 각 최대이각 → 그 순간의 태양–행성 거리 $r$")
    st.latex(r"\text{최대이각에서}\ \angle(\text{태양–행성–지구})=90^\circ \;\Rightarrow\; r = 1\,\text{AU}\times\sin\theta")
    st.dataframe(
        valid[["날짜", "방향", "최대이각 θ (°)", "r = sin θ (AU)"]].style.format({"r = sin θ (AU)": "{:.4f}"}),
        use_container_width=True, hide_index=True,
    )

    # ── 4단계 : r 의 변동 → a, e ──────────────────────────────────────
    st.markdown("### 4단계 · $r$ 이 일정하지 않다 → 궤도는 원이 아니다")
    a_der, e_der, r_max, r_min = orbit_from_radii(valid["r = sin θ (AU)"].tolist())
    st.latex(r"a=\frac{r_{\max}+r_{\min}}{2},\qquad e=\frac{r_{\max}-r_{\min}}{r_{\max}+r_{\min}}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("원일점 r_max", f"{r_max:.4f} AU")
    m2.metric("근일점 r_min", f"{r_min:.4f} AU")
    m3.metric("궤도 반경 a", f"{a_der:.4f} AU",
              delta=f"{(a_der - TRUTH[planet]['a']) / TRUTH[planet]['a'] * 100:+.2f} %" if show_truth else None)
    m4.metric("이심률 e", f"{e_der:.4f}",
              delta=f"실제 {TRUTH[planet]['e']:.4f}" if show_truth else None, delta_color="off")

    if e_der > 0.1:
        st.success(
            f"🎯 **{planet}의 궤도는 뚜렷한 타원입니다.** 최대이각이 {valid['최대이각 θ (°)'].min():.0f}°~"
            f"{valid['최대이각 θ (°)'].max():.0f}° 로 변한다는 사실 하나에서 $e = {e_der:.3f}$ 이 나왔습니다. "
            "케플러가 제1법칙에 도달한 논리가 바로 이것입니다."
        )
    else:
        st.success(
            f"✅ **{planet}의 궤도는 거의 완전한 원입니다** ($e = {e_der:.4f}$). "
            "그래서 최대이각이 언제 재도 거의 같은 값이 나옵니다."
        )
    st.caption(
        "⚠️ 관측 횟수가 적으면 진짜 원일점·근일점을 놓치기 쉽습니다. "
        "표에 행을 더 추가할수록 $a$ 와 $e$ 가 실제값에 가까워집니다."
    )

    # 결과를 다른 탭에 전달
    st.session_state["derived"] = {
        "planet": planet, "S": S_est, "T_days": T_days, "T_yr": T_yr,
        "a": a_der, "e": e_der, "obs": valid,
    }

# ---------------------------------------------------------------------------
# ③ 궤도 복원 — 강의자료의 애니메이션 재현
# ---------------------------------------------------------------------------
with t3:
    st.subheader("🛰️ 시선 작도로 궤도 복원하기")
    d = st.session_state.get("derived")
    if not d or d["planet"] != planet:
        st.info("② 탭에서 먼저 관측값을 입력하세요.")
    else:
        st.markdown(
            "강의자료의 그림을 그대로 재현합니다. **관측 날짜마다 지구를 궤도 위 제 위치에 놓고**, "
            "태양에서 동/서로 θ 만큼 벌어진 시선을 그은 뒤, 그 시선이 **태양에 가장 가까이 지나는 점**을 찍습니다. "
            "그 점이 곧 그때의 행성 위치입니다."
        )
        obs = d["obs"]
        fig = go.Figure()

        th = np.linspace(0, 2 * np.pi, 240)
        fig.add_trace(go.Scatter(x=np.cos(th), y=np.sin(th), mode="lines", name="지구 궤도",
                                 line=dict(color="#4A90E2", dash="dot", width=1)))
        fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers+text", text=["태양"],
                                 textposition="bottom center",
                                 marker=dict(size=18, color="#FFD24A"), name="태양"))

        px_all, py_all = [], []
        for _, row in obs.iterrows():
            (Ex, Ey), _, (Px, Py) = sight_line(row["날짜"], row["최대이각 θ (°)"], row["방향"])
            px_all.append(Px)
            py_all.append(Py)
            col = "#F5A623" if row["방향"] == "동방" else "#7ED321"
            # 시선 (지구에서 행성 너머까지 조금 연장)
            ext = 1.15
            fig.add_trace(go.Scatter(
                x=[Ex, Ex + (Px - Ex) * ext], y=[Ey, Ey + (Py - Ey) * ext],
                mode="lines", line=dict(color=col, width=1), opacity=0.55,
                showlegend=False, hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=[Ex], y=[Ey], mode="markers",
                marker=dict(size=8, color="#4A90E2"), showlegend=False,
                hovertext=f"{row['날짜']} 지구", hoverinfo="text",
            ))
            fig.add_trace(go.Scatter(
                x=[Px], y=[Py], mode="markers",
                marker=dict(size=11, color=col, line=dict(width=1, color="white")),
                showlegend=False,
                hovertext=f"{row['날짜']} · {row['방향']} {row['최대이각 θ (°)']}° · r={math.hypot(Px,Py):.3f} AU",
                hoverinfo="text",
            ))

        # 유도된 a 로 그린 원 궤도 (비교용)
        fig.add_trace(go.Scatter(x=d["a"] * np.cos(th), y=d["a"] * np.sin(th), mode="lines",
                                 name=f"유도된 평균 궤도 a={d['a']:.3f} AU",
                                 line=dict(color="#E24A4A", dash="dash", width=1)))
        fig.add_trace(go.Scatter(x=px_all, y=py_all, mode="markers", name=f"{planet} (복원된 위치)",
                                 marker=dict(size=1, color="rgba(0,0,0,0)")))

        fig.update_layout(
            xaxis=dict(range=[-1.35, 1.35], visible=False),
            yaxis=dict(range=[-1.35, 1.35], visible=False, scaleanchor="x", scaleratio=1),
            template="plotly_dark", height=620,
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0.3)"),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("주황 = 동방이각(저녁 서쪽 하늘), 초록 = 서방이각(새벽 동쪽 하늘). 점에 마우스를 올리면 r 이 나옵니다.")

        # r 변화 그래프
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=obs["날짜"], y=obs["r = sin θ (AU)"], mode="markers+lines",
            marker=dict(size=11, color="#E24A4A"), name="관측에서 유도한 r",
        ))
        fig2.add_hline(y=d["a"], line_dash="dash", line_color="#888",
                       annotation_text=f"평균 a = {d['a']:.3f} AU")
        fig2.update_layout(xaxis_title="관측 날짜", yaxis_title="태양–행성 거리 r (AU)",
                           template="plotly_dark", height=340)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown(
            f"$r$ 이 평균선 위아래로 흔들리는 폭이 곧 이심률입니다. "
            f"**{planet}: $e = {d['e']:.4f}$**"
        )

# ---------------------------------------------------------------------------
# ④ 케플러 제3법칙
# ---------------------------------------------------------------------------
with t4:
    st.subheader("📈 케플러 제3법칙 검증")
    d = st.session_state.get("derived")
    if not d:
        st.info("② 탭에서 먼저 내행성 관측값을 입력하세요.")
    else:
        rows = [{"행성": d["planet"], "a (AU)": d["a"], "T (년)": d["T_yr"], "출처": "내가 입력한 최대이각"}]
        for o in OUTER_OBS:
            S = o["회합주기 S (일)"]
            a = a_outer_from_quadrature(o["충→구 t (일)"], S)
            T_yr = (1.0 / (1.0 / E_days - 1.0 / S)) / E_days
            rows.append({"행성": o["행성"], "a (AU)": a, "T (년)": T_yr, "출처": "제공된 외행성 관측표"})
        kdf = pd.DataFrame(rows)
        kdf["T²/a³"] = kdf["T (년)"] ** 2 / kdf["a (AU)"] ** 3

        st.dataframe(
            kdf.style.format({"a (AU)": "{:.4f}", "T (년)": "{:.4f}", "T²/a³": "{:.4f}"}),
            use_container_width=True, hide_index=True,
        )

        m, b, r2 = fit_loglog(kdf["a (AU)"], kdf["T (년)"])
        c1, c2, c3 = st.columns(3)
        c1.metric("회귀 기울기 m", f"{m:.4f}", delta=f"{m - 1.5:+.4f} (이론 1.5)")
        c2.metric("결정계수 R²", f"{r2:.5f}")
        c3.metric("T²/a³ 평균", f"{kdf['T²/a³'].mean():.4f}")

        st.latex(r"T^2 = k\,a^3 \;\Longrightarrow\; \log T = \tfrac{3}{2}\log a + \tfrac{1}{2}\log k")

        xs = np.log10(kdf["a (AU)"].to_numpy(float))
        ys = np.log10(kdf["T (년)"].to_numpy(float))
        xl = np.linspace(xs.min() - 0.15, xs.max() + 0.15, 40)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=xl, y=1.5 * xl, mode="lines", name="이론 (기울기 1.5)",
                                 line=dict(color="#888", dash="dash")))
        fig.add_trace(go.Scatter(x=xl, y=m * xl + b, mode="lines", name=f"관측 회귀 (m={m:.3f})",
                                 line=dict(color="#E24A4A", width=2)))
        colors = ["#F5A623" if s.startswith("내가") else "#4A90E2" for s in kdf["출처"]]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=kdf["행성"],
                                 textposition="top left", name="행성",
                                 marker=dict(size=14, color=colors, line=dict(width=1, color="white"))))
        fig.update_layout(xaxis_title="log₁₀ a (AU)", yaxis_title="log₁₀ T (년)",
                          template="plotly_dark", height=520,
                          legend=dict(x=0.02, y=0.98))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("주황 점이 여러분이 직접 입력한 최대이각에서 나온 값입니다. 이론선 위에 얹히나요?")
