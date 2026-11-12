
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

DATA_PATH = BASE_DIR / "temperature.csv"

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

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

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
    "과거 기온 데이터를 이용하여 다양한 회귀 알고리즘으로 "
    "미래의 평균기온을 예측해 보세요!"
)

st.divider()

# ==========================================
# 2. CSV 파일 경로
# ==========================================
# py 파일: pages 폴더
# csv 파일: pages의 상위 폴더

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "temperature.csv"

# ==========================================
# 3. 한글 폰트 설정
# ==========================================
font_candidates = [
    "Malgun Gothic",
    "NanumGothic",
    "Noto Sans CJK KR",
    "Noto Sans KR"
]

available_fonts = {
    f.name for f in fm.fontManager.ttflist
}

for font in font_candidates:
    if font in available_fonts:
        plt.rcParams["font.family"] = font
        break

plt.rcParams["axes.unicode_minus"] = False

# ==========================================
# 4. CSV 데이터 불러오기
# ==========================================
@st.cache_data
def load_data(file_path):

    df = pd.read_csv(
        file_path,
        encoding="cp949"
    )

    df["일시"] = pd.to_datetime(
        df["일시"],
        format="%b-%y",
        errors="coerce"
    )

    df["연도"] = df["일시"].dt.year
    df["월"] = df["일시"].dt.month

    df["평균기온(℃)"] = pd.to_numeric(
        df["평균기온(℃)"],
        errors="coerce"
    )

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
    f"📊 분석 데이터: {min_year}년 ~ {max_year}년 "
    f"| 전체 데이터 {len(df)}개"
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

    selected_month = (
        month_names.index(selected_month_name) + 1
    )

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
# 7. 선택한 월의 기온 데이터 추출
# ==========================================
monthly_data = df[
    df["월"] == selected_month
].copy()

monthly_data = monthly_data.sort_values("연도")

if len(monthly_data) < 3:
    st.warning("회귀분석을 위한 데이터가 부족합니다.")
    st.stop()

X = monthly_data["연도"].values.reshape(-1, 1)
y = monthly_data["평균기온(℃)"].values

# ==========================================
# 8. 회귀 알고리즘 3개 생성 및 학습
# ==========================================

# ① 선형회귀
linear_model = LinearRegression()
linear_model.fit(X, y)

# ② 다항회귀 (2차)
# 연도를 기준 연도에서 빼서 수치 계산을 안정화
center_year = min_year
X_centered = X - center_year

polynomial_model = make_pipeline(
    PolynomialFeatures(degree=2),
    LinearRegression()
)

polynomial_model.fit(X_centered, y)

# ③ 랜덤 포레스트 회귀
random_forest_model = RandomForestRegressor(
    n_estimators=300,
    max_depth=5,
    min_samples_leaf=2,
    random_state=42
)

random_forest_model.fit(X, y)

# ==========================================
# 9. 예측 함수
# ==========================================
def predict_linear(year):
    return float(
        linear_model.predict(
            np.array([[year]])
        )[0]
    )


def predict_polynomial(year):
    return float(
        polynomial_model.predict(
            np.array([[year - center_year]])
        )[0]
    )


def predict_random_forest(year):
    return float(
        random_forest_model.predict(
            np.array([[year]])
        )[0]
    )


# 각 알고리즘의 예측값
predictions = {
    "선형회귀": predict_linear(forecast_year),
    "다항회귀": predict_polynomial(forecast_year),
    "랜덤 포레스트": predict_random_forest(forecast_year)
}

# ==========================================
# 10. 알고리즘 선택
# ==========================================
st.subheader("🤖 회귀 알고리즘 선택")

algorithm = st.radio(
    "사용할 예측 알고리즘을 선택하세요.",
    [
        "선형회귀",
        "다항회귀",
        "랜덤 포레스트"
    ],
    horizontal=True
)

st.caption(
    "알고리즘을 변경하면 그래프와 예측 결과가 자동으로 바뀝니다."
)

# ==========================================
# 11. 선택한 알고리즘 설정
# ==========================================
if algorithm == "선형회귀":

    selected_model = linear_model
    selected_predict = predict_linear
    model_color = "red"

elif algorithm == "다항회귀":

    selected_model = polynomial_model
    selected_predict = predict_polynomial
    model_color = "green"

