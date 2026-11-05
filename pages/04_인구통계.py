import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# --------------------------------
# 1. 페이지 설정
# --------------------------------
st.set_page_config(
    page_title="서울 인구 연령별 분석",
    page_icon="📊",
    layout="wide"
)

st.title("📊 서울특별시 연령별 인구 분석")
st.caption("행정구역, 성별, 연도를 선택하여 연령대별 인구를 비교해 보세요.")

# --------------------------------
# 2. CSV 파일 불러오기
# --------------------------------
BASE_DIR = Path(__file__).resolve().parent
FILE_PATH = BASE_DIR / "population.csv"


@st.cache_data
def load_data():

    # 한글 인코딩 자동 대응
    encodings = ["cp949", "utf-8-sig", "utf-8", "euc-kr"]

    df = None

    for encoding in encodings:
        try:
            df = pd.read_csv(
                FILE_PATH,
                encoding=encoding,
                dtype=str
            )
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError("CSV 파일의 한글 인코딩을 확인해 주세요.")

    # 열 이름 공백 제거
    df.columns = df.columns.str.strip()

    # 행정구역 이름 정리
    df["행정구역"] = (
        df["행정구역"]
        .astype(str)
        .str.replace(r"\s*\(\d+\)\s*$", "", regex=True)
        .str.strip()
    )

    return df


try:
    df = load_data()

except FileNotFoundError:
    st.error("population.csv 파일을 찾을 수 없습니다.")
    st.info("app.py와 population.csv를 같은 폴더에 넣어 주세요.")
    st.stop()

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


# --------------------------------
# 3. 선택 항목 설정
# --------------------------------

# 행정구역
regions = df["행정구역"].dropna().unique().tolist()

# 연도
years = ["2020", "2021", "2022", "2023", "2024", "2025"]

# 성별
genders = {
    "전체": "거주자",
    "남성": "남_거주자",
    "여성": "여_거주자"
}

# 나이 구간
ages = [
    "0~9세",
    "10~19세",
    "20~29세",
    "30~39세",
    "40~49세",
    "50~59세",
    "60~69세",
    "70~79세",
    "80~89세",
    "90~99세",
    "100세 이상"
]


# --------------------------------
# 4. 사용자 선택 메뉴
# --------------------------------
st.subheader("🔍 분석 조건 선택")

col1, col2, col3 = st.columns(3)

with col1:
    selected_region = st.selectbox(
        "행정구역 선택",
        regions
    )

with col2:
    selected_gender = st.selectbox(
        "성별 선택",
        list(genders.keys())
    )

with col3:
    selected_year = st.selectbox(
        "연도 선택",
        years,
        index=5
    )


# --------------------------------
# 5. 선택한 데이터 추출
# --------------------------------
selected_row = df[
    df["행정구역"] == selected_region
].iloc[0]

gender_column = genders[selected_gender]

values = []

for age in ages:

    column_name = (
        f"{selected_year}년_"
        f"{gender_column}_"
        f"{age}"
    )

    if column_name in df.columns:

        value = pd.to_numeric(
            str(selected_row[column_name]).replace(",", ""),
            errors="coerce"
        )

        values.append(
            0 if pd.isna(value) else int(value)
        )

    else:
        values.append(0)


# --------------------------------
# 6. 그래프 데이터 생성
# --------------------------------
chart_df = pd.DataFrame({
    "나이": ages,
    "인구수": values
})


# --------------------------------
# 7. 인구 통계 표시
# --------------------------------
total_population = sum(values)

st.divider()

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.metric("📍 선택 지역", selected_region)

with metric2:
    st.metric("👥 선택 성별", selected_gender)

with metric3:
    st.metric("📊 연령별 인구 합계", f"{total_population:,}명")


# --------------------------------
# 8. 꺾은선 그래프
# --------------------------------
st.subheader(
    f"📈 {selected_region} "
    f"{selected_year}년 {selected_gender} 연령별 인구"
)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=chart_df["나이"],
        y=chart_df["인구수"],
        mode="lines+markers",
        name="인구수",
        line=dict(
            color="red",
            width=3
        ),
        marker=dict(
            color="red",
            size=8
        ),
        hovertemplate=(
            "나이: %{x}<br>"
            "인구수: %{y:,.0f}명"
            "<extra></extra>"
        )
    )
)

fig.update_layout(
    height=600,
    plot_bgcolor="white",
    paper_bgcolor="white",

    font=dict(
        family="Malgun Gothic, AppleGothic, NanumGothic, sans-serif",
        size=13,
        color="black"
    ),

    xaxis=dict(
        title="나이",
        type="category",
        categoryorder="array",
        categoryarray=ages,
        showgrid=True,
        gridcolor="#dddddd",
        gridwidth=1,
        showline=True,
        linecolor="black"
    ),

    yaxis=dict(
        title="인구수 (명)",
        rangemode="tozero",
        showgrid=True,
        gridcolor="#cccccc",
        gridwidth=1,

        # 100명 단위 보조 눈금 및 구분선
        minor=dict(
            dtick=100,
            showgrid=True,
            gridcolor="#eeeeee",
            gridwidth=1
        ),

        showline=True,
        linecolor="black",
        separatethousands=True
    ),

    margin=dict(
        l=70,
        r=30,
        t=40,
        b=70
    ),

    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------
# 9. 데이터 표 출력
# --------------------------------
with st.expander("📋 연령별 상세 인구 데이터 보기"):

    display_df = chart_df.copy()

    display_df["인구수"] = display_df["인구수"].apply(
        lambda x: f"{x:,}명"
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

st.divider()

st.caption(
    "서울특별시 인구 통계 데이터 | 2020~2025년"
)

