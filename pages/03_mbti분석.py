
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# =====================================
# 1. 페이지 설정
# =====================================

st.set_page_config(
    page_title="국가별 MBTI 분석",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 World MBTI Explorer")
st.subheader("국가별 MBTI 유형 비율 분석")
st.write("국가를 선택하고 MBTI 유형별 비율을 비교해 보세요!")

# =====================================
# 2. CSV 파일 경로 설정
# =====================================

# 현재 파일은 pages 폴더 안에 있음
# parent : pages 폴더
# parent.parent : 프로젝트 상위 폴더

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = BASE_DIR / "countriesMBTI_16types.csv"


# =====================================
# 3. CSV 데이터 불러오기
# =====================================

@st.cache_data
def load_data():

    df = pd.read_csv(CSV_PATH)

    df.columns = df.columns.astype(str).str.strip()

    if "Country" not in df.columns:
        raise ValueError(
            "CSV 파일에서 Country 열을 찾을 수 없습니다."
        )

    mbti_columns = [
        col for col in df.columns
        if col != "Country"
    ]

    if len(mbti_columns) != 16:
        raise ValueError(
            f"MBTI 열이 16개가 아닙니다. 현재 {len(mbti_columns)}개입니다."
        )

    df["Country"] = (
        df["Country"].astype(str).str.strip()
    )

    for col in mbti_columns:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    df = df.dropna(subset=["Country"])
    df[mbti_columns] = df[mbti_columns].fillna(0)

    return df, mbti_columns


try:

    data, mbti_columns = load_data()

except FileNotFoundError:

    st.error(
        f"CSV 파일을 찾을 수 없습니다.\n\n"
        f"확인한 경로: {CSV_PATH}"
    )

    st.stop()

except Exception as e:

    st.error(f"데이터 오류: {e}")

    st.stop()


# =====================================
# 4. 국가 선택
# =====================================

st.sidebar.header("🌎 국가 선택")

countries = sorted(
    data["Country"].unique().tolist()
)

default_index = (
    countries.index("South Korea")
    if "South Korea" in countries
    else 0
)

selected_country = st.sidebar.selectbox(
    "분석할 국가를 선택하세요.",
    countries,
    index=default_index
)


# =====================================
# 5. 선택 국가 데이터 분석
# =====================================

country_data = data[
    data["Country"] == selected_country
].iloc[0]

chart_data = pd.DataFrame({

    "MBTI": mbti_columns,

    "비율": [
        float(country_data[col]) * 100
        for col in mbti_columns
    ]

})

# 비율 높은 순으로 정렬
chart_data = chart_data.sort_values(
    "비율",
    ascending=False
).reset_index(drop=True)


# =====================================
# 6. 상단 통계
# =====================================

top_mbti = chart_data.iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric(
    "🌍 선택 국가",
    selected_country
)

col2.metric(
    "🏆 1위 MBTI",
    top_mbti["MBTI"]
)

col3.metric(
    "📊 최고 비율",
    f'{top_mbti["비율"]:.2f}%'
)

st.divider()


# =====================================
# 7. 색상 그라데이션 함수
# =====================================

def hex_to_rgb(color):

    color = color.lstrip("#")

    return tuple(
        int(color[i:i+2], 16)
        for i in (0, 2, 4)
    )


def rgb_to_hex(rgb):

    return "#{:02x}{:02x}{:02x}".format(
        *rgb
    )


def interpolate_color(
    start_color,
    end_color,
    amount
):

    start = hex_to_rgb(start_color)
    end = hex_to_rgb(end_color)

    rgb = tuple(

        round(
            start[i]
            + (end[i] - start[i]) * amount
        )

        for i in range(3)

    )

    return rgb_to_hex(rgb)


# =====================================
# 8. 그래프 색상 지정
# =====================================

# 1위 빨간색
# 나머지 진한 파랑 -> 연한 파랑

blue_colors = [

    interpolate_color(
        "#155EEF",
        "#DCEBFF",
        i / max(len(chart_data) - 2, 1)
    )

    for i in range(len(chart_data) - 1)

]

bar_colors = ["#E53935"] + blue_colors


# =====================================
# 9. MBTI 막대그래프
# =====================================

st.subheader(
    f"📊 {selected_country}의 MBTI 비율"
)

st.caption(
    "🔴 1위 유형 / 🔵 나머지 유형"
)

fig = go.Figure(

    go.Bar(

        x=chart_data["비율"],

        y=chart_data["MBTI"],

        orientation="h",

        marker=dict(
            color=bar_colors
        ),

        text=[
            f"{value:.2f}%"
            for value in chart_data["비율"]
        ],

        textposition="outside",

        hovertemplate=
        "<b>%{y}</b><br>"
        "비율: %{x:.2f}%"
        "<extra></extra>"

    )

)


# =====================================
# 10. 그래프 디자인
# =====================================

fig.update_layout(

    height=650,

    xaxis_title="비율 (%)",

    yaxis_title="MBTI 유형",

    yaxis=dict(

        categoryorder="array",

        categoryarray=(
            chart_data["MBTI"].tolist()[::-1]
        )

    ),

    xaxis=dict(
        rangemode="tozero",
        showgrid=True,
        gridcolor="rgba(128,128,128,0.18)"
    ),

    plot_bgcolor="rgba(0,0,0,0)",

    paper_bgcolor="rgba(0,0,0,0)",

    margin=dict(
        l=30,
        r=60,
        t=30,
        b=40
    ),

    font=dict(size=13),

    showlegend=False

)

st.plotly_chart(
    fig,
    use_container_width=True
)


# =====================================
# 11. MBTI 순위표
# =====================================

st.divider()

st.subheader("🏅 MBTI 순위")

display_data = chart_data.copy()

display_data.insert(
    0,
    "순위",
    range(1, len(display_data) + 1)
)

display_data["비율"] = (
    display_data["비율"].apply(
        lambda x: f"{x:.2f}%"
    )
)

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)


# =====================================
# 12. 데이터 안내
# =====================================

with st.expander("📌 데이터 안내"):

    st.write(
        f"현재 {len(countries)}개 국가의 데이터를 분석합니다."
    )

    st.write(
        "CSV 원본 비율에 100을 곱해 백분율로 표시합니다."
    )

    st.write(
        "이 자료는 제공된 CSV의 통계이며 "
        "각 국가 전체 인구의 실제 MBTI 분포를 "
        "확정적으로 의미하지는 않습니다."
    )


st.caption(
    "🌍 World MBTI Explorer"
)
