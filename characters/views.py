from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, F, Case, When, FloatField
import json

from .models import Character, Conversation, Message, UserCredit
from .forms import CharacterCreateForm
from .services import gemini_service
from emotions.models import Emotion, Genre, EmotionKeyword

def generate_character_guide(emotion, genre):
    """감정-장르 조합에 따른 캐릭터 생성 가이드"""
    
    # 감정별 키워드 가져오기
    emotion_keywords = list(EmotionKeyword.objects.filter(
        emotion=emotion
    ).order_by('-weight')[:8])
    
    # 감정-장르 조합별 가이드 데이터
    guide_templates = {
        # 우울해요 조합들
        ('우울해요', '치유물'): {
            'personality_suggestions': [
                '따뜻하고 공감 능력이 뛰어난 성격',
                '상처받은 마음을 이해하고 위로해주는 캐릭터',
                '희망을 잃지 않고 긍정적 에너지를 전달하는 성격',
                '인내심이 많고 끝까지 함께해주는 든든한 캐릭터'
            ],
            'speaking_style_suggestions': [
                '부드럽고 따뜻한 말투, "괜찮아요", "천천히 해도 돼요"',
                '공감하는 표현을 자주 사용, "충분히 이해해요", "당신의 마음 알겠어요"',
                '격려와 위로의 말을 자연스럽게 건네는 말투',
                '존댓말 사용으로 상대방을 존중하는 느낌'
            ],
            'background_suggestions': [
                '상담사나 심리치료사 배경으로 전문성 부여',
                '과거 본인도 어려움을 겪었지만 극복한 경험',
                '도서관이나 카페 등 평온한 공간에서 활동',
                '동물 보호소나 자원봉사 활동으로 따뜻한 마음 표현'
            ]
        },
        
        ('짜증나요', '사이다물'): {
            'personality_suggestions': [
                '정의감이 강하고 불의를 참지 못하는 성격',
                '명확하고 논리적인 사고를 가진 캐릭터',
                '시원시원하고 직설적인 성격',
                '문제 해결 능력이 뛰어난 액션형 캐릭터'
            ],
            'speaking_style_suggestions': [
                '단호하고 확신에 찬 말투, "그건 잘못된 거예요!"',
                '논리적인 설명과 명확한 근거 제시',
                '때로는 날카롭지만 항상 정당한 이유가 있는 말투',
                '반말과 존댓말을 상황에 맞게 적절히 사용'
            ],
            'background_suggestions': [
                '변호사, 기자, 또는 정의를 추구하는 직업',
                '부당한 일을 당한 경험이 있어 더욱 정의감이 강함',
                '법정이나 언론사 등 진실을 다루는 환경',
                '사회 불의와 맞서 싸운 경험이 풍부'
            ]
        },
        
        ('외로워요', '우정물'): {
            'personality_suggestions': [
                '따뜻하고 사교적이며 사람을 좋아하는 성격',
                '진실한 우정을 소중히 여기는 캐릭터',
                '상대방의 이야기를 잘 들어주는 공감형 성격',
                '함께 있으면 편안함을 주는 친근한 캐릭터'
            ],
            'speaking_style_suggestions': [
                '친근하고 편안한 말투, "우리 함께 해요"',
                '공감과 격려의 표현을 자주 사용',
                '상황에 따라 반말과 존댓말을 자연스럽게 사용',
                '유머를 적절히 섞어 분위기를 밝게 만드는 말투'
            ],
            'background_suggestions': [
                '학교나 직장에서 인기 많은 분위기 메이커',
                '동아리나 모임 활동을 즐기는 사교적 배경',
                '카페나 공원 등 사람들이 모이는 곳을 좋아함',
                '과거 좋은 친구들과의 추억이 많은 경험'
            ]
        },
        
        ('자신없어요', '성장물'): {
            'personality_suggestions': [
                '도전을 두려워하지 않는 용기 있는 성격',
                '실패를 딛고 일어서는 강인한 정신력',
                '남을 격려하고 응원하는 것을 좋아하는 캐릭터',
                '꾸준한 노력과 성장을 중시하는 성격'
            ],
            'speaking_style_suggestions': [
                '격려와 응원이 가득한 말투, "할 수 있어요!"',
                '경험을 바탕으로 한 조언과 팁 제공',
                '때로는 엄격하지만 항상 성장을 바라는 마음',
                '자신의 실패담도 솔직하게 공유하는 말투'
            ],
            'background_suggestions': [
                '운동선수나 트레이너로 도전과 성장 경험',
                '창업가나 예술가로 끊임없는 시도와 실패 경험',
                '멘토나 코치 역할로 다른 사람 성장 도움',
                '어려운 환경을 극복한 성공 스토리 보유'
            ]
        },
        
        # 기타 조합들도 유사하게 추가 가능...
    }
    
    # 기본 가이드 템플릿
    default_guide = {
        'personality_suggestions': [
            f'{emotion.description} 감정을 이해하고 공감할 수 있는 성격',
            f'{genre.name} 장르에 어울리는 매력적인 캐릭터',
            '상대방의 마음을 헤아리는 따뜻한 성격',
            '자신만의 독특한 매력을 가진 개성 있는 캐릭터'
        ],
        'speaking_style_suggestions': [
            f'{genre.name} 장르에 어울리는 특색 있는 말투',
            '자연스럽고 편안한 대화 스타일',
            '상황에 맞는 적절한 반응과 표현',
            '개성을 드러내는 특별한 말버릇이나 표현'
        ],
        'background_suggestions': [
            f'{genre.name} 장르의 세계관에 맞는 배경 설정',
            f'{emotion.description} 상황을 이해할 수 있는 경험',
            '흥미로운 과거사나 특별한 경험',
            '캐릭터의 성격을 뒷받침하는 배경 스토리'
        ]
    }
    
    # 조합 키 생성
    combo_key = (emotion.name, genre.name)
    guide_data = guide_templates.get(combo_key, default_guide)
    
    # 키워드 정보 추가
    guide_data['keywords'] = [kw.keyword for kw in emotion_keywords]
    guide_data['emotion_description'] = emotion.description
    guide_data['genre_description'] = genre.description
    
    return guide_data
    
