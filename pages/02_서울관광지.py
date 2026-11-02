
import streamlit as st
import folium
from streamlit_folium import st_folium

# --------------------------------
# 서울 관광지 데이터
# --------------------------------

PLACES = [
    {
        "rank": 1,
        "name": "명동",
        "english": "Myeong-dong",
        "lat": 37.5636,
        "lon": 126.9869,
        "category": "쇼핑 · 먹거리",
        "description": "화장품, 패션 매장과 다양한 길거리 음식이 모여 있는 서울의 대표 쇼핑 거리예요.",
        "tip": "저녁에 방문하면 더욱 활기찬 분위기를 느낄 수 있어요."
    },
    {
        "rank": 2,
        "name": "N서울타워",
        "english": "N Seoul Tower",
        "lat": 37.5512,
        "lon": 126.9882,
        "category": "전망 · 야경",
        "description": "서울의 아름다운 전경을 감상할 수 있는 대표적인 전망 명소예요.",
        "tip": "해 질 무렵 방문하는 것을 추천해요."
    },
    {
        "rank": 3,
        "name": "코엑스",
        "english": "COEX",
        "lat": 37.5125,
        "lon": 127.0588,
        "category": "쇼핑 · 문화",
        "description": "쇼핑몰과 전시장, 별마당도서관 등이 있는 복합문화공간이에요.",
        "tip": "별마당도서관에서 멋진 사진을 남겨보세요."
    },
    {
        "rank": 4,
        "name": "강남역",
        "english": "Gangnam Station",
        "lat": 37.4979,
        "lon": 127.0276,
        "category": "쇼핑 · 거리",
        "description": "다양한 상점과 카페, 음식점이 모여 있는 서울의 대표 번화가예요.",
        "tip": "주변 카페와 맛집을 함께 방문해 보세요."
    },
    {
        "rank": 5,
        "name": "홍대",
        "english": "Hongdae",
        "lat": 37.5563,
        "lon": 126.9236,
        "category": "문화 · 공연",
        "description": "거리 공연과 개성 있는 상점, 카페가 유명한 젊음의 거리예요.",
        "tip": "주말에는 다양한 거리 공연을 구경할 수 있어요."
    },
    {
        "rank": 6,
        "name": "동대문디자인플라자",
        "english": "DDP",
        "lat": 37.5671,
        "lon": 127.0095,
        "category": "건축 · 전시",
        "description": "독특한 곡선형 건축물과 다양한 전시 및 디자인 행사가 열리는 장소예요.",
        "tip": "야간 조명이 켜진 DDP도 감상해 보세요."
    },
    {
        "rank": 7,
        "name": "경복궁",
        "english": "Gyeongbokgung Palace",
        "lat": 37.5796,
        "lon": 126.9770,
        "category": "역사 · 전통문화",
        "description": "조선 시대를 대표하는 궁궐로 한국의 전통문화를 경험할 수 있어요.",
        "tip": "한복을 입고 방문하면 특별한 추억을 만들 수 있어요."
    },
    {
        "rank": 8,
        "name": "북촌한옥마을",
        "english": "Bukchon Hanok Village",
        "lat": 37.5826,
        "lon": 126.9830,
        "category": "전통 · 산책",
        "description": "전통 한옥이 모여 있어 한국의 옛 주거 문화를 느낄 수 있는 마을이에요.",
        "tip": "주민들을 배려해 조용히 관람해 주세요."
    },
    {
        "rank": 9,
        "name": "광장시장",
        "english": "Gwangjang Market",
        "lat": 37.5700,
        "lon": 126.9997,
        "category": "전통시장 · 음식",
        "description": "빈대떡과 김밥 등 다양한 한국 전통 음식을 맛볼 수 있어요.",
        "tip": "다양한 길거리 음식을 경험해 보세요."
    },
    {
        "rank": 10,
        "name": "남대문시장",
        "english": "Namdaemun Market",
        "lat": 37.5592,
        "lon": 126.9777,
        "category": "전통시장 · 쇼핑",
        "description": "의류와 잡화, 기념품, 먹거리를 다양하게 판매하는 전통시장이에요.",
        "tip": "한국 전통 기념품을 찾아보세요."
    }
]


# --------------------------------
# 페이지 제목
# --------------------------------

st.title("🗺️ 서울 외국인 인기 관광지 TOP 10")

st.markdown("""
서울을 방문하는 외국인 관광객에게 추천하는
대표 관광지 10곳을 지도에서 확인해 보세요!

📍 지도 위 숫자를 클릭하면 관광지 정보를 확인할 수 있어요.
""")


# --------------------------------
# 서울 지도 만들기
# --------------------------------

m = folium.Map(
    location=[37.555, 126.985],
    zoom_start=12,
    tiles="OpenStreetMap",
    control_scale=True
)


# --------------------------------
# 관광지 마커 표시
# --------------------------------

for place in PLACES:

    popup_html = f"""
    <div style="font-family:Arial; width:220px;">
        <h3>{place['rank']}. {place['name']}</h3>
        <p><b>{place['english']}</b></p>
        <p>📌 {place['category']}</p>
        <p>{place['description']}</p>
    </div>
    """

    folium.Marker(
        location=[
            place["lat"],
            place["lon"]
        ],

        tooltip=f"{place['rank']}. {place['name']}",

        popup=folium.Popup(
            popup_html,
            max_width=280
        ),

        icon=folium.DivIcon(
            html=f"""
            <div style="
                background-color:#2563eb;
                color:white;
                border:2px solid white;
                border-radius:50%;
                width:32px;
                height:32px;
                text-align:center;
                line-height:28px;
                font-size:15px;
                font-weight:bold;
                box-shadow:0 2px 5px rgba(0,0,0,0.3);
            ">
                {place['rank']}
            </div>
            """,
            icon_size=(32, 32),
            icon_anchor=(16, 16)
        )

    ).add_to(m)


# --------------------------------
# 지도 화면 출력
# --------------------------------

st.subheader("📍 서울 관광지 지도")

st_folium(
    m,
    width=None,
    height=600,
    use_container_width=True,
    returned_objects=[]
)


# --------------------------------
# 관광지 설명
# --------------------------------

st.divider()

st.header("✨ 추천 관광지 TOP 10")

# 2열로 관광지 표시
columns = st.columns(2)

for i, place in enumerate(PLACES):

    with columns[i % 2]:

        with st.container(border=True):

            st.subheader(
                f"{place['rank']}. {place['name']}"
            )

            st.caption(
                f"{place['english']} | {place['category']}"
            )

            st.write(
                place["description"]
            )

            st.info(
                f"💡 방문 팁: {place['tip']}"
            )


# --------------------------------
# 관광 정보 출처
# --------------------------------

st.divider()

st.header("📚 관광 정보")

st.write("""
서울시의 외국인 관광객 방문 분석 자료와
서울의 주요 관광 명소를 참고하여 구성했습니다.
""")

st.markdown(
    "[서울시 공식 홈페이지 바로가기](https://english.seoul.go.kr/)"
)

st.caption(
    "※ 공식적인 단일 순위가 아닌 주요 관광 명소를 종합한 안내용 TOP 10입니다. "
    "실제 방문 전 운영 시간과 휴관일을 확인해 주세요."
)
