import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

st.set_page_config(
    page_title="서울 제과·제빵 상권 분석",
    page_icon="🥐",
    layout="wide"
)

DATA_DIR = Path(__file__).parent / "data"

SALES_COLUMNS = {
    "quarter": "기준_년분기_코드",
    "market_type": "상권_구분_코드_명",
    "market_code": "상권_코드",
    "market": "상권_코드_명",
    "industry_code": "서비스_업종_코드",
    "industry": "서비스_업종_코드_명",
    "sales": "당월_매출_금액",
    "transactions": "당월_매출_건수",
}

STORE_COLUMNS = {
    "quarter": "stdr_yyqu_cd",
    "market_type": "trdar_se_cd_nm",
    "market_code": "trdar_cd",
    "market": "trdar_cd_nm",
    "industry_code": "svc_induty_cd",
    "industry": "svc_induty_cd_nm",
    "stores": "stor_co",
    "similar_stores": "similr_induty_stor_co",
    "franchise_stores": "frc_stor_co",
}


@st.cache_data(show_spinner=False)
def read_csv_from_zip_bytes(file_bytes):
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
        csv_names = [
            n for n in archive.namelist()
            if n.lower().endswith(".csv")
        ]

        if not csv_names:
            raise ValueError(
                "ZIP 안에서 CSV 파일을 찾지 못했습니다."
            )

        csv_bytes = archive.read(csv_names[0])

    last_error = None

    for encoding in (
        "cp949",
        "utf-8-sig",
        "euc-kr",
        "utf-8"
    ):
        try:
            return pd.read_csv(
                io.BytesIO(csv_bytes),
                encoding=encoding,
                low_memory=False
            )
        except Exception as exc:
            last_error = exc

    raise ValueError(
        f"CSV 인코딩을 읽지 못했습니다: {last_error}"
    )


def load_uploaded_or_local(uploaded_file, local_path):
    if uploaded_file is not None:
        return read_csv_from_zip_bytes(
            uploaded_file.getvalue()
        )

    if local_path.exists():
        return read_csv_from_zip_bytes(
            local_path.read_bytes()
        )

    return None


def make_analysis(sales_raw, stores_raw):

    missing_sales = [
        c for c in SALES_COLUMNS.values()
        if c not in sales_raw.columns
    ]

    missing_stores = [
        c for c in STORE_COLUMNS.values()
        if c not in stores_raw.columns
    ]

    if missing_sales:
        raise ValueError(
            "매출 CSV에서 필요한 열을 찾지 못했습니다: "
            + ", ".join(missing_sales)
        )

    if missing_stores:
        raise ValueError(
            "점포 CSV에서 필요한 열을 찾지 못했습니다: "
            + ", ".join(missing_stores)
        )

    sales = sales_raw[
        list(SALES_COLUMNS.values())
    ].rename(
        columns={
            v: k for k, v in SALES_COLUMNS.items()
        }
    )

    stores = stores_raw[
        list(STORE_COLUMNS.values())
    ].rename(
        columns={
            v: k for k, v in STORE_COLUMNS.items()
        }
    )

    key_cols = [
        "quarter",
        "market_code",
        "industry_code"
    ]

    for frame in (sales, stores):
        frame["quarter"] = pd.to_numeric(
            frame["quarter"],
            errors="coerce"
        )

        frame["market_code"] = (
            frame["market_code"].astype(str)
        )

        frame["industry_code"] = (
            frame["industry_code"].astype(str)
        )

    sales["sales"] = pd.to_numeric(
        sales["sales"],
        errors="coerce"
    )

    sales["transactions"] = pd.to_numeric(
        sales["transactions"],
        errors="coerce"
    )

    stores["stores"] = pd.to_numeric(
        stores["stores"],
        errors="coerce"
    )

    stores["similar_stores"] = pd.to_numeric(
        stores["similar_stores"],
        errors="coerce"
    )

    stores["franchise_stores"] = pd.to_numeric(
        stores["franchise_stores"],
        errors="coerce"
    )

    sales = sales.dropna(
        subset=["quarter", "sales"]
    )

    stores = stores.dropna(
        subset=["quarter", "stores"]
    )

    sales["quarter"] = (
        sales["quarter"].astype(int)
    )

    stores["quarter"] = (
        stores["quarter"].astype(int)
    )

    merged = sales.merge(
        stores[
            key_cols
            + [
                "stores",
                "similar_stores",
                "franchise_stores"
            ]
        ],
        on=key_cols,
        how="left",
        validate="many_to_one"
    )

    merged["stores"] = (
        merged["stores"].fillna(0)
    )

    merged["sales_per_store"] = np.where(
        merged["stores"] > 0,
        merged["sales"] / merged["stores"],
        np.nan
    )

    merged["year"] = (
        merged["quarter"] // 10
    )

    merged["quarter_no"] = (
        merged["quarter"] % 10
    )

    merged["quarter_label"] = merged.apply(
        lambda r:
        f"{int(r['year'])}년 "
        f"{int(r['quarter_no'])}분기",
        axis=1
    )

    merged["market"] = (
        merged["market"].fillna("이름 없음")
    )

    merged["industry"] = (
        merged["industry"].fillna("업종 미상")
    )

    merged["market_type"] = (
        merged["market_type"].fillna("구분 미상")
    )

    return merged


