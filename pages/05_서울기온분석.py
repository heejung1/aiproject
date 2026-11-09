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
