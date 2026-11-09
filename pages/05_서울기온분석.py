import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import calendar

# ----------------------------------
# 1. 페이지 설정
# ----------------------------------
st.set_page_config(
    page_title="월별 기온분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 기온분석")
st.write("원하는 월을 선택하여 연도별 최고기온과 최저기온을 비교해 보세요!")

# ----------------------------------
# 2. CSV 파일 경로 설정
# ----------------------------------
# 현재 py 파일은 pages 폴더 안에 있고
# CSV 파일은 상위 폴더에 있음

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "temperature.csv"

# ----------------------------------
# 3. 데이터 불러오기
# ----------------------------------
@st.cache_data
def load_data(file_path):

    try:
        df = pd.read_csv(file_path, encoding="cp949")

    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

    return df


try:
    df = load_data(str(CSV_PATH))

except FileNotFoundError:
    st.error("temperature.csv 파일을 찾을 수 없습니다.")
    st.write("현재 검색 경로:", str(CSV_PATH))
    st.stop()

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# ----------------------------------
# 4. 날짜 데이터 처리
# ----------------------------------

# 원본 일시 형식: Oct-07, Nov-07 등

month_map = {
    name: number
    for number, name in enumerate(calendar.month_abbr)
    if name
}

date_parts = df["일시"].astype(str).str.strip().str.extract(
    r"^([A-Za-z]{3})-(\d{2})$"
)

df["월"] = date_parts[0].str.title().map(month_map)

year_suffix = pd.to_numeric(
    date_parts[1],
    errors="coerce"
)

# 1907년부터 연도 순서 복원
years = []
century = 1900
previous_year = None

for value in year_suffix:

    if pd.isna(value):
        years.append(None)
        continue

    current_year = int(value)

    if previous_year is not None:
        if current_year < previous_year:
            century += 100

    years.append(century + current_year)
    previous_year = current_year

df["연도"] = years

# ----------------------------------
# 5. 기온 데이터 숫자형 변환
# ----------------------------------

temperature_columns = [
    "최고기온(℃)",
    "최저기온(℃)"
]

for col in temperature_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = df.dropna(
    subset=["연도", "월"]
)

df["연도"] = df["연도"].astype(int)
df["월"] = df["월"].astype(int)

# ----------------------------------
# 6. 월 선택
# ----------------------------------

st.subheader("📅 분석할 월 선택")

selected_month = st.selectbox(
    "월을 선택하세요.",
    options=list(range(1, 13)),
    format_func=lambda x: f"{x}월"
)

# ----------------------------------
# 7. 선택한 월의 데이터 추출
# ----------------------------------

month_data = df[
    df["월"] == selected_month
].copy()

month_data = month_data.sort_values("연도")

# 연도별 최고기온과 최저기온 평균
yearly_data = (
    month_data
    .groupby("연도")[temperature_columns]
    .mean()
    .reset_index()
)

# ----------------------------------
# 8. 그래프 생성
# ----------------------------------

if yearly_data.empty:

    st.warning("선택한 월의 데이터가 없습니다.")

else:

    st.success(
        f"📊 {selected_month}월 연도별 기온 분석 결과입니다."
    )

    fig = go.Figure()

    # 최고기온: 핫핑크
    fig.add_trace(
        go.Scatter(
            x=yearly_data["연도"],
            y=yearly_data["최고기온(℃)"],
            mode="lines+markers",
            name="최고기온",
            line=dict(
                color="hotpink",
                width=3
            ),
            marker=dict(size=6)
        )
    )

    # 최저기온: 파란색
    fig.add_trace(
        go.Scatter(
            x=yearly_data["연도"],
            y=yearly_data["최저기온(℃)"],
            mode="lines+markers",
            name="최저기온",
            line=dict(
                color="blue",
                width=3
            ),
            marker=dict(size=6)
        )
    )

    # 그래프 제목 및 축 설정
    fig.update_layout(
        title={
            "text": "월별 기온분석",
            "x": 0.5,
            "xanchor": "center"
        },
        xaxis_title="연도",
        yaxis_title="온도(℃)",
        legend_title="범례",
        hovermode="x unified",
        template="plotly_white",
        height=550
    )

    # 그래프 출력
    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ----------------------------------
    # 9. 기온 통계
    # ----------------------------------

    st.subheader("📈 기온 통계")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "평균 최고기온",
            f"{yearly_data['최고기온(℃)'].mean():.1f}℃"
        )

    with col2:

        st.metric(
            "평균 최저기온",
            f"{yearly_data['최저기온(℃)'].mean():.1f}℃"
        )

    # ----------------------------------
    # 10. 상세 데이터
    # ----------------------------------

    with st.expander("연도별 상세 데이터 확인하기"):

        st.dataframe(
            yearly_data,
            use_container_width=True,
            hide_index=True
        )

