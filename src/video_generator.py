"""Google Veo3 API를 사용한 영상 생성"""

import asyncio
import time

from google import genai
from google.genai import types

from src.config import settings
from src.models import VideoGenerationResult


class Veo3VideoGenerator:
    """Google genai 라이브러리를 사용하여 Veo3 영상을 생성하는 클래스"""

    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")

        self.client = genai.Client(api_key=settings.google_api_key)
        self.output_dir = settings.output_dir
        self.character_image = self._load_character_image()

    def _load_character_image(self) -> types.Image | None:
        """캐릭터 참조 이미지를 로드합니다"""
        character_path = settings.character_image_path
        if character_path and character_path.exists():
            print(f"캐릭터 참조 이미지 로드: {character_path}")
            return types.Image.from_file(str(character_path))
        print("캐릭터 참조 이미지가 없습니다. character/ 디렉토리에 이미지를 추가하세요.")
        return None

    async def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        style: str = "cute, animated, raccoon cooking",
        negative_prompt: str = "realistic, human, scary",
    ) -> VideoGenerationResult:
        """Veo3 API를 사용하여 영상을 생성합니다"""
        full_prompt = (
            f"{prompt}, {style}, high quality, cute raccoon character, "
            f"cooking video, shorts format, {aspect_ratio} aspect ratio, "
            f"no dialogue, no speech, no narration, sound effects only, ambient cooking sounds, "
            f"avoid: {negative_prompt}"
        )

        try:
            # 동기 API를 비동기로 실행
            generate_kwargs = {
                "model": "veo-3.1-fast-generate-preview",
                "prompt": full_prompt,
                "config": types.GenerateVideosConfig(
                    number_of_videos=1,
                    duration_seconds=duration,
                    enhance_prompt=True,
                ),
            }

            # 캐릭터 참조 이미지가 있으면 추가
            if self.character_image:
                generate_kwargs["image"] = self.character_image

            operation = await asyncio.to_thread(
                self.client.models.generate_videos,
                **generate_kwargs,
            )

            # 작업 완료 대기
            while not operation.done:
                print("영상 생성 중...")
                await asyncio.sleep(10)
                operation = await asyncio.to_thread(self.client.operations.get, operation)

            # 영상 다운로드
            if operation.response and operation.response.generated_videos:
                video = operation.response.generated_videos[0]
                await asyncio.to_thread(self.client.files.download, file=video.video)

                filename = f"veo3_{int(time.time())}.mp4"
                filepath = self.output_dir / filename
                await asyncio.to_thread(video.video.save, str(filepath))

                return VideoGenerationResult(video_url=str(filepath), status="completed")

            raise ValueError("영상 생성 결과가 없습니다")

        except Exception as error:
            print(f"Veo3 영상 생성 오류: {error}")
            # API가 아직 공개되지 않았을 경우를 대비한 모의 응답
            return await self._generate_mock_video(prompt)

    async def _generate_mock_video(self, prompt: str) -> VideoGenerationResult:
        """모의 영상 생성 (API가 사용 불가능할 때)"""
        print(f"[모의] 영상 생성: {prompt}")
        filename = f"mock_video_{int(time.time())}.mp4"
        filepath = self.output_dir / filename

        return VideoGenerationResult(video_url=str(filepath), status="completed", mock=True)

    async def generate_video_sequence(
        self, prompts: list[str], duration: int = 5, output_filename: str | None = None
    ) -> str:
        """여러 프롬프트로 영상을 생성하고 합칩니다"""
        videos: list[str] = []

        for i, prompt in enumerate(prompts):
            print(f"영상 {i + 1}/{len(prompts)} 생성 중...")

            result = await self.generate_video(prompt, duration=duration)

            if result.video_url and result.status == "completed":
                videos.append(result.video_url)

        # 영상 합치기
        if len(videos) > 1:
            return await self.merge_videos(videos, output_filename)

        return videos[0] if videos else ""

    async def merge_videos(self, video_paths: list[str], output_filename: str | None = None) -> str:
        """여러 영상을 하나로 합칩니다 (ffmpeg 사용)"""
        import subprocess

        output_filename = output_filename or f"final_video_{int(time.time())}.mp4"
        output_path = self.output_dir / output_filename

        # ffmpeg를 사용하여 영상 합치기
        file_list_path = self.output_dir / "filelist.txt"
        file_list_content = "\n".join(f"file '{path}'" for path in video_paths)
        file_list_path.write_text(file_list_content)

        try:
            cmd = [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(file_list_path),
                "-c",
                "copy",
                str(output_path),
            ]

            await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, check=True)

            # 임시 파일 정리
            file_list_path.unlink()

            return str(output_path)
        except subprocess.CalledProcessError as error:
            print(f"영상 합치기 오류: {error}")
            print(f"stderr: {error.stderr}")
            raise
