
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="서울 인구 통계 분석",
    page_icon="📊",
    layout="wide"
)

st.title("📊 서울특별시 인구 통계 분석")
st.caption("행정구역, 성별, 연도, 연령대별 인구를 분석합니다.")

# ==========================================
# 2. CSV 파일 경로
# ==========================================
# py 파일은 pages 폴더
# csv 파일은 상위 폴더

BASE_DIR = Path(__file__).resolve().parent
FILE_PATH = BASE_DIR.parent / "population.csv"


# ==========================================
# 3. CSV 파일 불러오기
# ==========================================
@st.cache_data
def load_data(file_path):

    encodings = [
        "cp949",
        "utf-8-sig",
        "utf-8",
        "euc-kr"
    ]

    data = None

    for encoding in encodings:
        try:
            data = pd.read_csv(
                file_path,
                encoding=encoding,
                dtype=str
            )
            break
        except UnicodeDecodeError:
            continue

    if data is None:
        raise ValueError("CSV 한글 인코딩을 확인해 주세요.")

    # 열 이름 정리
    data.columns = data.columns.str.strip()

    # 행정구역 이름 정리
    data["행정구역"] = (
        data["행정구역"]
        .astype(str)
        .str.replace(
            r"\s*\(\d+\)\s*$",
            "",
            regex=True
        )
        .str.strip()
    )

    return data


# 파일 확인
if not FILE_PATH.exists():
    st.error("population.csv 파일을 찾을 수 없습니다.")
    st.write("현재 PY 파일:", str(BASE_DIR))
    st.write("CSV 파일 경로:", str(FILE_PATH))
    st.stop()

try:
    df = load_data(str(FILE_PATH))

except Exception as e:
    st.error(f"데이터 불러오기 오류: {e}")
    st.stop()


# ==========================================
# 4. 기본 데이터 설정
# ==========================================

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

years = [
    "2020",
    "2021",
    "2022",
    "2023",
    "2024",
    "2025"
]

genders = {
    "전체": "거주자",
    "남성": "남_거주자",
    "여성": "여_거주자"
}


# ==========================================
# 5. 행정구역 목록
# ==========================================

regions = df["행정구역"].dropna().unique().tolist()

regions = sorted(
    regions,
    key=lambda x: (
        0 if x == "서울특별시" else 1,
        x
    )
)

# 서울 전체를 제외한 25개 자치구
district_df = df[
    df["행정구역"] != "서울특별시"
].copy()


# ==========================================
# 6. 인구 데이터 숫자 변환 함수
# ==========================================

def get_population(row, column_name):

    if column_name not in row.index:
        return 0

    value = pd.to_numeric(
        str(row[column_name]).replace(",", "").strip(),
        errors="coerce"
    )

    if pd.isna(value):
        return 0

    return int(value)


# ==========================================
# 7. 분석 조건 선택
# ==========================================

st.divider()
st.subheader("🔍 분석 조건 선택")

col1, col2, col3 = st.columns(3)

with col1:
    selected_region = st.selectbox(
        "📍 행정구역 선택",
        regions,
        key="population_04_region"
    )

with col2:
    selected_gender = st.selectbox(
        "👥 성별 선택",
        list(genders.keys()),
        key="population_04_gender"
    )

with col3:
    selected_year = st.selectbox(
        "📅 연도 선택",
        years,
        index=5,
        key="population_04_year"
    )

gender_column = genders[selected_gender]


# ==========================================
# 8. 선택한 행정구역 데이터 추출
# ==========================================

selected_row = df[
    df["행정구역"] == selected_region
].iloc[0]

values = []

for age in ages:

    column_name = (
        f"{selected_year}년_"
        f"{gender_column}_"
        f"{age}"
    )

    value = get_population(
        selected_row,
        column_name
    )

    values.append(value)


chart_df = pd.DataFrame({
    "나이": ages,
    "인구수": values
})


# ==========================================
# 9. 주요 통계 표시
# ==========================================

st.divider()

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.metric(
        "📍 선택 행정구역",
        selected_region
    )

with metric2:
    st.metric(
        "👥 선택 성별",
        selected_gender
    )

with metric3:
    st.metric(
        "📊 연령별 인구 합계",
        f"{sum(values):,}명"
    )


# ==========================================
# 10. 연령별 꺾은선 그래프
# ==========================================

st.divider()
st.subheader("📈 연령별 인구 꺾은선 그래프")

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
            size=9
        ),

        hovertemplate=(
            "나이: %{x}<br>"
            "인구수: %{y:,.0f}명"
            "<extra></extra>"
        )
    )
)

