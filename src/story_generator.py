"""Gemini API를 사용한 스토리 생성"""

import json
import re
from datetime import datetime

from google import genai

from src.config import settings
from src.models import Story, StoryHistoryEntry


class GeminiStoryGenerator:
    """Gemini API를 사용하여 요리 영상 스토리를 생성하는 클래스"""

    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")

        self.client = genai.Client(api_key=settings.google_api_key)
        self.model_name = "gemini-2.0-flash"
        self.story_history: list[StoryHistoryEntry] = []

    def load_story_history(self, history: list[dict]) -> None:
        """이전 스토리 히스토리를 로드합니다"""
        self.story_history = [
            StoryHistoryEntry(**entry) if isinstance(entry, dict) else entry for entry in history
        ]

    def get_story_history(self) -> list[StoryHistoryEntry]:
        """스토리 히스토리를 반환합니다"""
        return self.story_history

    def build_prompt(self, episode: int) -> str:
        """프롬프트를 구성합니다"""
        history_context = ""
        if self.story_history:
            recent_episodes = self.story_history[-10:]  # 최근 10개까지 확인

            # 이전에 만든 요리 목록
            previous_dishes = [h.dish for h in self.story_history]
            dishes_list = ", ".join(previous_dishes) if previous_dishes else "없음"

            # 에피소드별 상세 정보
            episode_details = "\n".join(
                f"- 에피소드 {h.episode}: [{h.dish}] {h.title} - {h.summary}"
                for h in recent_episodes
            )

            history_context = f"""

=== 이전 콘텐츠 기록 (DB 조회 결과) ===

지금까지 만든 요리 목록 (중복 금지):
{dishes_list}

최근 에피소드 상세:
{episode_details}

중요: 위 요리들과 중복되지 않는 새로운 요리를 선택하세요!
==================================="""

        return f"""당신은 귀여운 라쿤 캐릭터 "넝심이"의 요리 쇼츠 영상을 위한 스토리를 작성하는 작가입니다.

캐릭터 정보:
- 주인공: {settings.main_character_name} - {settings.main_character_description}
- 조연: {settings.supporting_character_name} - {settings.supporting_character_description}

요구사항:
1. 요리 영상이 메인 콘텐츠입니다
2. 간단하고 귀여운 스토리가 요리 과정과 자연스럽게 연결됩니다
3. 캐릭터들은 일관성 있게 유지됩니다
4. 쇼츠 영상(60초 이내)에 적합한 분량입니다
5. 시청자들이 즐겁게 볼 수 있는 가벼운 톤입니다

{history_context}

에피소드 {episode}를 위한 스토리를 생성해주세요. 다음 JSON 형식으로 응답해주세요:

{{
  "title": "영상 제목",
  "dish": "만들 요리 이름",
  "summary": "스토리 요약 (1-2문장)",
  "story": "상세 스토리 설명",
  "cooking_steps": ["요리 단계 1", "요리 단계 2", "요리 단계 3"],
  "video_prompts": [
    "영상 프롬프트 1 (Veo3용)",
    "영상 프롬프트 2 (Veo3용)",
    "영상 프롬프트 3 (Veo3용)"
  ],
  "tags": ["태그1", "태그2", "태그3"],
  "description": "YouTube 설명란용 텍스트"
}}

스토리는 요리 과정과 자연스럽게 연결되어야 하며, {settings.main_character_name}와 {settings.supporting_character_name}의 캐릭터가 일관되게 유지되어야 합니다."""

    def parse_story_response(self, text: str, episode: int) -> Story:
        """응답을 파싱합니다"""
        try:
            # JSON 부분만 추출
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                story_data = json.loads(json_match.group(0))
                return Story(**story_data, episode=episode, date=datetime.now().isoformat())
        except (json.JSONDecodeError, Exception) as e:
            print(f"응답 파싱 오류: {e}")

        # 기본값 반환
        return Story(
            title=f"넝심이의 요리 - 에피소드 {episode}",
            dish="특별한 요리",
            summary="넝심이가 요리를 만드는 귀여운 영상",
            story=text[:500] if text else "넝심이가 요리를 만드는 스토리",
            cooking_steps=["준비", "요리", "완성"],
            video_prompts=[
                f"{settings.main_character_name}가 요리를 준비하는 모습",
                f"{settings.main_character_name}가 요리하는 모습",
                f"{settings.main_character_name}가 완성된 요리를 보여주는 모습",
            ],
            tags=["요리", "라쿤", "쇼츠"],
            description=text[:500] if text else "넝심이의 요리 영상",
            episode=episode,
            date=datetime.now().isoformat(),
        )

    async def generate_story(self, episode_number: int | None = None) -> Story:
        """새로운 요리 영상 스토리를 생성합니다"""
        episode = episode_number or len(self.story_history) + 1
        prompt = self.build_prompt(episode)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            text = response.text

            story = self.parse_story_response(text, episode)

            # 히스토리에 추가
            history_entry = StoryHistoryEntry(
                episode=story.episode,
                date=story.date or datetime.now().isoformat(),
                title=story.title,
                dish=story.dish,
                summary=story.summary,
                story=story.story,
                cooking_steps=story.cooking_steps,
                video_prompts=story.video_prompts,
                tags=story.tags,
                description=story.description,
            )
            self.story_history.append(history_entry)

            return story
        except Exception as error:
            print(f"스토리 생성 중 오류: {error}")
            raise
