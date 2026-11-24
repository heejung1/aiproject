
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="서울 제과·제빵 상권 분석",
    page_icon="🥐",
    layout="wide"
)

DATA_DIR = Path(__file__).parent / "data"
SALES_FILE = DATA_DIR / "sales_2025.csv"
STORES_FILE = DATA_DIR / "stores_2025.csv"

st.title("🥐 서울 제과·제빵 상권 분석 시스템")
st.write(
    "서울시 2025년 상권분석서비스 CSV 자료를 이용해 "
    "제과점·커피음료 업종의 매출과 점포 현황을 분석합니다."
)
st.caption(
    "자료: 서울시 상권분석서비스 · 추정매출-상권 / 점포-상권 · "
    "2025년 1~4분기"
)

# --------------------------------------------------
# CSV 불러오기
# --------------------------------------------------
@st.cache_data(show_spinner="CSV 데이터를 불러오는 중...")
def read_csv_file(file_bytes):
    """CSV 파일을 여러 인코딩으로 시도해 읽습니다."""
    last_error = None
    for encoding in ("cp949", "utf-8-sig", "euc-kr", "utf-8"):
        try:
            from io import BytesIO
            return pd.read_csv(
                BytesIO(file_bytes),
                encoding=encoding,
                low_memory=False
            )
        except Exception as exc:
            last_error = exc
    raise ValueError(f"CSV 파일을 읽지 못했습니다: {last_error}")


def load_data(uploaded_file, local_path):
    """업로드 파일이 있으면 업로드 파일, 없으면 data 폴더 파일을 사용합니다."""
    if uploaded_file is not None:
        return read_csv_file(uploaded_file.getvalue())
    if local_path.exists():
        return read_csv_file(local_path.read_bytes())
    return None


# 실제 업로드된 CSV의 열 이름에 맞춘 설정
SALES_REQUIRED = {
    "quarter": "기준_년분기_코드",
    "market": "상권_코드_명",
    "industry": "서비스_업종_코드_명",
    "sales": "당월_매출_금액",
    "transactions": "당월_매출_건수",
}

STORE_REQUIRED = {
    "quarter": "stdr_yyqu_cd",
    "market": "trdar_cd_nm",
    "industry": "svc_induty_cd_nm",
    "stores": "stor_co",
    "similar_stores": "similr_induty_stor_co",
    "franchise_stores": "frc_stor_co",
}


def make_analysis(sales_raw, stores_raw):
    """분기·상권명·업종명으로 매출 자료와 점포 자료를 결합합니다."""
    missing_sales = [
        col for col in SALES_REQUIRED.values()
        if col not in sales_raw.columns
    ]
    missing_stores = [
        col for col in STORE_REQUIRED.values()
        if col not in stores_raw.columns
    ]

    if missing_sales:
        raise ValueError(
            "추정매출 CSV에 필요한 열이 없습니다: "
            + ", ".join(missing_sales)
        )
    if missing_stores:
        raise ValueError(
            "점포 CSV에 필요한 열이 없습니다: "
            + ", ".join(missing_stores)
        )

    sales = sales_raw[list(SALES_REQUIRED.values())].rename(
        columns={value: key for key, value in SALES_REQUIRED.items()}
    ).copy()

    stores = stores_raw[list(STORE_REQUIRED.values())].rename(
        columns={value: key for key, value in STORE_REQUIRED.items()}
    ).copy()

    # 분기 코드는 숫자로 변환
    for frame in (sales, stores):
        frame["quarter"] = pd.to_numeric(
            frame["quarter"], errors="coerce"
        )

    for col in ("sales", "transactions"):
        sales[col] = pd.to_numeric(sales[col], errors="coerce")

    for col in ("stores", "similar_stores", "franchise_stores"):
        stores[col] = pd.to_numeric(stores[col], errors="coerce")

    # 이름 열의 공백 차이를 줄여 결합 정확도를 높입니다.
    for frame in (sales, stores):
        for col in ("market", "industry"):
            frame[col] = frame[col].astype("string").str.strip()

    sales = sales.dropna(
        subset=["quarter", "market", "industry", "sales"]
    ).copy()
    stores = stores.dropna(
        subset=["quarter", "market", "industry", "stores"]
    ).copy()

    sales["quarter"] = sales["quarter"].astype(int)
    stores["quarter"] = stores["quarter"].astype(int)

    # 분기 + 상권명 + 업종명으로 결합
    join_keys = ["quarter", "market", "industry"]

    # 동일 결합 키가 여러 개면 중복 점포 자료를 합산
    if stores.duplicated(join_keys).any():
        stores = stores.groupby(
            join_keys, as_index=False
        ).agg(
            stores=("stores", "sum"),
            similar_stores=("similar_stores", "sum"),
            franchise_stores=("franchise_stores", "sum")
        )

    result = sales.merge(
        stores[join_keys + [
            "stores", "similar_stores", "franchise_stores"
        ]],
        on=join_keys,
        how="left",
        validate="one_to_one"
    )

    result["stores"] = result["stores"].fillna(0)
    result["similar_stores"] = result["similar_stores"].fillna(0)
    result["franchise_stores"] = result["franchise_stores"].fillna(0)

    result["sales_per_store"] = np.where(
        result["stores"] > 0,
        result["sales"] / result["stores"],
        np.nan
    )

    result["year"] = result["quarter"] // 10
    result["quarter_no"] = result["quarter"] % 10
    result["quarter_label"] = result.apply(
        lambda row: (
            f"{int(row['year'])}년 "
            f"{int(row['quarter_no'])}분기"
        ),
        axis=1
    )

    return result


