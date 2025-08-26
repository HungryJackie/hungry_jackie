
import os
import time
import logging
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from django.conf import settings
from .models import Character, Conversation, Message, UserCredit

# 로거 설정
logger = logging.getLogger(__name__)

class GeminiChatService:
    """Gemini API를 사용한 캐릭터 대화 서비스 (간소화 버전)"""
    
    def __init__(self):
        """API 키 설정 및 모델 초기화"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        
        genai.configure(api_key=api_key)
        
        # 개발용으로 하나의 모델만 사용
        self.model_name = 'gemini-1.5-flash'
        self.credit_cost = 1  # 개발용으로 낮은 비용
        
        # 생성 설정
        self.generation_config = {
            'temperature': 0.9,
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 800,
        }
        
        # 안전 설정
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", 
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    
    def build_character_prompt(self, character: Character, conversation_history: List[Dict] = None) -> str:
        """캐릭터 설정을 기반으로 시스템 프롬프트 생성"""
        
        prompt = f"""당신은 '{character.name}'이라는 캐릭터입니다.

캐릭터 설정:
- 이름: {character.name}
- 장르: {character.genre.name}
- 성격: {character.personality}
- 배경 이야기: {character.background_story}
- 말투/대화 스타일: {character.speaking_style}

중요한 지침:
1. 항상 {character.name}의 설정된 성격과 말투를 유지하세요.
2. 한국어로 자연스럽게 대화하세요.
3. {character.genre.name} 장르에 맞는 분위기를 유지하세요.
4. 사용자의 감정을 이해하고 공감하며 대화하세요.
5. 부적절한 내용이나 개인정보를 요구하지 마세요.
6. 답변은 2-4문장으로 간결하게 해주세요.

"""
        
        # 대화 기록이 있으면 추가
        if conversation_history:
            prompt += "\n최근 대화:\n"
            for msg in conversation_history[-3:]:  # 최근 3개 메시지만
                sender = "사용자" if msg['sender'] == 'user' else character.name
                prompt += f"{sender}: {msg['content']}\n"
        
        return prompt
    
    def generate_response(
        self, 
        conversation: Conversation, 
        user_message: str
    ) -> Tuple[str, Dict]:
        """
        캐릭터 응답 생성 (동기 버전)
        
        Args:
            conversation: 대화 객체
            user_message: 사용자 메시지
            
        Returns:
            (응답 메시지, 메타데이터)
        """
        
        try:
            user_credit, _ = UserCredit.objects.get_or_create(user=conversation.user)
            
            # 크레딧 확인 및 차감
            if user_credit.total_credits < self.credit_cost:
                return "크레딧이 부족합니다. 관리자에게 문의하세요.", {
                    'error': 'insufficient_credits',
                    'credits_needed': self.credit_cost
                }
            
            # 대화 기록 가져오기
            recent_messages = list(conversation.messages.order_by('-timestamp')[:6])
            conversation_history = [
                {
                    'sender': msg.sender,
                    'content': msg.content
                }
                for msg in reversed(recent_messages)
            ]
            
            # 프롬프트 생성
            system_prompt = self.build_character_prompt(
                conversation.character, 
                conversation_history
            )
            
            # 모델 선택 및 생성
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
                system_instruction=system_prompt
            )
            
            # 시간 측정 시작
            start_time = time.time()
            
            # 응답 생성 (동기 방식)
            response = model.generate_content(user_message)
            
            # 생성 시간 계산
            generation_time = time.time() - start_time
            
            # 응답 검증
            if not response.text:
                return "죄송합니다. 응답을 생성할 수 없습니다. 다시 시도해주세요.", {
                    'error': 'no_response_generated'
                }
            
            # 크레딧 차감
            user_credit.use_credits(self.credit_cost)
            
            # 메타데이터 구성
            metadata = {
                'ai_model_used': self.model_name,
                'generation_time': round(generation_time, 2),
                'credits_used': self.credit_cost,
            }
            
            return response.text.strip(), metadata
            
        except Exception as e:
            logger.error(f"Gemini API 오류: {str(e)}")
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", {
                'error': 'api_error',
                'error_message': str(e)
            }
    
    def validate_user_message(self, message: str) -> Tuple[bool, str]:
        """사용자 메시지 검증"""
        
        # 길이 검증
        if len(message.strip()) == 0:
            return False, "메시지를 입력해주세요."
        
        if len(message) > 1000:
            return False, "메시지가 너무 깁니다. 1000자 이내로 입력해주세요."
        
        return True, ""


# 서비스 인스턴스 생성
gemini_service = GeminiChatService()
