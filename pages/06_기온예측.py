
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.ticker import MaxNLocator
from pathlib import Path

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="월별 평균기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 평균기온 예측")
st.write(
    "과거 기온 데이터를 이용해 선형회귀 알고리즘으로 "
    "미래의 평균기온을 예측해 보세요!"
)

st.divider()

# ==========================================
# 2. CSV 파일 경로 설정
# ==========================================
# 현재 py 파일은 pages 폴더 안에 있고
# CSV 파일은 pages의 상위 폴더에 있음

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = BASE_DIR / "temperature(1).csv"

# ==========================================
# 3. 한글 폰트 설정
# ==========================================
font_candidates = [
    "Malgun Gothic",
    "NanumGothic",
    "Noto Sans CJK KR",
    "Noto Sans KR"
]

available_fonts = {f.name for f in fm.fontManager.ttflist}

for font in font_candidates:
    if font in available_fonts:
        plt.rcParams["font.family"] = font
        break

plt.rcParams["axes.unicode_minus"] = False

# ==========================================
# 4. 데이터 불러오기
# ==========================================
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(
        file_path,
        encoding="cp949"
    )

    # 날짜 변환
    df["일시"] = pd.to_datetime(
        df["일시"],
        format="%b-%y",
        errors="coerce"
    )

    # 연도와 월 추출
    df["연도"] = df["일시"].dt.year
    df["월"] = df["일시"].dt.month

    # 평균기온 숫자 변환
    df["평균기온(℃)"] = pd.to_numeric(
        df["평균기온(℃)"],
        errors="coerce"
    )

    # 결측치 제거
    df = df.dropna(
        subset=["연도", "월", "평균기온(℃)"]
    )

    df["연도"] = df["연도"].astype(int)
    df["월"] = df["월"].astype(int)

    return df.sort_values("연도").reset_index(drop=True)


if not DATA_PATH.exists():
    st.error(
        f"CSV 파일을 찾을 수 없습니다.\n\n"
        f"확인한 경로: {DATA_PATH}"
    )
    st.stop()

try:
    df = load_data(str(DATA_PATH))

except Exception as e:
    st.error(f"데이터 불러오기 오류: {e}")
    st.stop()

if df.empty:
    st.error("분석할 데이터가 없습니다.")
    st.stop()

# ==========================================
# 5. 데이터 기본 정보
# ==========================================
min_year = int(df["연도"].min())
max_year = int(df["연도"].max())

st.info(
    f"📊 데이터 분석 기간: {min_year}년 ~ {max_year}년 | "
    f"전체 데이터: {len(df):,}개"
)

# ==========================================
# 6. 사용자 입력
# ==========================================
st.subheader("🔎 예측 조건 선택")

col1, col2 = st.columns(2)

with col1:
    month_names = [
        "1월", "2월", "3월", "4월",
        "5월", "6월", "7월", "8월",
        "9월", "10월", "11월", "12월"
    ]

    selected_month_name = st.selectbox(
        "예측할 월을 선택하세요.",
        month_names
    )

    selected_month = month_names.index(
        selected_month_name
    ) + 1

with col2:
    forecast_year = st.number_input(
        "예측할 연도를 입력하세요.",
        min_value=max_year + 1,
        max_value=2100,
        value=max_year + 1,
        step=1
    )

forecast_year = int(forecast_year)

st.divider()

# ==========================================
# 7. 선택한 월의 데이터 추출
# ==========================================
monthly_data = df[
    df["월"] == selected_month
].copy()

monthly_data = monthly_data.sort_values("연도")

if len(monthly_data) < 2:
    st.warning("분석할 데이터가 부족합니다.")
    st.stop()

# X: 연도
# Y: 평균기온
x = monthly_data["연도"].astype(float).values
y = monthly_data["평균기온(℃)"].astype(float).values

# ==========================================
# 8. 선형회귀 알고리즘 계산
# ==========================================
n = len(x)

