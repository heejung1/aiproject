
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
    "과거 기온 데이터를 이용하여 3가지 회귀 알고리즘으로 "
    "미래의 평균기온을 예측해 보세요!"
)

st.divider()

# ==========================================
# 2. CSV 경로 설정
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
    f"📊 분석 기간: {min_year}년 ~ {max_year}년 "
    f"| 전체 데이터 {len(df)}개"
)

# ==========================================
# 6. 사용자 입력
# ==========================================
st.subheader("🔎 예측 조건 선택")

col1, col2 = st.columns(2)

month_names = [
    "1월", "2월", "3월", "4월",
    "5월", "6월", "7월", "8월",
    "9월", "10월", "11월", "12월"
]

with col1:

    selected_month_name = st.selectbox(
        "예측할 월을 선택하세요.",
        month_names,
        key="temperature_prediction_month_06"
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
        step=1,
        key="temperature_prediction_year_06"
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

if len(monthly_data) < 3:
    st.warning("회귀분석을 위한 데이터가 부족합니다.")
    st.stop()

X = monthly_data["연도"].values.reshape(-1, 1)
y = monthly_data["평균기온(℃)"].values

# ==========================================
# 8. 회귀 알고리즘 학습
# ==========================================

# ① 선형회귀
linear_model = LinearRegression()
linear_model.fit(X, y)

# ② 다항회귀 (2차)
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
    random_state=42,
    n_jobs=-1
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


# ==========================================
# 10. 세 알고리즘 예측값 계산
# ==========================================
predictions = {
    "선형회귀": predict_linear(forecast_year),
    "다항회귀": predict_polynomial(forecast_year),
    "랜덤 포레스트": predict_random_forest(forecast_year)
}

# ==========================================
# 11. 알고리즘 선택
# ==========================================
st.subheader("🤖 회귀 알고리즘 선택")

algorithm = st.radio(
    "사용할 예측 알고리즘을 선택하세요.",
    [
        "선형회귀",
        "다항회귀",
        "랜덤 포레스트"
    ],
    horizontal=True,
    key="temperature_prediction_algorithm_06"
)

if algorithm == "선형회귀":

    selected_predict = predict_linear
    model_color = "red"
    history_predictions = linear_model.predict(X)

elif algorithm == "다항회귀":

    selected_predict = predict_polynomial
    model_color = "green"
    history_predictions = polynomial_model.predict(X_centered)

else:

    selected_predict = predict_random_forest
    model_color = "purple"
    history_predictions = random_forest_model.predict(X)

predicted_temp = predictions[algorithm]

# ==========================================
# 12. 결정계수 계산
# ==========================================
r2 = r2_score(y, history_predictions)

# ==========================================
# 13. 예측 결과 표시
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
    "R²는 과거 학습 데이터에 대한 설명력이며 "
    "미래 예측 정확도를 보장하지 않습니다."
)

st.divider()

# ==========================================
# 14. 선택 알고리즘 그래프
# ==========================================
st.subheader(
    f"📊 {selected_month_name} 평균기온 "
    f"{algorithm} 분석 그래프"
)

fig, ax = plt.subplots(figsize=(12, 6))

# 실제 관측값
ax.scatter(
    X.flatten(),
    y,
    color="royalblue",
    s=65,
    label="과거 실제 평균기온",
    zorder=3
)

# 회귀 예측선
line_x = np.linspace(
    min_year,
    forecast_year,
    400
)

line_y = np.array([
    selected_predict(year)
    for year in line_x
])

ax.plot(
    line_x,
    line_y,
    color=model_color,
    linewidth=2.5,
    label=f"{algorithm} 예측선"
)

# 과거 실제값과 회귀 예측값의 오차
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
# 15. 알고리즘별 예측값 비교
# ==========================================
st.divider()

st.subheader("⚖️ 세 가지 알고리즘 예측 결과 비교")

st.write(
    f"같은 {selected_month_name}의 과거 데이터를 사용하여 "
    f"{forecast_year}년의 평균기온을 예측한 결과입니다."
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

# 비교 그래프
fig2, ax2 = plt.subplots(figsize=(10, 5))

bars = ax2.bar(
    list(predictions.keys()),
    list(predictions.values()),
    color=["royalblue", "seagreen", "mediumpurple"],
    width=0.5
)

for bar in bars:

    height = bar.get_height()

    ax2.annotate(
        f"{height:.2f}℃",
        xy=(
            bar.get_x() + bar.get_width() / 2,
            height
        ),
        xytext=(0, 5),
        textcoords="offset points",
        ha="center",
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
# 16. 알고리즘별 설명
# ==========================================
st.divider()

st.subheader("🧠 회귀 알고리즘 알아보기")

st.markdown("### ① 선형회귀 (Linear Regression)")

st.write("""
과거 데이터의 전체적인 증가 또는 감소 추세를
하나의 직선으로 나타내는 알고리즘입니다.

실제 데이터와 직선 사이의 오차 제곱 합이
최소가 되도록 기울기와 절편을 계산합니다.
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
다항회귀는 직선이 아닌 곡선 형태로
데이터의 관계를 표현할 수 있는 알고리즘입니다.

이 프로그램에서는 2차 다항식을 사용합니다.
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
- 복잡한 데이터 변화 패턴을 학습할 수 있습니다.
- 계단 형태의 예측선이 나타날 수 있습니다.
- 학습한 연도 범위 밖에서는 새로운 추세를
  계속 연장하지 못하는 특성이 있습니다.
""")

# ==========================================
# 17. 알고리즘별 차이
# ==========================================
st.divider()

st.subheader("🔍 알고리즘별 차이점")

st.markdown("""
| 알고리즘 | 예측 방식 | 그래프 특징 |
|---|---|---|
| 선형회귀 | 직선으로 분석 | 직선 |
| 다항회귀 | 2차 곡선으로 분석 | 곡선 |
| 랜덤 포레스트 | 여러 결정트리의 평균 | 계단 형태 |
""")

st.write("""
같은 과거 기온 데이터를 사용하더라도
알고리즘마다 데이터를 학습하는 방법이 다르기 때문에
미래 예측값이 서로 다르게 나올 수 있습니다.
""")

# ==========================================
# 18. 분석 시 주의사항
# ==========================================
st.warning("""
⚠️ 분석 시 주의사항

1. 선형회귀와 다항회귀는 과거의 수학적 관계를 미래로 연장합니다.
2. 랜덤 포레스트는 학습 데이터 범위 밖의 연도에서
   예측값이 크게 달라지지 않는 특성이 있습니다.
3. R²는 학습 데이터에 대한 설명력이지 미래 예측 정확도가 아닙니다.
4. 실제 기온은 기후변화와 자연현상 등 다양한 요인의 영향을 받습니다.

이 결과는 실제 기상예보가 아닌
과거 데이터에 기반한 통계적 예측값입니다.
""")

# ==========================================
# 19. 데이터 출처
# ==========================================
st.divider()

st.caption(
    "📌 데이터 출처: 제공된 월별 평균기온 CSV 파일"
)

st.caption(
    "사용 알고리즘: 선형회귀, 다항회귀, 랜덤 포레스트 회귀"
)