@login_required
def character_create(request):
    """캐릭터 생성 페이지"""
    user_character_count = Character.objects.filter(creator=request.user).count()
    max_characters = 20  # 개발용으로 여유롭게

    if user_character_count >= max_characters:
        messages.error(request, f'캐릭터는 최대 {max_characters}개까지 생성할 수 있습니다.')
        return redirect('characters:my_characters')

    if request.method == 'POST':
        form = CharacterCreateForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            character = form.save(commit=False)
            character.creator = request.user
            character.status = 'active'  # 개발 중 자동 승인
            character.save()
            messages.success(request, '캐릭터가 성공적으로 생성되었습니다!')
            return redirect('characters:character_detail', character_id=character.id)
    else:
        form = CharacterCreateForm(user=request.user)

    return render(request, 'characters/character_create.html', {
        'form': form,
        'mode': 'create',  # 템플릿 재사용 위한 플래그
    })


@login_required
def character_edit(request, character_id):
    """캐릭터 수정 페이지 (create 템플릿 재사용)"""
    character = get_object_or_404(Character, id=character_id, creator=request.user)

    if request.method == 'POST':
        form = CharacterCreateForm(request.POST, request.FILES, instance=character, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '캐릭터가 수정되었습니다.')
            return redirect('characters:character_detail', character_id=character.id)
    else:
        form = CharacterCreateForm(instance=character, user=request.user)

    return render(request, 'characters/character_create.html', {
        'form': form,
        'character': character,
        'mode': 'edit',  # 템플릿 분기
    })


@login_required
def character_delete(request, character_id):
    """캐릭터 삭제 확인 및 처리"""
    character = get_object_or_404(Character, id=character_id, creator=request.user)
    
    if request.method == 'POST':
        character_name = character.name
        character.delete()
        messages.success(request, f'캐릭터 "{character_name}"이(가) 삭제되었습니다.')
        return redirect('characters:my_characters')
    
    # GET 요청시 삭제 확인 페이지 표시
    return render(request, 'characters/character_delete_confirm.html', {
        'character': character,
    })

@login_required
def my_characters(request):
    """내 캐릭터 목록 + 검색/정렬/공개범위 필터"""
    qs = Character.objects.filter(creator=request.user).select_related('genre')

    # 검색
    q = request.GET.get('search', '').strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(tags__icontains=q)
        )

    # 공개범위 필터 (public / private)
    vis = request.GET.get('visibility', '')
    if vis in ('public', 'private'):
        qs = qs.filter(visibility=vis)

    # 정렬 (rating / created / updated)
    sort = request.GET.get('sort', 'created_desc')
    if sort == 'rating_desc':
        qs = qs.order_by('-rating_count', '-rating_sum', '-created_at')
    elif sort == 'rating_asc':
        qs = qs.order_by('rating_count', 'rating_sum', '-created_at')
    elif sort == 'created_asc':
        qs = qs.order_by('created_at')
    elif sort == 'updated_desc':
        qs = qs.order_by('-updated_at')
    elif sort == 'updated_asc':
        qs = qs.order_by('updated_at')
    else:
        # 기본: 생성일 내림차순
        qs = qs.order_by('-created_at')

    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'characters/my_characters.html', {
        'page_obj': page_obj,
        'total_count': qs.count(),
        'search_query': q,
        'visibility_filter': vis,
        'sort': sort,
    })


