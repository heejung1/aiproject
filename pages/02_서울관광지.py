
import streamlit as st
import folium
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(
    page_title="서울 외국인 인기 관광지 TOP 10",
    page_icon="🗺️",
    layout="wide"
)

# 관광지 데이터
PLACES = [
    {
        "rank": 1,
        "name": "명동",
        "english": "Myeong-dong",
        "lat": 37.5636,
        "lon": 126.9869,
        "category": "쇼핑 · 먹거리",
        "description": "화장품과 패션 매장, 길거리 음식이 모여 있어 쇼핑과 K-푸드를 함께 즐기기 좋은 거리예요.",
        "tip": "저녁에는 사람이 많을 수 있으니 소지품을 잘 챙겨요."
    },
    {
        "rank": 2,
        "name": "N서울타워",
        "english": "N Seoul Tower",
        "lat": 37.5512,
        "lon": 126.9882,
        "category": "전망 · 야경",
        "description": "서울의 대표 전망 명소예요. 전망대에서 아름다운 서울의 풍경을 볼 수 있어요.",
        "tip": "해 질 무렵 방문하면 낮과 밤의 풍경을 모두 볼 수 있어요."
    },
    {
        "rank": 3,
        "name": "삼성역·코엑스",
        "english": "COEX",
        "lat": 37.5125,
        "lon": 127.0588,
        "category": "쇼핑 · 문화",
        "description": "대형 쇼핑 공간과 전시장이 모여 있어 쇼핑과 문화생활을 즐길 수 있어요.",
        "tip": "별마당도서관은 사진 촬영 장소로도 유명해요."
    },
    {
        "rank": 4,
        "name": "강남역",
        "english": "Gangnam",
        "lat": 37.4979,
        "lon": 127.0276,
        "category": "쇼핑 · 거리",
        "description": "상점과 음식점, 카페가 밀집한 활기찬 거리예요.",
        "tip": "약속 장소는 출구 번호로 정하면 편리해요."
    },
    {
        "rank": 5,
        "name": "홍대",
        "english": "Hongdae",
        "lat": 37.5563,
        "lon": 126.9236,
        "category": "문화 · 공연",
        "description": "개성 있는 상점과 카페, 거리 공연으로 유명한 젊음의 거리예요.",
        "tip": "주말 저녁에는 거리 공연을 구경하기 좋아요."
    },
    {
        "rank": 6,
        "name": "동대문디자인플라자",
        "english": "DDP",
        "lat": 37.5671,
        "lon": 127.0095,
        "category": "건축 · 전시",
        "description": "독특한 곡선형 건축물로 유명하며 전시와 디자인 행사를 즐길 수 있어요.",
        "tip": "방문 전 전시 일정을 확인해 보세요."
    },
    {
        "rank": 7,
        "name": "경복궁",
        "english": "Gyeongbokgung Palace",
        "lat": 37.5796,
        "lon": 126.9770,
        "category": "역사 · 전통문화",
        "description": "조선 시대의 대표 궁궐로 한국 전통 건축의 아름다움을 느낄 수 있어요.",
        "tip": "휴궁일과 관람 시간을 미리 확인하세요."
    },
    {
        "rank": 8,
        "name": "북촌한옥마을",
        "english": "Bukchon Hanok Village",
        "lat": 37.5826,
        "lon": 126.9830,
        "category": "전통 · 산책",
        "description": "전통 한옥이 모여 있는 마을로 서울의 옛 모습을 경험할 수 있어요.",
        "tip": "주민들이 거주하는 곳이므로 조용히 관람해 주세요."
    },
    {
        "rank": 9,
        "name": "광장시장",
        "english": "Gwangjang Market",
        "lat": 37.5700,
        "lon": 126.9997,
        "category": "전통시장 · 음식",
        "description": "빈대떡과 김밥 등 다양한 한국 길거리 음식을 맛볼 수 있어요.",
        "tip": "가게마다 운영 시간이 다를 수 있어요."
    },
    {
        "rank": 10,
        "name": "남대문시장",
        "english": "Namdaemun Market",
        "lat": 37.5592,
        "lon": 126.9777,
        "category": "전통시장 · 쇼핑",
        "description": "의류와 잡화, 기념품, 먹거리를 다양하게 만날 수 있는 전통시장이에요.",
        "tip": "구경할 곳이 많으니 여유 있게 둘러보세요."
    }
]

# 제목
st.title("🗺️ 외국인 관광객이 좋아하는 서울 관광지 TOP 10")
st.write(
    "서울을 방문하는 외국인 관광객에게 추천하는 "
    "대표 관광지 10곳을 지도에서 확인해 보세요!"
)

st.info(
    "📍 지도 위 숫자 마커를 클릭하면 "
    "관광지 이름과 간단한 설명을 확인할 수 있어요."
)

# 서울 지도 생성
m = folium.Map(
    location=[37.555, 126.985],
    zoom_start=12,
    tiles="OpenStreetMap"
)

# 관광지 마커 표시
for place in PLACES:

    popup_html = f"""
    <div style="font-family:sans-serif; width:210px;">
        <h4>{place['rank']}. {place['name']}</h4>
        <p>{place['english']}</p>
        <b>{place['category']}</b>
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
                background:#2563eb;
                color:white;
                border:2px solid white;
                border-radius:50%;
                width:30px;
                height:30px;
                text-align:center;
                line-height:26px;
                font-weight:bold;
                box-shadow:0 1px 5px rgba(0,0,0,.35);
            ">
                {place['rank']}
            </div>
            """,
            icon_size=(30, 30),
            icon_anchor=(15, 15)
        )
    ).add_to(m)

# 지도 화면 출력
st_folium(
    m,
    use_container_width=True,
    height=590,
    returned_objects=[]
)

# 관광지 설명
st.subheader("📍 서울 관광지 TOP 10")

# 2열 배치
cols = st.columns(2)

for i, place in enumerate(PLACES):

    with cols[i % 2]:

        with st.container(border=True):

            st.markdown(
                f"### {place['rank']}. {place['name']}"
            )

            st.caption(
                f"{place['english']} · {place['category']}"
            )

            st.write(place["description"])

            st.caption(
                f"💡 방문 팁: {place['tip']}"
            )

# 출처
st.divider()

st.subheader("📚 자료 및 참고")

st.write(
    "서울시의 외국인 관광객 방문 분석 자료를 참고하여 "
    "주요 관광지 10곳을 선정했습니다."
)

st.markdown(
    "[서울시 공식 관광 관련 자료](https://english.seoul.go.kr/)"
)

st.caption(
    "※ 공식 단일 순위표가 아닌 주요 관광 명소를 "
    "종합한 안내용 목록입니다."
)
