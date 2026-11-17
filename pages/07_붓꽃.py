
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score
)


# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 붓꽃 품종 예측 프로그램")

st.write(
    "꽃의 길이와 너비를 입력하면 "
    "머신러닝 알고리즘이 붓꽃의 품종을 예측합니다."
)

st.markdown("""
이 프로그램은 3가지 분류 알고리즘을 사용하여
붓꽃의 품종을 예측하고 결과를 비교합니다.
""")

st.divider()


# ==========================================
# 2. CSV 데이터 불러오기
# ==========================================

@st.cache_data
def load_data():

    # pages 폴더의 상위 폴더에서 CSV 찾기
    file_path = (
        Path(__file__).resolve().parent.parent / "Iris.csv"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            "Iris.csv 파일을 찾을 수 없습니다. "
            "프로젝트 최상위 폴더에 CSV 파일을 넣어주세요."
        )

    # 업로드한 CSV는 CP949 인코딩 사용
    try:
        data = pd.read_csv(
            file_path,
            encoding="cp949"
        )
    except UnicodeDecodeError:
        data = pd.read_csv(
            file_path,
            encoding="utf-8-sig"
        )

    return data


try:
    df = load_data()

except Exception as e:
    st.error(f"데이터 불러오기 오류: {e}")
    st.stop()


# 필요한 열 확인
required_columns = [
    "꽃받침길이",
    "꽃받침너비",
    "꽃잎길이",
    "꽃잎너비",
    "품종"
]

if not all(col in df.columns for col in required_columns):
    st.error(
        "CSV 파일에 필요한 열이 없습니다. "
        "열 이름을 확인해주세요."
    )
    st.stop()


# 결측치 제거
df = df[required_columns].copy()

for col in required_columns[:4]:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = df.dropna().copy()

if df.empty or df["품종"].nunique() < 2:
    st.error("분석할 데이터가 부족합니다.")
    st.stop()


# ==========================================
# 3. 데이터 기본 정보
# ==========================================

st.subheader("📊 데이터 기본 정보")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "전체 데이터",
        f"{len(df)}개"
    )

with col2:
    st.metric(
        "붓꽃 품종",
        f"{df['품종'].nunique()}종"
    )

with col3:
    st.metric(
        "측정 속성",
        "4개"
    )

with col4:
    st.metric(
        "결측치",
        f"{df[required_columns].isnull().sum().sum()}개"
    )


# 품종별 데이터 개수
with st.expander("📚 품종별 데이터 개수 확인"):

    count_df = (
        df["품종"]
        .value_counts()
        .rename_axis("품종")
        .reset_index(name="데이터 개수")
    )

    st.dataframe(
        count_df,
        use_container_width=True,
        hide_index=True
    )

    st.write("전체 데이터 미리보기")

    st.dataframe(
        df,
        use_container_width=True
    )


st.divider()


# ==========================================
# 4. 분류 알고리즘 3가지
# ==========================================

def create_models():

    models = {

        # SVM
        "SVM": Pipeline([
            ("scaler", StandardScaler()),
            ("model", SVC(
                kernel="rbf",
                C=1.0,
                gamma="scale"
            ))
        ]),

        # KNN
        "KNN": Pipeline([
            ("scaler", StandardScaler()),
            ("model", KNeighborsClassifier(
                n_neighbors=5
            ))
        ]),

        # Random Forest
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            random_state=42
        )
    }

    return models


# ==========================================
# 5. 알고리즘 작동 원리
# ==========================================

algorithm_info = {

    "SVM": {
        "title": "① SVM (서포트 벡터 머신)",

        "description": """
SVM은 데이터를 가장 잘 구분하는 경계선을 찾는
분류 알고리즘입니다.

품종별 데이터 사이의 간격을 최대한 넓히는
경계를 찾아 새로운 꽃의 품종을 예측합니다.

이번 프로그램에서는 RBF 커널을 사용하여
직선으로 구분하기 어려운 데이터도 학습합니다.
"""
    },

    "KNN": {
        "title": "② KNN (K-최근접 이웃)",

        "description": """
KNN은 새롭게 입력된 데이터와 가장 가까운
기존 데이터를 찾아 품종을 예측하는 알고리즘입니다.

이번 프로그램에서는 입력값과 가까운
5개의 데이터를 확인합니다.

그중 가장 많이 나타나는 품종을
최종 예측 결과로 선택합니다.
"""
    },

    "Random Forest": {
        "title": "③ 랜덤 포레스트",

        "description": """
랜덤 포레스트는 여러 개의 결정 트리를 만들어
각각의 예측 결과를 종합하는 알고리즘입니다.

여러 결정 트리의 판단을 모아
가장 많은 표를 얻은 품종을
최종 예측 결과로 결정합니다.
"""
    }
}


