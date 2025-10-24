import os
import time
import math
import logging
from typing import Dict, List, Optional, Tuple

import google.generativeai as genai
from django.conf import settings
from .models import Character, Conversation, Message, UserCredit

logger = logging.getLogger(__name__)


def _get_env(name: str, default: Optional[str] = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise ValueError(f"환경변수 {name}가 설정되지 않았습니다.")
    return val


class GeminiChatService:
    """
    Gemini 기반 캐릭터 대화 서비스 (Prod-ready)
    - 모델명은 환경변수 GEMINI_MODEL 로 고정 (예: 'models/gemini-2.5-flash')
    - 재시도/백오프
    - 지연 초기화
    """

    _initialised = False

    def __init__(self):
        # 지연 초기화를 위해 여기서는 플래그만
        self.model_name: Optional[str] = None
        self.credit_cost = 1

        self.generation_config = {
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        self.safety_settings = self._build_safety_settings()

    def _lazy_init(self):
        if self._initialised:
            return
        api_key = _get_env("GEMINI_API_KEY")
        genai.configure(api_key=api_key)

        # ✅ 프로덕션: 모델명 고정 (필수)
        # 예: export GEMINI_MODEL="models/gemini-2.5-flash"
        self.model_name = _get_env("GEMINI_MODEL", "models/gemini-2.0-flash")

        self.__class__._initialised = True
        logger.info("GeminiChatService 초기화 완료 | model=%s", self.model_name)

    def _build_safety_settings(self):
        try:
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            return [
                {"category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                 "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                 "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                 "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                 "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
            ]
        except Exception:
            return [
                {"category": "HARM_CATEGORY_HARASSMENT",
                 "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH",
                 "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                 "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                 "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]

    # -----------------------------
    # 백오프 재시도 유틸
    # -----------------------------
    def _retry_generate(self, model, user_message: str, max_attempts: int = 3) -> str:
        """
        간단한 지수 백오프 재시도.
        - 429/5xx/일시 예외에서만 재시도.
        """
        attempt = 0
        last_err = None
        while attempt < max_attempts:
            attempt += 1
            t0 = time.time()
            try:
                resp = model.generate_content(user_message)
                text = (getattr(resp, "text", None) or "").strip()
                if text:
                    # 관측성: 시도 횟수와 지연시간 기록
                    logger.info(
                        "Gemini gen ok | attempt=%d latency=%.2fs",
                        attempt, time.time() - t0
                    )
                    return text
                raise RuntimeError("empty_response")
            except Exception as e:
                last_err = e
                emsg = str(e).lower()
                retriable = any(x in emsg for x in [
                    "429", "rate", "quota", "timeout", "temporar", "unavailable", "5"
                ])
                logger.warning(
                    "Gemini gen fail | attempt=%d retriable=%s err=%s",
                    attempt, retriable, e
                )
                if not retriable or attempt >= max_attempts:
                    break
                # 지수 백오프 (최대 2s 정도)
                sleep_s = min(2.0, 0.2 * (2 ** (attempt - 1)))
                time.sleep(sleep_s)
        # 최종 실패
        raise last_err or RuntimeError("generation_failed")

    # -----------------------------
    # 프롬프트
    # -----------------------------
    def build_character_prompt(
        self, character: Character, conversation_history: Optional[List[Dict]] = None
    ) -> str:
        prompt = f"""당신은 '{character.name}'이라는 캐릭터입니다.

캐릭터 설정:
- 이름: {character.name}
- 장르: {getattr(character.genre, 'name', '미지정')}
- 성격: {character.personality}
- 배경 이야기: {character.background_story}
- 말투/대화 스타일: {character.speaking_style}

중요한 지침:
1. 항상 {character.name}의 설정된 성격과 말투를 유지하세요.
2. 한국어로 자연스럽게 대화하세요.
3. {getattr(character.genre, 'name', '미지정')} 장르에 맞는 분위기를 유지하세요.
4. 사용자의 감정을 이해하고 공감하며 대화하세요.
5. 부적절한 내용이나 개인정보를 요구하지 마세요.
6. 답변은 2-4문장으로 간결하게 해주세요.
"""
        if conversation_history:
            prompt += "\n최근 대화:\n"
            for msg in conversation_history[-3:]:
                sender = "사용자" if msg["sender"] == "user" else character.name
                prompt += f"{sender}: {msg['content']}\n"
        return prompt

    # -----------------------------
    # 생성 호출
    # -----------------------------
    def generate_response(
        self, conversation: Conversation, user_message: str
    ) -> Tuple[str, Dict]:
        self._lazy_init()

        try:
            # 크레딧 확인
            user_credit, _ = UserCredit.objects.get_or_create(user=conversation.user)
            if user_credit.total_credits < self.credit_cost:
                return ("크레딧이 부족합니다. 관리자에게 문의하세요.",
                        {"error": "insufficient_credits", "credits_needed": self.credit_cost})

            # 최근 메시지 정리
            recent_qs = conversation.messages.order_by("-timestamp")[:6]
            history = [{"sender": m.sender, "content": m.content}
                       for m in reversed(list(recent_qs))]

            system_prompt = self.build_character_prompt(conversation.character, history)

            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
                system_instruction=system_prompt,
            )

            t0 = time.time()
            text = self._retry_generate(model, user_message, max_attempts=3)
            latency = time.time() - t0

            # 크레딧 차감(실패해도 응답은 반환)
            try:
                user_credit.use_credits(self.credit_cost)
            except Exception as ce:
                logger.error("크레딧 차감 실패: %s", ce)

            meta = {
                "ai_model_used": self.model_name,
                "generation_time": round(latency, 2),
                "credits_used": self.credit_cost,
            }
            return text, meta

        except Exception as e:
            # 사용자 메시지는 일반화, 내부는 상세 로깅
            logger.error(
                "Gemini API 오류 | model=%s | err=%s",
                self.model_name, e, exc_info=True
            )
            return ("죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                    {"error": "api_error", "error_message": str(e)})

    # -----------------------------
    # 입력 검증
    # -----------------------------
    def validate_user_message(self, message: str) -> Tuple[bool, str]:
        if len(message.strip()) == 0:
            return False, "메시지를 입력해주세요."
        if len(message) > 1000:
            return False, "메시지가 너무 깁니다. 1000자 이내로 입력해주세요."
        return True, ""


# 지연 초기화 전략: import 시점에 생성하지 않음
# 필요하다면 Django AppConfig.ready() 등에서 한 번 touch하는 방식으로 warm-up 가능
gemini_service: Optional[GeminiChatService] = GeminiChatService()