def character_list(request):
    """공개 캐릭터 목록"""
    characters = Character.objects.filter(
        status='active',
        visibility='public'
    ).select_related('creator', 'genre').annotate(
        conversation_count=Count('conversation')
    ).order_by('-total_conversations', '-created_at')

    # 장르 필터
    genre_id = request.GET.get('genre')
    if genre_id:
        characters = characters.filter(genre_id=genre_id)

    # 검색
    search_query = request.GET.get('search', '').strip()
    if search_query:
        characters = characters.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )

    paginator = Paginator(characters, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'characters/character_list.html', {
        'page_obj': page_obj,
        'genres': Genre.objects.all(),
        'emotions': Emotion.objects.filter(is_active=True),
        'current_genre': genre_id,
        'search_query': search_query,
    })


def character_detail(request, character_id):
    """캐릭터 상세 페이지"""
    character = get_object_or_404(
        Character.objects.select_related('creator', 'genre'),
        id=character_id
    )

    # 사용자의 이전 대화 확인
    user_conversation = None
    if request.user.is_authenticated:
        user_conversation = Conversation.objects.filter(
            user=request.user,
            character=character,
            status='active'
        ).first()

    # 평점 정보
    ratings = character.characterrating_set.select_related('user').order_by('-created_at')[:5]
    user_rating = None
    if request.user.is_authenticated:
        user_rating = character.characterrating_set.filter(user=request.user).first()

    return render(request, 'characters/character_detail.html', {
        'character': character,
        'user_conversation': user_conversation,
        'ratings': ratings,
        'user_rating': user_rating,
    })


@login_required
def start_conversation(request, character_id):
    """캐릭터와 대화 시작"""
    character = get_object_or_404(Character, id=character_id, status='active')

    # 이미 진행 중인 대화가 있는지 확인
    existing_conversation = Conversation.objects.filter(
        user=request.user,
        character=character,
        status='active'
    ).first()

    if existing_conversation:
        return redirect('characters:conversation', conversation_id=existing_conversation.id)

    # 새 대화 생성
    conversation = Conversation.objects.create(
        user=request.user,
        character=character
    )
    return redirect('characters:conversation', conversation_id=conversation.id)


@login_required
def conversation_view(request, conversation_id):
    """대화 페이지"""
    conversation = get_object_or_404(
        Conversation.objects.select_related('character', 'user'),
        id=conversation_id,
        user=request.user
    )

    # 대화 메시지 목록
    chat_messages = conversation.messages.order_by('timestamp')

    # 사용자 크레딧 정보 (없으면 생성)
    user_credit, _ = UserCredit.objects.get_or_create(user=request.user)

    return render(request, 'characters/conversation.html', {
        'conversation': conversation,
        'chat_messages': chat_messages,  # ← 충돌 피하기 위해 이름 변경
        'user_credit': user_credit,
        'credit_cost': gemini_service.credit_cost,
    })


@login_required
@require_http_methods(["POST"])
def send_message(request, conversation_id):
    """메시지 전송 API"""
    try:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            user=request.user,
            status='active'
        )

        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        # 메시지 검증
        is_valid, error_message = gemini_service.validate_user_message(user_message)
        if not is_valid:
            return JsonResponse({'success': False, 'error': error_message})

        # 사용자 메시지 저장
        Message.objects.create(
            conversation=conversation,
            sender='user',
            content=user_message
        )

        # AI 응답 생성
        ai_response, metadata = gemini_service.generate_response(conversation, user_message)

        # 에러 처리
        if 'error' in metadata:
            return JsonResponse({'success': False, 'error': ai_response})

        # AI 응답 저장
        Message.objects.create(
            conversation=conversation,
            sender='character',
            content=ai_response,
            ai_model_used=metadata.get('ai_model_used', ''),
            generation_time=metadata.get('generation_time')
        )

        # 대화 제목 자동 생성 (첫 쌍 교환 시)
        if conversation.message_count == 2:
            conversation.auto_generate_title()

        # 안전하게 남은 크레딧 계산
        user_credit, _ = UserCredit.objects.get_or_create(user=request.user)

        return JsonResponse({
            'success': True,
            'ai_response': ai_response,
            'credits_used': metadata.get('credits_used', 0),
            'remaining_credits': user_credit.total_credits
        })

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"메시지 전송 오류: {str(e)}")
        return JsonResponse({'success': False, 'error': '메시지 전송 중 오류가 발생했습니다.'})

