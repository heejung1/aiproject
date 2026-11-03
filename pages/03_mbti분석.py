import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# =====================================
# 1. 페이지 기본 설정
# =====================================

st.set_page_config(
    page_title="World MBTI Explorer",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 World MBTI Explorer")
st.subheader("세계 국가별 MBTI 비율 분석")
st.write("궁금한 국가를 선택하고 MBTI 유형별 비율을 확인해 보세요!")

# =====================================
# 2. CSV 파일 불러오기
# =====================================

CSV_PATH = Path(__file__).parent / "countriesMBTI_16types(1).csv"

@st.cache_data
def load_data():

    df = pd.read_csv(CSV_PATH)

    # 열 이름 공백 제거
    df.columns = df.columns.astype(str).str.strip()

    # 국가 열 확인
    if "Country" not in df.columns:
        raise ValueError("Country 열을 찾을 수 없습니다.")

    # MBTI 16개 열 추출
    mbti_columns = [
        col for col in df.columns
        if col != "Country"
    ]

    if len(mbti_columns) != 16:
        raise ValueError("MBTI 유형은 16개여야 합니다.")

    # 데이터 정리
    df["Country"] = df["Country"].astype(str).str.strip()

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
        "CSV 파일을 찾을 수 없습니다. "
        "app.py와 같은 폴더에 "
        "countriesMBTI_16types(1).csv를 넣어주세요."
    )
    st.stop()

except Exception as e:
    st.error(f"데이터 오류: {e}")
    st.stop()


# =====================================
# 3. 사이드바 국가 선택
# =====================================

st.sidebar.title("🌎 국가 선택")

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

st.sidebar.divider()

st.sidebar.info(
    "국가를 변경하면 해당 국가의 "
    "MBTI 비율 그래프가 자동으로 바뀝니다."
)


# =====================================
# 4. 선택한 국가 데이터 추출
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

# 높은 비율부터 정렬
chart_data = chart_data.sort_values(
    by="비율",
    ascending=False
).reset_index(drop=True)


# =====================================
# 5. 상단 통계 카드
# =====================================

top_mbti = chart_data.iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric(
    "🌍 선택 국가",
    selected_country
)

col2.metric(
    "🏆 가장 높은 MBTI",
    top_mbti["MBTI"]
)

col3.metric(
    "📊 최고 비율",
    f'{top_mbti["비율"]:.2f}%'
)

st.divider()


# =====================================
# 6. 그라데이션 색상 함수
# =====================================

def hex_to_rgb(hex_color):

    hex_color = hex_color.lstrip("#")

    return tuple(
        int(hex_color[i:i+2], 16)
        for i in (0, 2, 4)
    )


def rgb_to_hex(rgb):

    return "#{:02x}{:02x}{:02x}".format(
        *rgb
    )


def interpolate_color(
    start_hex,
    end_hex,
    amount
):

    start = hex_to_rgb(start_hex)
    end = hex_to_rgb(end_hex)

    rgb = tuple(

        round(
            start[i]
            + (end[i] - start[i]) * amount
        )

        for i in range(3)

    )

    return rgb_to_hex(rgb)


# =====================================
# 7. 그래프 색상 지정
# =====================================

# 1위는 빨간색
# 나머지는 진한 파랑에서 연한 파랑

blue_colors = [

    interpolate_color(
        "#155EEF",
        "#DCEBFF",
        i / max(len(chart_data) - 2, 1)
    )

    for i in range(len(chart_data) - 1)

]

bar_colors = [
    "#E53935"
] + blue_colors


# =====================================
# 8. MBTI 막대그래프
# =====================================

st.subheader(
    f"📊 {selected_country}의 MBTI 유형별 비율"
)

st.caption(
    "🔴 1위 MBTI | 🔵 나머지 MBTI"
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
# 9. 그래프 디자인
# =====================================

fig.update_layout(

    height=650,

    xaxis_title="MBTI 비율 (%)",

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
        r=55,
        t=25,
        b=35
    ),

    font=dict(
        size=13
    ),

    showlegend=False

)

st.plotly_chart(
    fig,
    use_container_width=True
)


# =====================================
# 10. MBTI 상세 순위표
# =====================================

st.divider()

st.subheader("🏅 MBTI 순위 상세 정보")

display_data = chart_data.copy()

display_data.insert(
    0,
    "순위",
    range(1, len(display_data) + 1)
)

display_data["비율"] = (
    display_data["비율"].map(
        lambda x: f"{x:.2f}%"
    )
)

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)


# =====================================
# 11. 데이터 안내
# =====================================

with st.expander("📌 데이터 안내"):

    st.write(
        f"현재 총 {len(countries)}개 국가의 "
        "MBTI 데이터를 분석하고 있습니다."
    )

    st.write(
        "그래프는 CSV 파일의 원본 비율에 "
        "100을 곱하여 백분율로 표시합니다."
    )

    st.write(
        "이 데이터는 제공된 자료를 시각화한 것으로, "
        "각 국가 전체 인구의 실제 MBTI 분포를 "
        "확정적으로 의미하지는 않습니다."
    )


st.caption(
    "🌍 World MBTI Explorer | Country MBTI Statistics"
)