def won(value):
    if pd.isna(value):
        return "-"

    value = float(value)

    if abs(value) >= 100_000_000:
        return (
            f"{value / 100_000_000:,.1f}억 원"
        )

    if abs(value) >= 10_000:
        return (
            f"{value / 10_000:,.0f}만 원"
        )

    return f"{value:,.0f}원"


# --------------------------------------------------
# 메인 화면
# --------------------------------------------------

st.title(
    "🥐 서울 제과·제빵 상권 분석 시스템"
)

st.write(
    "서울시 2025년 상권분석서비스 자료를 이용해 "
    "제과점·커피음료 업종의 매출과 점포 현황을 살펴봅니다."
)

st.caption(
    "자료: 서울시 상권분석서비스 · "
    "추정매출-상권 / 점포-상권 · "
    "2025년 1~4분기"
)


# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------

with st.sidebar:

    st.header("📂 데이터")

    st.write(
        "프로젝트의 `data` 폴더에 원본 ZIP을 넣으면 "
        "자동으로 불러옵니다. "
        "다른 자료를 분석하려면 ZIP 파일을 업로드하세요."
    )

    sales_upload = st.file_uploader(
        "추정매출-상권 ZIP",
        type=["zip"]
    )

    stores_upload = st.file_uploader(
        "점포-상권 ZIP",
        type=["zip"]
    )

    st.divider()

    st.header("🔎 분석 조건")


try:

    sales_raw = load_uploaded_or_local(
        sales_upload,
        DATA_DIR / "sales_2025.zip"
    )

    stores_raw = load_uploaded_or_local(
        stores_upload,
        DATA_DIR / "stores_2025.zip"
    )

    if sales_raw is None or stores_raw is None:

        st.warning(
            "매출 ZIP과 점포 ZIP을 모두 `data` 폴더에 "
            "넣거나 왼쪽 메뉴에서 업로드해 주세요."
        )

        st.stop()

    data = make_analysis(
        sales_raw,
        stores_raw
    )

except Exception as exc:

    st.error(
        f"데이터를 불러오는 중 문제가 발생했습니다: {exc}"
    )

    st.stop()


# --------------------------------------------------
# 분석 조건 설정
# --------------------------------------------------

all_industries = sorted(
    data["industry"].dropna().unique().tolist()
)

preferred = [
    name for name in all_industries
    if name in ["제과점", "커피-음료"]
]

if not preferred:
    preferred = all_industries


with st.sidebar:

    selected_industries = st.multiselect(
        "업종 선택",
        all_industries,
        default=preferred
    )

    market_types = sorted(
        data["market_type"].dropna().unique().tolist()
    )

    selected_market_types = st.multiselect(
        "상권 유형",
        market_types,
        default=market_types
    )

    all_markets = sorted(
        data[
            data["market_type"].isin(
                selected_market_types
            )
        ]["market"].unique()
    )

    selected_markets = st.multiselect(
        "상권 선택 (비우면 전체)",
        all_markets,
        default=[]
    )


if not selected_industries:

    st.warning(
        "분석할 업종을 하나 이상 선택해 주세요."
    )

    st.stop()


filtered = data[
    data["industry"].isin(selected_industries)
    & data["market_type"].isin(
        selected_market_types
    )
].copy()


if selected_markets:

    filtered = filtered[
        filtered["market"].isin(selected_markets)
    ]


if filtered.empty:

    st.warning(
        "선택한 조건에 해당하는 데이터가 없습니다."
    )

    st.stop()


quarters = sorted(
    filtered["quarter"].unique()
)

latest_q = max(quarters)

latest = filtered[
    filtered["quarter"] == latest_q
].copy()