def won(value):
    if pd.isna(value):
        return "-"
    value = float(value)
    if abs(value) >= 100_000_000:
        return f"{value / 100_000_000:,.1f}억 원"
    if abs(value) >= 10_000:
        return f"{value / 10_000:,.0f}만 원"
    return f"{value:,.0f}원"


# --------------------------------------------------
# 사이드바: 파일 업로드와 분석 조건
# --------------------------------------------------
with st.sidebar:
    st.header("📂 데이터 파일")
    st.write(
        "기본 CSV는 프로젝트의 data 폴더에서 자동으로 읽습니다. "
        "다른 자료를 분석하려면 아래에서 업로드하세요."
    )
    sales_upload = st.file_uploader(
        "추정매출-상권 CSV",
        type=["csv"],
        key="sales_csv"
    )
    stores_upload = st.file_uploader(
        "점포-상권 CSV",
        type=["csv"],
        key="stores_csv"
    )

try:
    sales_raw = load_data(sales_upload, SALES_FILE)
    stores_raw = load_data(stores_upload, STORES_FILE)

    if sales_raw is None or stores_raw is None:
        st.warning(
            "매출 CSV와 점포 CSV가 필요합니다. "
            "프로젝트의 data 폴더에 두 파일을 넣거나 "
            "왼쪽 메뉴에서 각각 업로드해 주세요."
        )
        st.stop()

    data = make_analysis(sales_raw, stores_raw)

except Exception as exc:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {exc}")
    st.stop()

# 실제 결합 상태 안내
matched_rows = int(data["stores"].gt(0).sum())
st.sidebar.success(
    f"데이터 결합 완료: {len(data):,}개 매출 행"
)

with st.sidebar:
    st.caption(
        f"점포 수가 연결된 행: {matched_rows:,}개"
    )
    st.divider()
    st.header("🔎 분석 조건")

all_industries = sorted(data["industry"].dropna().unique().tolist())
preferred = [
    item for item in ("제과점", "커피-음료")
    if item in all_industries
]
if not preferred:
    preferred = all_industries

with st.sidebar:
    selected_industries = st.multiselect(
        "업종 선택",
        options=all_industries,
        default=preferred
    )

    all_markets = sorted(data["market"].dropna().unique().tolist())
    selected_markets = st.multiselect(
        "상권 선택 (비우면 전체)",
        options=all_markets,
        default=[]
    )

if not selected_industries:
    st.warning("분석할 업종을 하나 이상 선택해 주세요.")
    st.stop()

filtered = data[
    data["industry"].isin(selected_industries)
].copy()

if selected_markets:
    filtered = filtered[
        filtered["market"].isin(selected_markets)
    ]

if filtered.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

latest_q = int(filtered["quarter"].max())
latest = filtered[filtered["quarter"] == latest_q].copy()

# --------------------------------------------------
# 탭 구성
# --------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 전체 상권 현황",
    "⚖️ 지역·업종 비교",
    "🤖 AI 매출 예측",
    "📥 데이터 다운로드"
])