else:

    selected_model = random_forest_model
    selected_predict = predict_random_forest
    model_color = "purple"


predicted_temp = predictions[algorithm]

# 학습 데이터 예측
if algorithm == "선형회귀":
    history_predictions = linear_model.predict(X)

elif algorithm == "다항회귀":
    history_predictions = polynomial_model.predict(X_centered)

else:
    history_predictions = random_forest_model.predict(X)

# 결정계수
r2 = r2_score(y, history_predictions)

# ==========================================
# 12. 예측 결과 표시
# ==========================================
st.divider()

st.subheader("📈 선택한 알고리즘 예측 결과")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "선택 알고리즘",
        algorithm
    )

with col2:
    st.metric(
        "예측 연도",
        f"{forecast_year}년"
    )

with col3:
    st.metric(
        "예상 평균기온",
        f"{predicted_temp:.2f} ℃"
    )

st.metric(
    "결정계수 R² (학습 데이터)",
    f"{r2:.3f}"
)

st.caption(
    "R²는 과거 학습 데이터에 대한 설명력이며, "
    "미래 예측의 정확도를 보장하지 않습니다."
)

# ==========================================
# 13. 선택 알고리즘 그래프
# ==========================================
st.divider()

st.subheader(
    f"📊 {selected_month_name} 평균기온 "
    f"{algorithm} 분석 그래프"
)

fig, ax = plt.subplots(figsize=(12, 6))

# 과거 실제 기온
ax.scatter(
    X.flatten(),
    y,
    color="royalblue",
    s=65,
    label="과거 실제 평균기온",
    zorder=3
)

# 회귀선 및 예측선
line_x = np.linspace(
    min_year,
    forecast_year,
    400
).reshape(-1, 1)

line_y = np.array([
    selected_predict(year)
    for year in line_x.flatten()
])

ax.plot(
    line_x.flatten(),
    line_y,
    color=model_color,
    linewidth=2.5,
    label=f"{algorithm} 예측선"
)

# 과거 실제값과 학습 예측값 사이의 오차
for i in range(len(X)):
    ax.plot(
        [X[i, 0], X[i, 0]],
        [y[i], history_predictions[i]],
        color="gray",
        linestyle=":",
        alpha=0.4
    )

# 미래 예측값
ax.scatter(
    forecast_year,
    predicted_temp,
    color="darkorange",
    marker="*",
    s=280,
    edgecolors="black",
    label="미래 예측 평균기온",
    zorder=5
)

ax.annotate(
    f"{predicted_temp:.2f}℃",
    xy=(forecast_year, predicted_temp),
    xytext=(8, 12),
    textcoords="offset points",
    fontsize=12,
    fontweight="bold",
    color="darkorange"
)

ax.set_title(
    f"{selected_month_name} 평균기온 {algorithm}",
    fontsize=16,
    fontweight="bold"
)

ax.set_xlabel("연도")
ax.set_ylabel("평균기온 (℃)")

ax.grid(
    True,
    linestyle="--",
    alpha=0.35
)

ax.legend()
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)

# ==========================================
# 14. 세 알고리즘 예측값 비교
# ==========================================
st.divider()

st.subheader("⚖️ 세 가지 알고리즘 예측 결과 비교")

st.write(
    f"같은 {selected_month_name}의 과거 기온 데이터를 "
    f"사용하여 {forecast_year}년의 기온을 예측한 결과입니다."
)

comparison = pd.DataFrame({
    "알고리즘": list(predictions.keys()),
    "예측 평균기온(℃)": [
        round(value, 2)
        for value in predictions.values()
    ]
})

st.dataframe(
    comparison,
    use_container_width=True,
    hide_index=True
)

# 비교 막대그래프
fig2, ax2 = plt.subplots(figsize=(10, 4))

colors = ["royalblue", "seagreen", "mediumpurple"]

bars = ax2.bar(
    list(predictions.keys()),
    list(predictions.values()),
    color=colors,
    width=0.5
)

for bar in bars:
    height = bar.get_height()

    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{height:.2f}℃",
        ha="center",
        va="bottom",
        fontsize=11
    )

ax2.set_title(
    f"{forecast_year}년 {selected_month_name} 알고리즘별 예측 기온"
)

