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
    page_title="픽업존",
    page_icon="▣",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; max-width: 640px; }
    .stApp { background-color: #ece6d9; }
    .pickup-title {
        font-family: "Courier New", Courier, monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #1c1c1c;
        letter-spacing: -1px;
        margin: 0;
    }
    .pickup-sub {
        font-family: "Courier New", Courier, monospace;
        font-size: 0.85rem;
        color: #5c5346;
        margin-top: 0.3rem;
        margin-bottom: 1.6rem;
    }
    .pickup-box {
        border: 2px solid #1c1c1c;
        background: #faf7f0;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }
    .pickup-label {
        font-family: "Courier New", Courier, monospace;
        font-size: 0.7rem;
        color: #7a6f5d;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.8rem;
    }
    .pickup-result {
        border: 2px solid #1c1c1c;
        border-left: 6px solid #c84b31;
        background: #faf7f0;
        padding: 0.9rem 1rem;
        margin-bottom: 0.7rem;
    }
    .pickup-rank {
        font-family: "Courier New", Courier, monospace;
        font-size: 0.75rem;
        color: #c84b31;
        font-weight: 700;
    }
    .pickup-game {
        font-family: "Courier New", Courier, monospace;
        font-size: 1.05rem;
        font-weight: 700;
        color: #1c1c1c;
        margin: 0.15rem 0;
    }
    .pickup-meta {
        font-size: 0.8rem;
        color: #5c5346;
    }
    .pickup-desc {
        font-size: 0.85rem;
        color: #3a342c;
        margin: 0.4rem 0 0.3rem;
        line-height: 1.5;
    }
    .pickup-reason {
        font-size: 0.78rem;
        color: #5c5346;
        margin: 0;
        padding-left: 0.6rem;
        border-left: 2px solid #d4cbb8;
    }
    .pickup-status {
        font-family: "Courier New", Courier, monospace;
        font-size: 0.72rem;
        color: #7a6f5d;
        text-align: right;
        margin-bottom: 0.5rem;
    }
    .pickup-status-ok { color: #3d6b4f; }
    .pickup-status-err { color: #c84b31; }
    div[data-testid="stHorizontalBlock"] label p { font-size: 0.85rem; }
  </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="pickup-title">게임 추천 픽업 존에 온 걸 환영해요.</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="pickup-sub">오늘 밤 뭐 할지 모르겠으면, 조건만 넣고 골라보세요.</p>',
    unsafe_allow_html=True,
)

api_ok = False
game_count = 0
try:
    health = requests.get(f"{API_URL}/health", timeout=3)
    if health.status_code == 200:
        api_ok = True
        game_count = health.json().get("games_loaded", 0)
except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
    pass

status_class = "pickup-status-ok" if api_ok else "pickup-status-err"
status_text = f"api · online · {game_count} titles" if api_ok else "api · offline"
st.markdown(
    f'<p class="pickup-status {status_class}">{status_text}</p>',
    unsafe_allow_html=True,
)

st.markdown('<div class="pickup-box"><p class="pickup-label">01 / 기본</p>', unsafe_allow_html=True)
left, right = st.columns(2)
with left:
    genre = st.selectbox("장르", GENRES)
    platform = st.selectbox("플랫폼", PLATFORMS)
    play_style = st.selectbox("혼자 / 같이", ["솔로", "멀티", "협동"])
with right:
    session_time = st.selectbox("한 판 길이", ["짧은 플레이", "중간 플레이", "긴 플레이"])
    difficulty = st.selectbox("난이도", ["쉬움", "보통", "어려움"])
    multiplayer = st.selectbox("멀티 필요?", ["없음", "선택적", "필수"])
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="pickup-box"><p class="pickup-label">02 / 분위기</p>', unsafe_allow_html=True)
mood_col, focus_col = st.columns(2)
with mood_col:
    mood = st.radio("무드", ["힐링", "경쟁", "모험", "창작"], label_visibility="collapsed")
with focus_col:
    focus = st.radio("뭐가 더 중요?", ["스토리", "게임플레이"], label_visibility="collapsed")
st.markdown("</div>", unsafe_allow_html=True)

recommend_btn = st.button("추천 받기", use_container_width=True)

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

    with st.spinner("서버에서 골라는 중..."):
        try:
            response = requests.post(f"{API_URL}/recommend", json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.ConnectionError:
            st.error(f"백엔드에 연결 안 됨. ({API_URL}) docker ps 로 확인해보세요.")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("응답이 너무 느립니다.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"요청 실패: {e}")
            st.stop()

    st.markdown("---")
    st.markdown(
        f'<p class="pickup-sub" style="margin-bottom:1rem;">{result["user_profile"]}</p>',
        unsafe_allow_html=True,
    )
    st.caption(f"후보 {result['total_candidates']}개 중 상위 {len(result['recommendations'])}개")
    st.caption(result["play_tip"])

    for i, game in enumerate(result["recommendations"], 1):
        reasons = " / ".join(game["reasons"][:2])
        tags = ", ".join(game["tags"])
        st.markdown(
            f"""
            <div class="pickup-result">
                <p class="pickup-rank">NO.{i} · {game['match_percent']}%</p>
                <p class="pickup-game">{game['title']}</p>
                <p class="pickup-meta">{game['genre']} · {', '.join(game['platform'])}</p>
                <p class="pickup-desc">{game['description']}</p>
                <p class="pickup-meta">{tags}</p>
                <p class="pickup-reason">{reasons}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("응답 원본 (json)"):
        st.json(result)

else:
    st.markdown(
        """
        <div class="pickup-box" style="text-align:center; padding:2rem;">
            <p class="pickup-meta" style="margin:0;">
                위에서 조건 고르고<br>추천 받기 누르면 됩니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