mean_x = x.mean()
mean_y = y.mean()

# 기울기 계산
numerator = sum(
    (x[i] - mean_x) * (y[i] - mean_y)
    for i in range(n)
)

denominator = sum(
    (x[i] - mean_x) ** 2
    for i in range(n)
)

if denominator == 0:
    st.error("회귀분석을 진행할 수 없습니다.")
    st.stop()

slope = numerator / denominator

# 절편 계산
intercept = mean_y - slope * mean_x

# 예측 함수
def predict(year):
    return slope * year + intercept

# ==========================================
# 9. 미래 기온 예측
# ==========================================
predicted_temp = predict(forecast_year)

# 과거 데이터의 회귀 예측값
predicted_history = [
    predict(year) for year in x
]

# ==========================================
# 10. 결정계수 R² 계산
# ==========================================
ss_total = sum(
    (value - mean_y) ** 2 for value in y
)

ss_residual = sum(
    (y[i] - predicted_history[i]) ** 2
    for i in range(n)
)

if ss_total == 0:
    r_squared = 0
else:
    r_squared = 1 - ss_residual / ss_total

# ==========================================
# 11. 예측 결과 표시
# ==========================================
st.subheader("📈 기온 예측 결과")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "예측 연도",
        f"{forecast_year}년"
    )

with col2:
    st.metric(
        "예상 평균기온",
        f"{predicted_temp:.1f} ℃"
    )

with col3:
    st.metric(
        "결정계수 R²",
        f"{r_squared:.3f}"
    )

st.caption(
    f"선택 월: {selected_month_name} | "
    f"분석 연도 수: {n}년"
)

# 기울기 설명
if slope > 0:
    trend_text = "상승"
elif slope < 0:
    trend_text = "하락"
else:
    trend_text = "변화 없음"

st.write(
    f"📌 과거 데이터의 장기적인 기온 추세는 "
    f"연평균 약 {abs(slope):.3f}℃ {trend_text}하는 경향입니다."
)

st.divider()

# ==========================================
# 12. 선형회귀 그래프
# ==========================================
st.subheader(
    f"📊 {selected_month_name} 연도별 평균기온 및 미래 예측"
)

fig, ax = plt.subplots(figsize=(12, 6))

# 과거 실제 기온 점
ax.scatter(
    x,
    y,
    color="royalblue",
    s=65,
    label="과거 실제 평균기온",
    zorder=3
)

# 선형회귀 직선
line_x = list(
    range(min_year, forecast_year + 1)
)

line_y = [
    predict(year) for year in line_x
]

ax.plot(
    line_x,
    line_y,
    color="red",
    linewidth=2.5,
    label="선형회귀 예측 직선",
    zorder=2
)

# 실제 데이터와 회귀 직선의 오차
for i in range(n):
    ax.plot(
        [x[i], x[i]],
        [y[i], predicted_history[i]],
        color="gray",
        linestyle=":",
        alpha=0.45,
        linewidth=1
    )

# 미래 예측값
ax.scatter(
    forecast_year,
    predicted_temp,
    color="darkorange",
    marker="*",
    s=280,
    edgecolors="black",
    linewidths=0.7,
    label="미래 예측 평균기온",
    zorder=5
)

# 예측값 표시
ax.annotate(
    f"{predicted_temp:.1f}℃",
    xy=(forecast_year, predicted_temp),
    xytext=(8, 12),
    textcoords="offset points",
    fontsize=12,
    fontweight="bold",
    color="darkorange"
)

# 그래프 제목
ax.set_title(
    f"{selected_month_name} 평균기온 선형회귀 분석",
    fontsize=16,
    fontweight="bold"
)

ax.set_xlabel("연도", fontsize=12)
ax.set_ylabel("평균기온 (℃)", fontsize=12)

# 연도 축 자동 조정
ax.xaxis.set_major_locator(
    MaxNLocator(nbins=12, integer=True)
)