# --------------------------------------------------
# 탭 1: 전체 상권 현황
# --------------------------------------------------
with tab1:
    st.header("최근 분기 상권 현황")

    total_sales = latest["sales"].sum()
    total_stores = latest["stores"].sum()
    total_transactions = latest["transactions"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("추정 매출 합계", won(total_sales))
    col2.metric("점포 수 합계", f"{total_stores:,.0f}개")
    col3.metric("매출 건수 합계", f"{total_transactions:,.0f}건")

    st.caption(
        f"기준: {latest_q // 10}년 {latest_q % 10}분기"
    )

    trend = (
        filtered.groupby(
            ["quarter", "quarter_label"], as_index=False
        )
        .agg(
            sales=("sales", "sum"),
            stores=("stores", "sum")
        )
        .sort_values("quarter")
    )

    fig = px.line(
        trend,
        x="quarter_label",
        y="sales",
        markers=True,
        title="분기별 추정 매출 변화"
    )
    fig.update_layout(
        xaxis_title="분기",
        yaxis_title="추정 매출(원)"
    )
    st.plotly_chart(fig, use_container_width=True)

    market_rank = (
        latest.groupby("market", as_index=False)
        .agg(
            sales=("sales", "sum"),
            stores=("stores", "sum"),
            transactions=("transactions", "sum")
        )
        .sort_values("sales", ascending=False)
    )

    fig = px.bar(
        market_rank.head(20),
        x="market",
        y="sales",
        color="stores",
        title="추정 매출 상위 20개 상권",
        labels={
            "market": "상권",
            "sales": "추정 매출(원)",
            "stores": "점포 수"
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        market_rank,
        use_container_width=True,
        hide_index=True
    )

# --------------------------------------------------
# 탭 2: 지역·업종 비교
# --------------------------------------------------
with tab2:
    st.header("상권별 경쟁 환경 비교")

    compare = (
        latest.groupby(
            ["market", "industry"], as_index=False
        )
        .agg(
            sales=("sales", "sum"),
            stores=("stores", "sum"),
            transactions=("transactions", "sum")
        )
    )

    compare["sales_per_store"] = np.where(
        compare["stores"] > 0,
        compare["sales"] / compare["stores"],
        np.nan
    )

    metric_choice = st.selectbox(
        "비교 기준",
        ["추정 매출", "점포 수", "점포당 추정 매출", "매출 건수"]
    )

    metric_map = {
        "추정 매출": "sales",
        "점포 수": "stores",
        "점포당 추정 매출": "sales_per_store",
        "매출 건수": "transactions"
    }
    metric = metric_map[metric_choice]
    ranked = compare.sort_values(
        metric, ascending=False
    ).head(25)

    fig = px.bar(
        ranked,
        x="market",
        y=metric,
        color="industry",
        barmode="group",
        title=f"상권별 {metric_choice} 상위 25개"
    )
    fig.update_layout(
        xaxis_title="상권",
        yaxis_title=metric_choice
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.scatter(
        compare,
        x="stores",
        y="sales",
        color="industry",
        size="transactions",
        hover_name="market",
        title="점포 수와 추정 매출의 관계",
        labels={
            "stores": "점포 수",
            "sales": "추정 매출(원)",
            "transactions": "매출 건수"
        }
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        compare.sort_values("sales", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "매출이 높은 상권은 소비 수요가 클 수 있지만 "
        "점포 수도 많으면 경쟁이 치열할 수 있습니다. "
        "점포당 매출은 상권 전체 매출을 점포 수로 나눈 "
        "단순 지표이며 개별 매장의 실제 매출이 아닙니다."
    )

# --------------------------------------------------
# 탭 3: AI 매출 예측
# --------------------------------------------------
with tab3:
    st.header("🤖 다음 분기 매출 예측")
    st.write(
        "랜덤 포레스트 회귀 모델을 이용해 "
        "상권·업종·분기·점포 수의 패턴으로 "
        "다음 분기 매출을 추정합니다."
    )

    model_df = filtered.dropna(
        subset=["sales", "stores"]
    ).copy()
    model_df = model_df[model_df["stores"] >= 0]

    if len(model_df) < 30 or model_df["quarter"].nunique() < 2:
        st.warning("예측을 수행하기에 데이터가 충분하지 않습니다.")
    else:
        features = model_df[
            ["market", "industry", "quarter_no", "stores"]
        ].copy()

        X = pd.get_dummies(
            features,
            columns=["market", "industry"],
            dtype=int
        )
        y = model_df["sales"]

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42
        )

        model = RandomForestRegressor(
            n_estimators=250,
            max_depth=12,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)

        validation_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, validation_pred)

        st.metric(
            "검증 데이터 평균 절대 오차(MAE)",
            won(mae)
        )
        st.caption(
            "검증은 2025년 자료 일부를 무작위로 나누어 진행했습니다. "
            "2025년 4개 분기만 사용하므로 장기 예측이 아닌 "
            "참고용 패턴 추정입니다."
        )

        last_quarter = int(model_df["quarter"].max())
        year = last_quarter // 10
        quarter_no = last_quarter % 10

        if quarter_no == 4:
            next_quarter = (year + 1) * 10 + 1
        else:
            next_quarter = year * 10 + quarter_no + 1

        next_quarter_no = next_quarter % 10

        latest_inputs = (
            model_df.sort_values("quarter")
            .groupby(
                ["market", "industry"],
                as_index=False
            )
            .tail(1)
            .copy()
        )
        latest_inputs["quarter_no"] = next_quarter_no

        future_features = latest_inputs[
            ["market", "industry", "quarter_no", "stores"]
        ]

        future_X = pd.get_dummies(
            future_features,
            columns=["market", "industry"],
            dtype=int
        ).reindex(columns=X.columns, fill_value=0)

        latest_inputs["predicted_sales"] = model.predict(future_X)

        st.success(
            f"예측 대상 분기: "
            f"{next_quarter // 10}년 {next_quarter_no}분기"
        )

        forecast = (
            latest_inputs.groupby("market", as_index=False)
            ["predicted_sales"]
            .sum()
            .sort_values("predicted_sales", ascending=False)
        )

        fig = px.bar(
            forecast.head(25),
            x="market",
            y="predicted_sales",
            title="다음 분기 상권별 예측 매출 상위 25개"
        )
        fig.update_layout(
            xaxis_title="상권",
            yaxis_title="예측 추정 매출(원)"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            forecast,
            use_container_width=True,
            hide_index=True
        )

        forecast_csv = forecast.to_csv(
            index=False,
            encoding="utf-8-sig"
        ).encode("utf-8-sig")

        st.download_button(
            "예측 결과 CSV 다운로드",
            data=forecast_csv,
            file_name="seoul_bakery_sales_forecast.csv",
            mime="text/csv"
        )

        st.warning(
            "예측값은 실제 미래 매출이 아닙니다. "
            "2025년 4개 분기만으로 학습했으며 임대료, "
            "유동인구, 경쟁점포 변화, 소비심리 등은 반영하지 못합니다."
        )

# --------------------------------------------------
# 탭 4: CSV 다운로드
# --------------------------------------------------
with tab4:
    st.header("📥 분석 데이터 다운로드")

    csv_data = filtered.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")

    st.download_button(
        "현재 분석 데이터 CSV 다운로드",
        data=csv_data,
        file_name="seoul_bakery_market_analysis.csv",
        mime="text/csv"
    )

    st.dataframe(
        filtered.head(300),
        use_container_width=True,
        hide_index=True
    )

# --------------------------------------------------
# 진로 연계 및 데이터 한계
# --------------------------------------------------
with st.expander("📘 데이터 해석 및 제과·제빵 진로 연계"):
    st.markdown("""
    **진로 연계 활용**

    - 제과점 업종을 선택하면 베이커리 전문점의 상권별
      추정 매출과 점포 수를 비교할 수 있습니다.
    - 커피-음료 업종을 함께 선택하면 카페형 베이커리와
      연관된 상권 환경을 살펴볼 수 있습니다.
    - 매출 규모, 점포 수, 점포당 추정 매출을 함께 비교해
      창업 후보 상권을 탐색할 수 있습니다.

    **데이터의 한계**

    - 추정 매출은 개별 점포의 실제 매출이 아니라
      서울시 상권분석서비스의 추정치입니다.
    - 현재 매출 CSV에는 상권 코드와 상권 유형 열이 없어
      분기·상권명·업종명 기준으로 점포 자료와 결합했습니다.
    - 임대료, 권리금, 유동인구, 원재료비, 매장 면적 등은
      이 두 CSV만으로 확인할 수 없습니다.
    - 2025년 4개 분기만으로 만든 예측은 표본 기간이 짧아
      신뢰도에 한계가 있습니다.
    - 실제 창업 입지는 현장 조사와 추가 자료를 함께 확인해야 합니다.
    """)

st.caption(
    "교육·탐구 목적의 분석 도구 | "
    "데이터: 서울시 상권분석서비스 2025년 자료"
)