# ----------------------------------
# 11. 하단 안내
# ----------------------------------

st.divider()

st.caption(
    "🌡️ 월별 기온분석 | Pandas · Streamlit · Plotly"
)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# -----------------------------------------
# 1. 페이지 설정
# -----------------------------------------
st.set_page_config(
    page_title="서울 기온 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 기온 데이터 분석")
st.write("서울의 기온 변화를 다양한 그래프로 살펴보세요!")

st.divider()

# -----------------------------------------
# 2. CSV 파일 경로
# -----------------------------------------
# py 파일은 pages 폴더
# csv 파일은 상위 폴더

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "temperature.csv"

# -----------------------------------------
# 3. 데이터 불러오기
# -----------------------------------------
@st.cache_data
def load_data():

    try:
        data = pd.read_csv(
            CSV_PATH,
            encoding="cp949"
        )

    except UnicodeDecodeError:
        data = pd.read_csv(
            CSV_PATH,
            encoding="utf-8-sig"
        )

    return data


try:
    df = load_data()

except Exception as e:
    st.error(f"데이터를 불러올 수 없습니다: {e}")
    st.stop()

# -----------------------------------------
# 4. 날짜 데이터 처리
# -----------------------------------------

# 날짜 형식: Oct-07, Jan-08 등
date_parts = df["일시"].astype(str).str.strip().str.extract(
    r"^([A-Za-z]{3})-(\d{2})$"
)

month_map = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12
}

df["월"] = date_parts[0].str.title().map(month_map)

# 07~99는 1907~1999년
# 00~26은 2000~2026년
year_suffix = pd.to_numeric(
    date_parts[1],
    errors="coerce"
)

df["연도"] = year_suffix.apply(
    lambda x: (
        1900 + int(x) if x >= 7
        else 2000 + int(x)
    ) if pd.notna(x) else None
)

# -----------------------------------------
# 5. 기온 데이터 숫자형 변환
# -----------------------------------------

temp_columns = [
    "평균기온(℃)",
    "최고기온(℃)",
    "최저기온(℃)"
]

for col in temp_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = df.dropna(
    subset=["연도", "월"]
).copy()

df["연도"] = df["연도"].astype(int)
df["월"] = df["월"].astype(int)

# -----------------------------------------
# 6. 데이터 기간 안내
# -----------------------------------------

min_year = df["연도"].min()
max_year = df["연도"].max()

st.info(
    f"📅 서울 기온 데이터 수집 기간: "
    f"{min_year}년 ~ {max_year}년"
)

# 월 이름
month_names = [
    "1월", "2월", "3월", "4월",
    "5월", "6월", "7월", "8월",
    "9월", "10월", "11월", "12월"
]

# -----------------------------------------
# 그래프 1
# 서울 월별 평균기온
# -----------------------------------------

st.header("1️⃣ 서울 월별 평균기온")
st.write("전체 관측 기간을 기준으로 월별 평균기온을 비교합니다.")

monthly_avg = (
    df.groupby("월")["평균기온(℃)"]
    .mean()
    .reindex(range(1, 13))
)

fig1 = go.Figure()

fig1.add_trace(
    go.Scatter(
        x=month_names,
        y=monthly_avg.values,
        mode="lines+markers",
        name="월별 평균기온",
        line=dict(
            color="#FF1493",
            width=3
        ),
        marker=dict(size=9)
    )
)