fig.update_layout(
    height=550,

    plot_bgcolor="white",
    paper_bgcolor="white",

    font=dict(
        family="Malgun Gothic, AppleGothic, NanumGothic, sans-serif",
        size=13,
        color="black"
    ),

    hovermode="x unified",

    xaxis=dict(
        title="나이",

        type="category",

        categoryorder="array",
        categoryarray=ages,

        showgrid=True,
        gridcolor="#dddddd",
        gridwidth=1
    ),

    yaxis=dict(
        title="인구수 (명)",

        rangemode="tozero",

        showgrid=True,
        gridcolor="#cccccc",

        # 세로축 100명 단위
        dtick=100,

        separatethousands=True
    ),

    margin=dict(
        l=80,
        r=30,
        t=40,
        b=80
    )
)

st.plotly_chart(
    fig,
    use_container_width=True,
    key="population_04_line_chart"
)


# ==========================================
# 11. 연령대별 자치구 순위 분석
# ==========================================

st.divider()

st.subheader("🏆 연령대별 인구가 많은 자치구")

st.write(
    "연령대를 선택하면 해당 연령 인구가 "
    "가장 많은 자치구부터 순서대로 표시됩니다."
)

selected_age = st.selectbox(
    "🎂 비교할 연령대 선택",
    ages,
    index=2,
    key="population_04_ranking_age"
)


# ==========================================
# 12. 선택 연령대의 자치구별 인구 추출
# ==========================================

ranking_column = (
    f"{selected_year}년_"
    f"{gender_column}_"
    f"{selected_age}"
)

if ranking_column not in district_df.columns:

    st.error(
        f"데이터 열을 찾을 수 없습니다: {ranking_column}"
    )

else:

    ranking_df = district_df[
        ["행정구역", ranking_column]
    ].copy()

    ranking_df["인구수"] = pd.to_numeric(
        ranking_df[ranking_column]
        .astype(str)
        .str.replace(",", ""),
        errors="coerce"
    ).fillna(0)

    # 인구수 내림차순 정렬
    ranking_df = ranking_df.sort_values(
        by="인구수",
        ascending=False
    ).reset_index(drop=True)

    ranking_df["순위"] = ranking_df.index + 1


    # ======================================
    # 13. 인구 1위 자치구 표시
    # ======================================

    top_district = ranking_df.iloc[0]

    st.success(
        f"🥇 {selected_year}년 {selected_age} "
        f"인구가 가장 많은 지역은 "
        f"{top_district['행정구역']}입니다!"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "🏆 인구 1위 자치구",
            top_district["행정구역"]
        )

    with col2:
        st.metric(
            "👥 해당 연령 인구",
            f"{int(top_district['인구수']):,}명"
        )


    # ======================================
    # 14. 자치구별 가로 막대그래프
    # ======================================

    st.subheader(
        f"📊 {selected_age} 자치구별 인구 순위"
    )

    fig2 = go.Figure()

    fig2.add_trace(
        go.Bar(
            x=ranking_df["인구수"],
            y=ranking_df["행정구역"],

            orientation="h",

            name="인구수",

            marker=dict(
                color="red"
            ),

            text=ranking_df["인구수"].apply(
                lambda x: f"{int(x):,}명"
            ),

            textposition="outside",

            cliponaxis=False,

            hovertemplate=(
                "행정구역: %{y}<br>"
                "인구수: %{x:,.0f}명"
                "<extra></extra>"
            )
        )
    )

    fig2.update_layout(
        height=750,

        plot_bgcolor="white",
        paper_bgcolor="white",

        font=dict(
            family="Malgun Gothic, AppleGothic, NanumGothic, sans-serif",
            size=12,
            color="black"
        ),

        xaxis=dict(
            title="인구수 (명)",

            showgrid=True,
            gridcolor="#dddddd",

            separatethousands=True
        ),

        yaxis=dict(
            title="행정구역",

            categoryorder="array",

            categoryarray=ranking_df[
                "행정구역"
            ].tolist()[::-1],

            showgrid=False
        ),

        margin=dict(
            l=110,
            r=100,
            t=40,
            b=60
        )
    )

    st.plotly_chart(
        fig2,
        use_container_width=True,
        key="population_04_bar_chart"
    )


    # ======================================
    # 15. 자치구별 순위 데이터 표
    # ======================================

    with st.expander(
        "📋 자치구별 상세 순위 확인",
        key="population_04_ranking_expander"
    ):

        display_ranking = ranking_df[
            ["순위", "행정구역", "인구수"]
        ].copy()

        display_ranking["인구수"] = (
            display_ranking["인구수"]
            .apply(lambda x: f"{int(x):,}명")
        )

        st.dataframe(
            display_ranking,
            use_container_width=True,
            hide_index=True
        )


# ==========================================
# 16. 연령별 상세 데이터
# ==========================================

with st.expander(
    "📋 선택 지역 연령별 상세 데이터",
    key="population_04_detail_expander"
):

    display_df = chart_df.copy()

    display_df["인구수"] = (
        display_df["인구수"]
        .apply(lambda x: f"{x:,}명")
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 17. 하단 안내
# ==========================================

st.divider()

st.caption(
    "서울특별시 인구 통계 분석 | "
    "2020~2025년 | 자료: population.csv"
)