# --------------------------------------------------
# 탭 구성
# --------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 전체 상권 현황",
        "⚖️ 지역·업종 비교",
        "🤖 AI 매출 예측",
        "📥 데이터 다운로드"
    ]
)


# --------------------------------------------------
# 1. 전체 상권 현황
# --------------------------------------------------

with tab1:

    st.header("최근 분기 상권 현황")

    total_sales = latest["sales"].sum()

    total_stores = latest["stores"].sum()

    total_transactions = (
        latest["transactions"].sum()
    )

    avg_sales_per_store = (
        total_sales / total_stores
        if total_stores > 0
        else np.nan
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "추정 매출 합계",
        won(total_sales)
    )

    c2.metric(
        "점포 수 합계",
        f"{total_stores:,.0f}개"
    )

    c3.metric(
        "매출 건수 합계",
        f"{total_transactions:,.0f}건"
    )

    st.caption(
        f"기준: {int(latest_q)//10}년 "
        f"{int(latest_q)%10}분기 · "
        "선택 업종 및 상권"
    )

    trend = (
        filtered.groupby(
            ["quarter", "quarter_label"],
            as_index=False
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

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    market_rank = (
        latest.groupby(
            "market",
            as_index=False
        )
        .agg(
            sales=("sales", "sum"),
            stores=("stores", "sum"),
            transactions=("transactions", "sum")
        )
        .sort_values(
            "sales",
            ascending=False
        )
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

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        market_rank,
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 2. 지역·업종 비교
# --------------------------------------------------

with tab2:

    st.header("상권별 경쟁 환경 비교")

    compare = (
        latest.groupby(
            ["market", "industry"],
            as_index=False
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
        [
            "추정 매출",
            "점포 수",
            "점포당 추정 매출",
            "매출 건수"
        ]
    )

    metric_map = {
        "추정 매출": "sales",
        "점포 수": "stores",
        "점포당 추정 매출": "sales_per_store",
        "매출 건수": "transactions"
    }

    selected_metric = metric_map[
        metric_choice
    ]

    ranked = (
        compare.sort_values(
            selected_metric,
            ascending=False
        ).head(25)
    )

    fig = px.bar(
        ranked,
        x="market",
        y=selected_metric,
        color="industry",
        barmode="group",
        title=f"상권별 {metric_choice} 상위 25개"
    )

    fig.update_layout(
        xaxis_title="상권",
        yaxis_title=metric_choice
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

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

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        compare.sort_values(
            "sales",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "해석할 때 주의하세요. 매출이 높은 상권은 "
        "소비 수요가 클 수 있지만, 점포 수도 많으면 "
        "경쟁이 치열할 수 있습니다. "
        "점포당 매출은 상권 전체 매출을 점포 수로 "
        "나눈 단순 지표이며 개별 매장의 실제 매출이 아닙니다."
    )


# --------------------------------------------------
# 3. AI 매출 예측
# --------------------------------------------------

with tab3:

    st.header("🤖 다음 분기 매출 예측")

    st.write(
        "랜덤 포레스트 회귀 모델이 2025년 분기별 "
        "업종·상권·점포 수 패턴을 학습해 "
        "다음 분기 매출을 추정합니다."
    )

    model_df = filtered.dropna(
        subset=["sales", "stores"]
    ).copy()

    model_df = model_df[
        model_df["stores"] >= 0
    ]

    if (
        len(model_df) < 30
        or model_df["quarter"].nunique() < 2
    ):

        st.warning(
            "예측을 수행하기에 데이터가 충분하지 않습니다."
        )

    else:

        features = model_df[
            [
                "market",
                "industry",
                "market_type",
                "quarter_no",
                "stores"
            ]
        ].copy()

        X = pd.get_dummies(
            features,
            columns=[
                "market",
                "industry",
                "market_type"
            ],
            dtype=int
        )

        y = model_df["sales"]

        X_train, X_test, y_train, y_test = (
            train_test_split(
                X,
                y,
                test_size=0.2,
                random_state=42
            )
        )

        model = RandomForestRegressor(
            n_estimators=250,
            max_depth=12,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        model.fit(
            X_train,
            y_train
        )

        validation_pred = model.predict(
            X_test
        )

        mae = mean_absolute_error(
            y_test,
            validation_pred
        )

        st.metric(
            "검증 데이터 평균 절대 오차(MAE)",
            won(mae)
        )

        st.caption(
            "검증은 2025년 자료 일부를 무작위로 나누어 "
            "진행했습니다. 2025년 한 해 자료만 사용하므로 "
            "장기 추세 예측이 아니라 참고용 패턴 추정입니다."
        )

        last_quarter = int(
            model_df["quarter"].max()
        )

        year = last_quarter // 10
        qtr = last_quarter % 10

        if qtr == 4:

            next_quarter = (
                (year + 1) * 10 + 1
            )

        else:

            next_quarter = (
                year * 10 + qtr + 1
            )

        next_qtr_no = (
            next_quarter % 10
        )

        latest_inputs = (
            model_df.sort_values("quarter")
            .groupby(
                [
                    "market",
                    "industry",
                    "market_type"
                ],
                as_index=False
            )
            .tail(1)
            .copy()
        )

        latest_inputs["quarter_no"] = (
            next_qtr_no
        )

        future_features = latest_inputs[
            [
                "market",
                "industry",
                "market_type",
                "quarter_no",
                "stores"
            ]
        ]

        future_X = pd.get_dummies(
            future_features,
            columns=[
                "market",
                "industry",
                "market_type"
            ],
            dtype=int
        ).reindex(
            columns=X.columns,
            fill_value=0
        )

        latest_inputs["predicted_sales"] = (
            model.predict(future_X)
        )

        st.success(
            f"예측 대상 분기: "
            f"{next_quarter // 10}년 "
            f"{next_qtr_no}분기"
        )

        forecast = (
            latest_inputs.groupby(
                "market",
                as_index=False
            )["predicted_sales"]
            .sum()
            .sort_values(
                "predicted_sales",
                ascending=False
            )
        )

        fig = px.bar(
            forecast.head(25),
            x="market",
            y="predicted_sales",
            title=(
                "다음 분기 상권별 예측 "
                "추정 매출 상위 25개"
            )
        )

        fig.update_layout(
            xaxis_title="상권",
            yaxis_title="예측 추정 매출(원)"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            forecast,
            use_container_width=True,
            hide_index=True
        )

        forecast_csv = (
            forecast.to_csv(
                index=False,
                encoding="utf-8-sig"
            ).encode("utf-8-sig")
        )

        st.download_button(
            "예측 결과 CSV 다운로드",
            forecast_csv,
            file_name=(
                "seoul_bakery_sales_forecast.csv"
            ),
            mime="text/csv"
        )

        st.warning(
            "예측값은 실제 미래 매출이 아닙니다. "
            "2025년 4개 분기만으로 학습한 결과이므로 "
            "임대료, 유동인구, 경쟁점포 변화, "
            "소비심리 등을 반영하지 못합니다."
        )


# --------------------------------------------------
# 4. 데이터 다운로드
# --------------------------------------------------

with tab4:

    st.header("📥 분석 데이터 다운로드")

    csv_bytes = (
        filtered.to_csv(
            index=False,
            encoding="utf-8-sig"
        ).encode("utf-8-sig")
    )

    st.download_button(
        "현재 분석 데이터 CSV 다운로드",
        data=csv_bytes,
        file_name=(
            "seoul_bakery_market_analysis.csv"
        ),
        mime="text/csv"
    )

    st.dataframe(
        filtered.head(300),
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 데이터 해석 및 진로 연계
# --------------------------------------------------

with st.expander(
    "📘 데이터 해석 및 제과·제빵 진로 연계"
):

    st.markdown("""
    **진로 연계 활용**

    - 제과점 업종을 선택하면 베이커리 전문점의
      상권별 추정 매출과 점포 수를 비교할 수 있습니다.

    - 커피-음료 업종을 함께 선택하면 카페형 베이커리와
      연관된 상권 환경을 비교하는 데 참고할 수 있습니다.

    - 매출 규모, 점포 수, 점포당 추정 매출을 함께 살펴보며
      창업 후보 상권을 탐색할 수 있습니다.

    **데이터의 한계**

    - 추정 매출은 개별 점포의 실제 매출이 아니라
      서울시 상권분석서비스의 추정치입니다.

    - 이 자료에는 임대료, 권리금, 유동인구,
      원재료비, 매장 면적 등이 포함되어 있지 않습니다.

    - 2025년 자료만으로 만든 예측은 표본 기간이 짧아
      신뢰도에 한계가 있습니다.

    - 상권 비교 결과만으로 창업 성공 가능성을 판단하지 말고
      현장 조사와 추가 자료를 함께 확인해야 합니다.
    """)


st.caption(
    "교육·탐구 목적의 분석 도구 | "
    "데이터: 서울시 상권분석서비스 2025년 자료"
)