fig1.update_layout(
    title="서울 월별 평균기온",
    xaxis_title="월",
    yaxis_title="평균기온(℃)",
    template="plotly_white",
    height=450,
    hovermode="x unified",
    xaxis=dict(
        categoryorder="array",
        categoryarray=month_names
    ),
    showlegend=True
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

st.divider()

# -----------------------------------------
# 그래프 2
# 연도별 최고기온과 최저기온
# -----------------------------------------

st.header("2️⃣ 연도별 최고기온과 최저기온")
st.write("각 연도의 월별 최고기온 중 가장 높은 값과 월별 최저기온 중 가장 낮은 값을 비교합니다.")

yearly_data = (
    df.groupby("연도")
    .agg(
        최고기온=("최고기온(℃)", "max"),
        최저기온=("최저기온(℃)", "min")
    )
    .reset_index()
    .sort_values("연도")
)

fig2 = go.Figure()

# 최고기온
fig2.add_trace(
    go.Scatter(
        x=yearly_data["연도"],
        y=yearly_data["최고기온"],
        mode="lines+markers",
        name="연도별 최고기온",
        line=dict(
            color="#FF1493",
            width=3
        ),
        marker=dict(size=5)
    )
)

# 최저기온
fig2.add_trace(
    go.Scatter(
        x=yearly_data["연도"],
        y=yearly_data["최저기온"],
        mode="lines+markers",
        name="연도별 최저기온",
        line=dict(
            color="#0000FF",
            width=3
        ),
        marker=dict(size=5)
    )
)

fig2.update_layout(
    title="서울 연도별 최고기온과 최저기온",
    xaxis_title="연도",
    yaxis_title="온도(℃)",
    template="plotly_white",
    height=500,
    hovermode="x unified",
    xaxis=dict(
        tickmode="linear",
        dtick=10
    ),
    showlegend=True
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

st.divider()

# -----------------------------------------
# 그래프 3
# 두 연도 비교
# -----------------------------------------

st.header("3️⃣ 두 연도 기온 비교")
st.write("비교하고 싶은 연도 2개를 선택하면 월별 평균기온을 비교할 수 있어요!")

available_years = sorted(
    df["연도"].unique().tolist()
)

col1, col2 = st.columns(2)

# 기본 선택 연도: 가장 최근의 완전한 연도 2개
complete_years = (
    df.groupby("연도")["월"]
    .nunique()
)

complete_years = sorted(
    complete_years[complete_years == 12].index.tolist()
)

if len(complete_years) >= 2:
    default_year1 = complete_years[-2]
    default_year2 = complete_years[-1]
else:
    default_year1 = available_years[-2]
    default_year2 = available_years[-1]

with col1:
    year1 = st.selectbox(
        "첫 번째 연도 선택",
        available_years,
        index=available_years.index(default_year1),
        key="year1"
    )

with col2:
    year2_options = [
        y for y in available_years if y != year1
    ]

    year2 = st.selectbox(
        "두 번째 연도 선택",
        year2_options,
        index=year2_options.index(
            default_year2 if default_year2 != year1
            else year2_options[-1]
        ),
        key="year2"
    )

# 선택한 두 연도의 데이터
compare_data = df[
    df["연도"].isin([year1, year2])
]

compare_monthly = (
    compare_data
    .pivot_table(
        index="월",
        columns="연도",
        values="평균기온(℃)",
        aggfunc="mean"
    )
    .reindex(range(1, 13))
)

fig3 = go.Figure()

# 첫 번째 연도
fig3.add_trace(
    go.Scatter(
        x=month_names,
        y=compare_monthly[year1],
        mode="lines+markers",
        name=f"{year1}년",
        line=dict(
            color="#FF1493",
            width=3
        ),
        marker=dict(size=8)
    )
)

# 두 번째 연도
fig3.add_trace(
    go.Scatter(
        x=month_names,
        y=compare_monthly[year2],
        mode="lines+markers",
        name=f"{year2}년",
        line=dict(
            color="#0000FF",
            width=3
        ),
        marker=dict(size=8)
    )
)

fig3.update_layout(
    title=f"{year1}년과 {year2}년 월별 평균기온 비교",
    xaxis_title="월",
    yaxis_title="평균기온(℃)",
    template="plotly_white",
    height=450,
    hovermode="x unified",
    xaxis=dict(
        categoryorder="array",
        categoryarray=month_names
    ),
    showlegend=True
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

# -----------------------------------------
# 7. 데이터 확인
# -----------------------------------------

with st.expander("📋 원본 데이터 확인하기"):

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

st.divider()

st.caption(
    "🌡️ 서울 기온 데이터 분석 | "
    "Pandas · Streamlit · Plotly"
)