# ==========================================
# 6. 모델 학습 및 정확도 계산
# ==========================================

def analyze_models(features):

    X = df[features]
    y = df["품종"]

    models = create_models()

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    results = {}

    for name, model in models.items():

        # 5겹 교차 검증
        scores = cross_val_score(
            model,
            X,
            y,
            cv=cv,
            scoring="accuracy"
        )

        # 전체 데이터로 최종 학습
        model.fit(X, y)

        results[name] = {
            "model": model,
            "accuracy": scores.mean(),
            "scores": scores
        }

    return results


# ==========================================
# 7. 한글 품종 이름
# ==========================================

korean_names = {

    "Iris-setosa": "세토사",

    "Iris-versicolor": "버시컬러",

    "Iris-virginica": "버지니카"
}


# ==========================================
# 8. 예측 화면 함수
# ==========================================

def show_prediction(features):

    feature1 = features[0]
    feature2 = features[1]

    # 실제 데이터의 최솟값과 최댓값
    min1 = float(df[feature1].min())
    max1 = float(df[feature1].max())

    min2 = float(df[feature2].min())
    max2 = float(df[feature2].max())

    # --------------------------------------
    # 사용자 입력
    # --------------------------------------

    st.subheader("✏️ 꽃의 측정값 입력")

    st.info(
        f"""
        📏 **{feature1}**

        입력 가능 범위: {min1:.1f} ~ {max1:.1f} cm

        📐 **{feature2}**

        입력 가능 범위: {min2:.1f} ~ {max2:.1f} cm
        """
    )

    col1, col2 = st.columns(2)

    with col1:

        value1 = st.slider(
            feature1 + " (cm)",
            min_value=min1,
            max_value=max1,
            value=float((min1 + max1) / 2),
            step=0.1,
            key="slider_" + feature1
        )

    with col2:

        value2 = st.slider(
            feature2 + " (cm)",
            min_value=min2,
            max_value=max2,
            value=float((min2 + max2) / 2),
            step=0.1,
            key="slider_" + feature2
        )

    # 입력값 데이터프레임
    input_data = pd.DataFrame({

        feature1: [value1],

        feature2: [value2]

    })

    # 모델 분석
    results = analyze_models(features)


    # ======================================
    # 9. 알고리즘별 품종 예측 결과 비교
    # ======================================

    st.divider()

    st.subheader("🔮 알고리즘별 품종 예측 결과")

    result_cols = st.columns(3)

    comparison = []

    for i, (name, result) in enumerate(results.items()):

        prediction = result["model"].predict(
            input_data
        )[0]

        korean_name = korean_names.get(
            prediction,
            prediction
        )

        accuracy = result["accuracy"] * 100

        comparison.append({

            "알고리즘": name,

            "예측 품종": korean_name,

            "교차 검증 정확도": f"{accuracy:.2f}%"

        })

        with result_cols[i]:

            st.metric(
                label=name,
                value=korean_name
            )

            st.metric(
                label="평균 정확도",
                value=f"{accuracy:.2f}%"
            )


    # ======================================
    # 10. 예측 결과 비교 표
    # ======================================

    st.subheader("📋 세 가지 알고리즘 비교표")

    comparison_df = pd.DataFrame(comparison)

    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True
    )

    predictions = [
        item["예측 품종"]
        for item in comparison
    ]

    if len(set(predictions)) == 1:

        st.success(
            f"세 알고리즘 모두 {predictions[0]} 품종으로 예측했습니다."
        )

    else:

        st.warning(
            "알고리즘마다 예측 결과가 다릅니다. "
            "각 알고리즘의 결과와 정확도를 비교해보세요."
        )

    st.caption(
        "정확도는 5겹 교차 검증의 평균입니다. "
        "정확도가 높다고 해서 개별 예측이 반드시 맞는 것은 아닙니다."
    )


    # ======================================
    # 11. 실제 데이터 분포 그래프
    # ======================================

    st.divider()

    st.subheader("📊 붓꽃 품종별 측정값 그래프")

    st.write(
        "각 점은 실제 붓꽃 데이터입니다. "
        "초록색 별은 사용자가 입력한 값입니다."
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {

        "Iris-setosa": "blue",

        "Iris-versicolor": "orange",

        "Iris-virginica": "red"

    }

    # 품종별 산점도
    for species, color in colors.items():

        subset = df[df["품종"] == species]

        if subset.empty:
            continue

        ax.scatter(

            subset[feature1],

            subset[feature2],

            color=color,

            label=korean_names.get(
                species,
                species
            ),

            alpha=0.65,

            s=55

        )


    # 사용자 입력값 초록색 별
    ax.scatter(

        value1,

        value2,

        color="green",

        marker="*",

        s=350,

        edgecolors="black",

        linewidths=1.2,

        label="사용자 입력값",

        zorder=10

    )

    ax.set_xlabel(
        feature1 + " (cm)",
        fontsize=12
    )

    ax.set_ylabel(
        feature2 + " (cm)",
        fontsize=12
    )

    ax.set_title(
        "Iris Flower Classification",
        fontsize=15
    )

    ax.grid(alpha=0.25)

    ax.legend()

    fig.tight_layout()

    st.pyplot(fig)

    plt.close(fig)


    # ======================================
    # 12. 그래프 아래 알고리즘 원리 설명
    # ======================================

    st.divider()

    st.subheader("🧠 분류 알고리즘 작동 원리")

    st.write(
        "이번 예측에 사용된 세 가지 알고리즘의 "
        "작동 방식을 확인할 수 있습니다."
    )

    for name in [
        "SVM",
        "KNN",
        "Random Forest"
    ]:

        with st.expander(
            algorithm_info[name]["title"]
        ):

            st.write(
                algorithm_info[name]["description"]
            )

            st.write(
                "**현재 측정 방식의 교차 검증 정확도:** "
                f"{results[name]['accuracy'] * 100:.2f}%"
            )


# ==========================================
# 13. 예측 탭 만들기
# ==========================================

st.divider()

st.subheader("🔬 측정 방식 선택")

tab1, tab2 = st.tabs([

    "🌷 꽃잎 정보로 예측하기",

    "🌿 꽃받침 정보로 예측하기"

])


# ==========================================
# 탭 1. 꽃잎 길이 + 꽃잎 너비
# ==========================================

with tab1:

    st.subheader("🌷 꽃잎 정보 분석")

    st.write(
        "꽃잎의 길이와 너비를 이용하여 "
        "붓꽃의 품종을 예측합니다."
    )

    show_prediction([

        "꽃잎길이",

        "꽃잎너비"

    ])


# ==========================================
# 탭 2. 꽃받침 길이 + 꽃받침 너비
# ==========================================

with tab2:

    st.subheader("🌿 꽃받침 정보 분석")

    st.write(
        "꽃받침의 길이와 너비를 이용하여 "
        "붓꽃의 품종을 예측합니다."
    )

    show_prediction([

        "꽃받침길이",

        "꽃받침너비"

    ])


# ==========================================
# 14. 마무리
# ==========================================

st.divider()

st.subheader("📚 분석 안내")

st.write("""
이 프로그램은 Iris 데이터 150개를 활용하여
붓꽃의 품종을 예측합니다.

꽃잎의 길이와 너비를 사용하는 방법,
꽃받침의 길이와 너비를 사용하는 방법을 비교할 수 있습니다.

또한 SVM, KNN, 랜덤 포레스트의
예측 결과와 교차 검증 정확도를 비교하여
어떤 알고리즘이 각 측정 방식에서 좋은 결과를 보이는지
확인할 수 있습니다.
""")

st.caption(
    "🌸 Iris 데이터 기반 머신러닝 품종 예측 프로그램"
)