ax2.set_ylabel("예측 평균기온 (℃)")
ax2.grid(axis="y", linestyle="--", alpha=0.3)

fig2.tight_layout()

st.pyplot(fig2)
plt.close(fig2)

# ==========================================
# 15. 알고리즘별 설명
# ==========================================
st.divider()

st.subheader("🧠 회귀 알고리즘 알아보기")

st.markdown("### ① 선형회귀 (Linear Regression)")

st.write("""
과거 데이터의 전체적인 증가 또는 감소 추세를
하나의 직선으로 나타내는 알고리즘입니다.

실제 데이터와 직선 사이의 오차 제곱 합이
최소가 되도록 직선을 계산합니다.
""")

st.latex(r"y = ax + b")

st.write("""
- x: 연도
- y: 예측 평균기온
- a: 기울기
- b: 절편

특징: 전체적인 장기 변화 추세를 파악하기 쉽습니다.
""")

st.markdown("### ② 다항회귀 (Polynomial Regression)")

st.write("""
선형회귀와 달리 곡선 형태로 데이터의 관계를
표현할 수 있는 알고리즘입니다.

이번 프로그램에서는 2차 다항식을 사용합니다.
""")

st.latex(r"y = ax^2 + bx + c")

st.write("""
- x: 연도
- y: 예측 평균기온
- a, b, c: 데이터로 계산한 계수

특징: 기온 변화가 일정한 직선 형태가 아닐 때
곡선으로 변화 경향을 표현할 수 있습니다.
""")

st.markdown("### ③ 랜덤 포레스트 회귀 (Random Forest Regression)")

st.write("""
랜덤 포레스트는 여러 개의 결정트리를 만들어
각각 예측하게 한 다음, 그 결과의 평균을 계산하는
앙상블 머신러닝 알고리즘입니다.

여러 결정트리의 결과를 결합하여
복잡하고 비선형적인 데이터 관계를 분석할 수 있습니다.
""")

st.write("""
특징:
- 여러 결정트리의 예측 결과를 결합합니다.
- 데이터의 복잡한 변화 패턴을 학습할 수 있습니다.
- 직선이나 하나의 곡선이 아닌 계단 형태의 예측선이 나타날 수 있습니다.
- 학습한 연도 범위 밖에서는 새로운 추세를 계속 연장하지 못하는 특성이 있습니다.
""")

# ==========================================
# 16. 알고리즘별 비교 설명
# ==========================================
st.divider()

st.subheader("🔍 알고리즘별 차이점")

st.markdown("""
| 알고리즘 | 예측 방식 | 그래프 특징 |
|---|---|---|
| 선형회귀 | 직선으로 추세 분석 | 직선 |
| 다항회귀 | 2차 곡선으로 분석 | 곡선 |
| 랜덤 포레스트 | 여러 결정트리의 평균 | 계단 형태 |
""")

st.write("""
같은 과거 기온 데이터를 사용하더라도
알고리즘마다 데이터를 학습하는 방법이 다르기 때문에
미래 예측값이 서로 다르게 나올 수 있습니다.

특히 먼 미래를 예측할 때는 알고리즘의 특성에 따라
예측 결과의 차이가 더욱 커질 수 있습니다.
""")

# ==========================================
# 17. 분석 시 주의사항
# ==========================================
st.warning("""
⚠️ 주의사항

1. 선형회귀와 다항회귀는 과거의 수학적 관계를 미래로 연장합니다.
2. 랜덤 포레스트는 과거 학습 범위를 벗어난 연도에서 예측값이 크게 달라지지 않는 특성이 있습니다.
3. R²는 학습 데이터에 대한 설명력이지 미래 예측 정확도가 아닙니다.
4. 실제 기온은 기후변화와 자연현상 등 다양한 요인의 영향을 받습니다.

이 프로그램의 결과는 실제 기상예보가 아닌
과거 데이터에 기반한 통계적 예측값입니다.
""")

# ==========================================
# 18. 데이터 출처
# ==========================================
st.divider()

st.caption(
    "📌 데이터 출처: 제공된 월별 평균기온 CSV 파일"
)

st.caption(
    "사용 알고리즘: 선형회귀, 다항회귀, 랜덤 포레스트 회귀"
)
