import json
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="GameMatch API",
    description="게임 취향 기반 추천 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GAMES_PATH = Path(__file__).parent / "data" / "games.json"


class RecommendRequest(BaseModel):
    genre: str = Field(..., description="선호 장르")
    platform: str = Field(..., description="플레이 플랫폼")
    play_style: Literal["솔로", "멀티", "협동"] = Field(..., description="플레이 스타일")
    session_time: Literal["짧은 플레이", "중간 플레이", "긴 플레이"] = Field(
        ..., description="1회 플레이 시간"
    )
    difficulty: Literal["쉬움", "보통", "어려움"] = Field(..., description="선호 난이도")
    multiplayer: Literal["없음", "선택적", "필수"] = Field(..., description="멀티플레이 선호")
    mood: Literal["힐링", "경쟁", "모험", "창작"] = Field(..., description="원하는 분위기")
    focus: Literal["스토리", "게임플레이"] = Field(..., description="중시 요소")


class GameRecommendation(BaseModel):
    title: str
    genre: str
    description: str
    tags: list[str]
    match_score: int
    match_percent: float
    reasons: list[str]
    platform: list[str]


class RecommendResponse(BaseModel):
    user_profile: str
    total_candidates: int
    recommendations: list[GameRecommendation]
    play_tip: str


def load_games() -> list[dict]:
    with open(GAMES_PATH, encoding="utf-8") as f:
        return json.load(f)


def score_game(game: dict, req: RecommendRequest) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    if game["genre"] == req.genre:
        score += 25
        reasons.append(f"선호 장르 '{req.genre}'와 일치")
    elif req.genre in game.get("tags", []):
        score += 12
        reasons.append(f"태그에 '{req.genre}' 관련 요소 포함")

    if req.platform in game["platform"]:
        score += 20
        reasons.append(f"'{req.platform}'에서 플레이 가능")
    elif "PC" in game["platform"] and req.platform != "모바일":
        score += 5

    if game["play_style"] == req.play_style:
        score += 15
        reasons.append(f"'{req.play_style}' 플레이에 적합")
    elif req.play_style == "협동" and game["play_style"] == "멀티":
        score += 8
        reasons.append("멀티플레이로 협동 플레이 가능")

    if game["session_time"] == req.session_time:
        score += 12
        reasons.append(f"'{req.session_time}' 세션에 맞는 플레이 시간")
    elif _session_compatible(game["session_time"], req.session_time):
        score += 6
        reasons.append("플레이 시간이 비슷한 편")

    if game["difficulty"] == req.difficulty:
        score += 10
        reasons.append(f"선호 난이도 '{req.difficulty}'와 일치")
    elif _difficulty_compatible(game["difficulty"], req.difficulty):
        score += 4

    if game["multiplayer"] == req.multiplayer:
        score += 10
        reasons.append(f"멀티플레이 선호도 '{req.multiplayer}'와 일치")
    elif req.multiplayer == "선택적":
        score += 5

    if game["mood"] == req.mood:
        score += 12
        reasons.append(f"'{req.mood}' 분위기를 잘 표현")
    elif _mood_compatible(game["mood"], req.mood):
        score += 5

    if game["focus"] == req.focus:
        score += 10
        reasons.append(f"'{req.focus}' 중심의 게임 경험 제공")

    return score, reasons


def _session_compatible(game_session: str, user_session: str) -> bool:
    order = ["짧은 플레이", "중간 플레이", "긴 플레이"]
    g_idx = order.index(game_session)
    u_idx = order.index(user_session)
    return abs(g_idx - u_idx) == 1


def _difficulty_compatible(game_diff: str, user_diff: str) -> bool:
    order = ["쉬움", "보통", "어려움"]
    g_idx = order.index(game_diff)
    u_idx = order.index(user_diff)
    return abs(g_idx - u_idx) == 1


def _mood_compatible(game_mood: str, user_mood: str) -> bool:
    pairs = {("모험", "창작"), ("경쟁", "모험"), ("힐링", "창작")}
    return (game_mood, user_mood) in pairs or (user_mood, game_mood) in pairs


def build_user_profile(req: RecommendRequest) -> str:
    return (
        f"{req.platform}에서 {req.session_time} 동안 "
        f"{req.play_style}로 즐길 수 있는 {req.genre} 게임을 찾는 "
        f"{req.mood} 분위기 · {req.focus} 중심 플레이어"
    )


def build_play_tip(req: RecommendRequest, top_game: dict | None) -> str:
    if not top_game:
        return "조건을 조금 완화하면 더 많은 게임을 찾을 수 있어요!"

    tips = {
        "솔로": "혼자 몰입할 때는 헤드폰을 끼고 조명을 어둡게 하면 더 좋아요.",
        "멀티": "디스코드로 친구들과 소통하면 승률과 재미가 올라갑니다.",
        "협동": "파티원과 역할을 나누면 보스전이 훨씬 수월해집니다.",
    }
    base = tips.get(req.play_style, "즐겁게 플레이하세요!")
    return f"'{top_game['title']}' 추천! {base}"


@app.get("/")
def root():
    return {
        "service": "GameMatch API",
        "status": "running",
        "endpoints": ["/health", "/recommend", "/games"],
    }


@app.get("/health")
def health():
    return {"status": "healthy", "games_loaded": len(load_games())}


@app.get("/games")
def list_games():
    return {"count": len(load_games()), "games": [g["title"] for g in load_games()]}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    games = load_games()
    scored: list[tuple[dict, int, list[str]]] = []

    for game in games:
        score, reasons = score_game(game, req)
        if score > 0:
            scored.append((game, score, reasons))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:5]

    max_score = 120
    recommendations = [
        GameRecommendation(
            title=game["title"],
            genre=game["genre"],
            description=game["description"],
            tags=game["tags"],
            match_score=score,
            match_percent=round(min(score / max_score * 100, 100), 1),
            reasons=reasons[:4],
            platform=game["platform"],
        )
        for game, score, reasons in top
    ]

    if not recommendations:
        fallback = games[:3]
        recommendations = [
            GameRecommendation(
                title=game["title"],
                genre=game["genre"],
                description=game["description"],
                tags=game["tags"],
                match_score=30,
                match_percent=25.0,
                reasons=["조건에 완벽히 맞지 않지만 인기 있는 추천 게임"],
                platform=game["platform"],
            )
            for game in fallback
        ]

    top_game = top[0][0] if top else None

    return RecommendResponse(
        user_profile=build_user_profile(req),
        total_candidates=len(scored),
        recommendations=recommendations,
        play_tip=build_play_tip(req, top_game),
    )