def recommended_characters(request):
    """감정-장르 기반 캐릭터 추천"""
    emotion_id = request.GET.get('emotion')
    genre_id = request.GET.get('genre')
    sort_type = request.GET.get('sort', 'recommended')

    if not emotion_id or not genre_id:
        messages.error(request, '감정과 장르 정보가 필요합니다.')
        return redirect('emotions:emotion_selection')

    emotion = get_object_or_404(Emotion, id=emotion_id, is_active=True)
    genre = get_object_or_404(Genre, id=genre_id)

    # 해당 장르의 활성 캐릭터들
    characters_qs = Character.objects.filter(
        genre=genre,
        status='active',
        visibility='public'
    ).select_related('creator', 'genre').annotate(
        conversation_count=Count('conversation')
    )

    # 정렬 방식에 따른 처리
    if sort_type == 'recommended':
        # 추천순: 감정 키워드 매칭 + 개인화 점수
        characters_with_scores = []
        
        for character in characters_qs:
            score = calculate_recommendation_score(character, emotion, request.user)
            characters_with_scores.append((character, score))
        
        # 점수순 정렬
        characters_with_scores.sort(key=lambda x: x[1], reverse=True)
        characters = [item[0] for item in characters_with_scores]
        
    elif sort_type == 'rating':
        # 평점순
        characters = characters_qs.order_by('-rating_count', '-rating_sum', '-created_at')
        
    elif sort_type == 'popular':
        # 인기순 (대화수 기준)
        characters = characters_qs.order_by('-total_conversations', '-created_at')
        
    else:
        # 기본값
        characters = characters_qs.order_by('-created_at')

    # 페이지네이션
    paginator = Paginator(characters, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 감정 키워드 정보 (UI에 표시용)
    emotion_keywords = EmotionKeyword.objects.filter(
        emotion=emotion
    ).order_by('-weight')[:5]  # 상위 5개 키워드만

    context = {
        'emotion': emotion,
        'genre': genre,
        'page_obj': page_obj,
        'sort_type': sort_type,
        'emotion_keywords': emotion_keywords,
        'total_count': len(characters) if sort_type == 'recommended' else characters_qs.count(),
    }

    return render(request, 'characters/recommended_characters.html', context)


def calculate_recommendation_score(character, emotion, user):
    """캐릭터 추천 점수 계산"""
    score = 0.0
    
    # 1. 감정 키워드 매칭 점수 (40%)
    keyword_score = calculate_keyword_match_score(character, emotion)
    score += keyword_score * 0.4
    
    # 2. 사용자 선호도 점수 (30%)
    if user.is_authenticated:
        preference_score = calculate_user_preference_score(character, user)
        score += preference_score * 0.3
    
    # 3. 평점 점수 (20%)
    rating_score = character.average_rating / 5.0  # 0-1로 정규화
    score += rating_score * 0.2
    
    # 4. 인기도 점수 (10%)
    max_conversations = Character.objects.aggregate(
        max_conv=Count('conversation')
    )['max_conv'] or 1
    popularity_score = character.total_conversations / max_conversations
    score += popularity_score * 0.1
    
    return score


def calculate_keyword_match_score(character, emotion):
    """감정 키워드 매칭 점수 계산"""
    keywords = EmotionKeyword.objects.filter(emotion=emotion)
    score = 0.0
    max_possible_score = sum(kw.weight for kw in keywords)
    
    if max_possible_score == 0:
        return 0.0
    
    # 캐릭터의 텍스트 필드들
    text_fields = [
        character.description or '',
        character.personality or '',
        character.background_story or '',
        character.speaking_style or '',
        character.tags or ''
    ]
    
    combined_text = ' '.join(text_fields).lower()
    
    for keyword in keywords:
        if keyword.keyword in combined_text:
            score += keyword.weight
    
    # 0-1 범위로 정규화
    return score / max_possible_score


def calculate_user_preference_score(character, user):
    """사용자 선호도 점수 계산"""
    # 사용자의 대화 이력 기반 점수 계산
    user_conversations = Conversation.objects.filter(
        user=user,
        status='active'
    ).select_related('character__genre')
    
    if not user_conversations.exists():
        return 0.5  # 중간값
    
    # 같은 장르 대화 비율
    total_conversations = user_conversations.count()
    same_genre_conversations = user_conversations.filter(
        character__genre=character.genre
    ).count()
    
    genre_preference = same_genre_conversations / total_conversations
    
    # 비슷한 캐릭터와의 대화 만족도 (평가가 있다면)
    # 현재는 간단하게 장르 선호도만 반영
    return genre_preference