ax.grid(
    True,
    linestyle="--",
    alpha=0.35
)

ax.legend(loc="best")

fig.tight_layout()

st.pyplot(fig)

plt.close(fig)

# ==========================================
# 13. 선형회귀 계산 결과
# ==========================================
with st.expander("🔍 선형회귀 계산 결과 자세히 보기"):
    st.write(f"기울기(a): {slope:.5f}")
    st.write(f"절편(b): {intercept:.5f}")

    st.write(
        f"회귀식: y = {slope:.5f}x + {intercept:.5f}"
    )

    st.write(
        f"입력한 연도: {forecast_year}년"
    )

    st.write(
        f"예측 계산: {slope:.5f} × "
        f"{forecast_year} + {intercept:.5f}"
    )

    st.write(
        f"최종 예측 기온: {predicted_temp:.2f}℃"
    )

# ==========================================
# 14. 선형회귀 알고리즘 설명
# ==========================================
st.divider()

st.subheader("🧠 선형회귀 알고리즘 알아보기")

st.write("""
선형회귀는 과거 데이터를 분석하여 두 변수 사이의
관계를 직선으로 나타내고, 이를 이용해 미래의 값을
예측하는 머신러닝 알고리즘입니다.
""")

st.markdown("### ① 데이터 수집")

st.write("""
선택한 월의 과거 연도별 평균기온을 수집합니다.

- X축: 연도
- Y축: 평균기온
""")

st.markdown("### ② 최적의 직선 찾기")

st.write("""
실제 기온 데이터와 예측 직선 사이의 차이를 계산합니다.

각 데이터의 오차를 제곱한 뒤 모두 더한 값이
가장 작아지도록 기울기와 절편을 구합니다.

이 방법을 최소제곱법이라고 합니다.
""")

st.markdown("### ③ 미래 기온 예측")

st.write("""
계산한 직선의 방정식에 사용자가 입력한 미래 연도를
대입하여 예상 평균기온을 계산합니다.
""")

st.latex(r"y = ax + b")

st.write("""
- x: 연도
- y: 예측 평균기온
- a: 기울기
- b: 절편

기울기가 양수이면 기온이 상승하는 경향,
음수이면 하락하는 경향을 의미합니다.
""")

st.markdown("### ④ 그래프 읽는 방법")

st.markdown("""
- 🔵 파란색 점: 과거 실제 평균기온
- 🔴 빨간색 직선: 선형회귀 알고리즘이 계산한 추세선
- 🟠 주황색 별: 미래 예측 평균기온
- 회색 점선: 실제 기온과 회귀 직선 사이의 오차

파란색 점들의 전체적인 분포를 바탕으로
빨간색 직선이 만들어지고, 그 직선을 미래까지
연장하여 주황색 별의 위치를 예측합니다.
""")

st.markdown("### ⑤ 결정계수 R²란?")

st.write("""
결정계수 R²는 회귀 직선이 과거 기온 데이터의 변화를
얼마나 설명하는지 나타내는 지표입니다.

일반적으로 1에 가까울수록 과거 데이터에 대한
설명력이 높다는 의미입니다.

단, R²가 높더라도 미래 예측이 반드시 정확한 것은 아닙니다.
""")

st.warning("""
⚠️ 기온은 온실가스, 기후변화, 자연현상 등 다양한 요인의
영향을 받습니다.

선형회귀는 과거의 추세가 미래에도 이어진다고 가정하므로
실제 미래 기온과 차이가 발생할 수 있습니다.

따라서 이 결과는 실제 기상예보가 아닌
과거 데이터에 기반한 통계적 예측값입니다.
""")

# ==========================================
# 15. 데이터 출처
# ==========================================
st.divider()

st.caption(
    "📌 데이터 출처: 제공된 월별 기온 CSV 파일"
)

st.caption(
    "분석 방법: 단순 선형회귀 / 최소제곱법"
)
