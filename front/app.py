import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

GENRES = [
    "액션 RPG", "시뮬레이션", "FPS", "메트로바니아", "MOBA",
    "플랫포머", "샌드박스", "JRPG", "어드벤처", "로그라이크",
    "RPG", "퍼즐", "파티",
]

PLATFORMS = ["PC", "PlayStation", "Xbox", "Nintendo Switch", "모바일"]

st.set_page_config(
    page_title="GameMatch - 게임 추천",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #6C63FF, #FF6584);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #888;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .match-badge {
        background: linear-gradient(90deg, #6C63FF, #FF6584);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .tag {
        background: #2a2a4a;
        color: #a0a0ff;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-right: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-header">🎮 GameMatch</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">당신의 게임 취향을 분석해 딱 맞는 게임을 추천해 드립니다</p>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("🎯 게임 취향 입력")
    st.markdown("---")

    genre = st.selectbox("선호 장르", GENRES, index=0)
    platform = st.selectbox("플레이 플랫폼", PLATFORMS, index=0)
    play_style = st.radio("플레이 스타일", ["솔로", "멀티", "협동"], horizontal=True)
    session_time = st.select_slider(
        "1회 플레이 시간",
        options=["짧은 플레이", "중간 플레이", "긴 플레이"],
        value="중간 플레이",
    )
    difficulty = st.select_slider(
        "선호 난이도",
        options=["쉬움", "보통", "어려움"],
        value="보통",
    )
    multiplayer = st.selectbox(
        "멀티플레이",
        ["없음", "선택적", "필수"],
        index=1,
    )
    mood = st.radio(
        "원하는 분위기",
        ["힐링", "경쟁", "모험", "창작"],
        horizontal=True,
    )
    focus = st.radio(
        "중시하는 요소",
        ["스토리", "게임플레이"],
        horizontal=True,
    )

    st.markdown("---")
    recommend_btn = st.button("🚀 게임 추천 받기", use_container_width=True, type="primary")

status_col = st.columns([1])[0]
with status_col:
    try:
        health = requests.get(f"{API_URL}/health", timeout=3)
        if health.status_code == 200:
            data = health.json()
            st.success(f"API 연결됨 ({data['games_loaded']}개 게임)")
        else:
            st.error("API 오류")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        st.error("API 연결 실패")

if recommend_btn:
    payload = {
        "genre": genre,
        "platform": platform,
        "play_style": play_style,
        "session_time": session_time,
        "difficulty": difficulty,
        "multiplayer": multiplayer,
        "mood": mood,
        "focus": focus,
    }

    with st.spinner("FastAPI에서 게임을 분석 중..."):
        try:
            response = requests.post(
                f"{API_URL}/recommend",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.ConnectionError:
            st.error(
                f"FastAPI 서버에 연결할 수 없습니다. (`{API_URL}`)\n\n"
                "Docker 컨테이너가 실행 중인지 확인해 주세요."
            )
            st.stop()
        except requests.exceptions.Timeout:
            st.error("서버 응답 시간이 초과되었습니다.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"API 오류: {e}")
            st.stop()

    st.markdown("---")
    st.subheader("📊 분석 결과")
    st.info(result["user_profile"])

    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    metrics_col1.metric("추천 게임 수", len(result["recommendations"]))
    metrics_col2.metric("매칭 후보", result["total_candidates"])
    if result["recommendations"]:
        metrics_col3.metric(
            "최고 매칭률",
            f"{result['recommendations'][0]['match_percent']}%",
        )

    st.success(f"💡 {result['play_tip']}")

    st.markdown("---")
    st.subheader("🏆 추천 게임 TOP 5")

    for i, game in enumerate(result["recommendations"], 1):
        rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i - 1]
        header_col, score_col = st.columns([4, 1])
        with header_col:
            st.markdown(f"### {rank_emoji} {game['title']}")
            st.caption(f"{game['genre']} · {', '.join(game['platform'])}")
        with score_col:
            st.markdown(
                f'<div style="text-align:right; margin-top:10px;">'
                f'<span class="match-badge">{game["match_percent"]}% 매칭</span></div>',
                unsafe_allow_html=True,
            )

        st.write(game["description"])

        tag_html = " ".join(
            f'<span class="tag">#{tag}</span>' for tag in game["tags"]
        )
        st.markdown(tag_html, unsafe_allow_html=True)

        with st.expander("왜 추천했나요?"):
            for reason in game["reasons"]:
                st.markdown(f"- ✅ {reason}")

        st.markdown("---")

    with st.expander("🔍 API 응답 (JSON)"):
        st.json(result)

else:
    st.markdown("### 👈 왼쪽 사이드바에서 취향을 입력하고 추천 버튼을 눌러주세요!")
    st.markdown(
        """
        **GameMatch**는 8가지 취향 요소를 분석해 최적의 게임을 추천합니다.

        | 입력 항목 | 설명 |
        |-----------|------|
        | 장르 | 선호하는 게임 장르 |
        | 플랫폼 | 사용 가능한 기기 |
        | 플레이 스타일 | 솔로 / 멀티 / 협동 |
        | 플레이 시간 | 한 번에 플레이하는 시간 |
        | 난이도 | 선호하는 게임 난이도 |
        | 멀티플레이 | 멀티 필요 여부 |
        | 분위기 | 힐링 / 경쟁 / 모험 / 창작 |
        | 중시 요소 | 스토리 vs 게임플레이 |
        """
    )
