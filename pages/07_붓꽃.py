import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score

# ----------------------------------
# 1. 페이지 설정
# ----------------------------------
st.set_page_config(
    page_title="붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 붓꽃 품종 예측 프로그램")
st.write(
    "꽃잎의 길이와 너비를 입력하면 "
    "머신러닝이 붓꽃의 품종을 예측합니다."
)

st.divider()

# ----------------------------------
# 2. CSV 파일 불러오기
# ----------------------------------
@st.cache_data
def load_data():
    file_path = Path(__file__).resolve().parent.parent / "Iris.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Iris.csv 파일을 찾을 수 없습니다: {file_path}"
        )

    try:
        data = pd.read_csv(file_path, encoding="cp949")
    except UnicodeDecodeError:
        data = pd.read_csv(file_path, encoding="utf-8-sig")

    return data


try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 파일을 불러오지 못했습니다: {e}")
    st.stop()

# 필요한 열 확인
required_columns = ["꽃잎길이", "꽃잎너비", "품종"]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일에 필요한 열이 없습니다.")
    st.stop()

# 결측치 제거
df = df[required_columns].dropna().copy()

# ----------------------------------
# 3. 데이터 범위 설정
# ----------------------------------
min_length = float(df["꽃잎길이"].min())
max_length = float(df["꽃잎길이"].max())

min_width = float(df["꽃잎너비"].min())
max_width = float(df["꽃잎너비"].max())

# ----------------------------------
# 4. 머신러닝 모델 생성
# ----------------------------------
X = df[["꽃잎길이", "꽃잎너비"]]
y = df["품종"]

@st.cache_resource
def train_model(X, y):
    # SVM + 데이터 표준화
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("svm", SVC(kernel="rbf", C=1.0, gamma="scale"))
    ])

    # 5겹 교차 검증으로 정확도 확인
    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    scores = cross_val_score(
        model,
        X,
        y,
        cv=cv,
        scoring="accuracy"
    )

    # 전체 데이터로 최종 학습
    model.fit(X, y)

    return model, scores


model, scores = train_model(X, y)

# ----------------------------------
# 5. 모델 정보
# ----------------------------------
st.subheader("🤖 AI 예측 모델 정보")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("분류 알고리즘", "SVM (RBF)")

with col2:
    st.metric(
        "교차 검증 평균 정확도",
        f"{scores.mean() * 100:.2f}%"
    )

with col3:
    st.metric("분석 데이터", f"{len(df)}개")

st.caption(
    "정확도는 전체 데이터를 5개 그룹으로 나누어 "
    "교차 검증한 결과입니다."
)

st.divider()

# ----------------------------------
# 6. 사용자 입력
# ----------------------------------
st.subheader("✏️ 꽃잎 정보 입력")

st.info(
    f"""
    📏 꽃잎 길이 입력 범위: {min_length:.1f} ~ {max_length:.1f} cm

    📐 꽃잎 너비 입력 범위: {min_width:.1f} ~ {max_width:.1f} cm
    """
)

col1, col2 = st.columns(2)

with col1:
    petal_length = st.slider(
        "🌷 꽃잎 길이 (cm)",
        min_value=min_length,
        max_value=max_length,
        value=3.0,
        step=0.1
    )

with col2:
    petal_width = st.slider(
        "🌷 꽃잎 너비 (cm)",
        min_value=min_width,
        max_value=max_width,
        value=1.0,
        step=0.1
    )

# ----------------------------------
# 7. 품종 예측
# ----------------------------------
input_data = pd.DataFrame({
    "꽃잎길이": [petal_length],
    "꽃잎너비": [petal_width]
})

prediction = model.predict(input_data)[0]

# 품종 한글 이름
flower_names = {
    "Iris-setosa": "세토사",
    "Iris-versicolor": "버시컬러",
    "Iris-virginica": "버지니카"
}

st.divider()

st.subheader("🔮 예측 결과")

result_col1, result_col2 = st.columns(2)

with result_col1:
    st.success(
        f"""
        ### 🌸 예측된 품종

        # {flower_names.get(prediction, prediction)}

        **{prediction}**
        """
    )

with result_col2:
    st.write("**입력한 꽃잎 정보**")
    st.metric("꽃잎 길이", f"{petal_length:.1f} cm")
    st.metric("꽃잎 너비", f"{petal_width:.1f} cm")

# ----------------------------------
# 8. 그래프 시각화
# ----------------------------------
st.divider()
st.subheader("📊 붓꽃 품종별 꽃잎 분포")

st.write(
    "가로축은 꽃잎 길이, 세로축은 꽃잎 너비입니다. "
    "초록색 별은 사용자가 입력한 꽃잎의 위치입니다."
)

fig, ax = plt.subplots(figsize=(10, 6))

# 품종별 실제 데이터 표시
colors = {
    "Iris-setosa": "blue",
    "Iris-versicolor": "orange",
    "Iris-virginica": "red"
}

for species, color in colors.items():
    subset = df[df["품종"] == species]

    ax.scatter(
        subset["꽃잎길이"],
        subset["꽃잎너비"],
        color=color,
        label=flower_names.get(species, species),
        alpha=0.65,
        s=55
    )

# 사용자 입력값: 초록색 별
ax.scatter(
    petal_length,
    petal_width,
    color="green",
    marker="*",
    s=350,
    edgecolors="black",
    linewidths=1.2,
    label="사용자 입력값",
    zorder=10
)

ax.set_xlabel("Petal Length (cm)", fontsize=12)
ax.set_ylabel("Petal Width (cm)", fontsize=12)

ax.set_title(
    "Iris Flower Classification",
    fontsize=15
)

ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)

# ----------------------------------
# 9. 데이터 정보
# ----------------------------------
with st.expander("📚 데이터 정보 확인하기"):
    st.write("전체 데이터 미리보기")
    st.dataframe(df, use_container_width=True)

    st.write("품종별 데이터 개수")
    st.dataframe(
        df["품종"].value_counts().rename("개수"),
        use_container_width=True
    )

st.divider()

st.caption(
    "🌸 Iris 데이터 기반 머신러닝 품종 예측 프로그램"
)
