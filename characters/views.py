from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
import json

from .models import Character, Conversation, Message, UserCredit
from .forms import CharacterCreateForm
from .services import gemini_service
from emotions.models import Emotion, Genre


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
    """캐릭터 삭제"""
    character = get_object_or_404(Character, id=character_id, creator=request.user)
    if request.method == 'POST':
        character.delete()
        messages.success(request, '캐릭터가 삭제되었습니다.')
        return redirect('characters:my_characters')

    # 간단한 확인 화면이 없다면 바로 삭제 UI 없이 리스트로 돌려보내도 됨
    messages.error(request, '잘못된 접근입니다.')
    return redirect('characters:my_characters')


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

    # 메시지 목록
    messages_qs = conversation.messages.order_by('timestamp')

    # 사용자 크레딧 정보 (없으면 생성)
    user_credit, _ = UserCredit.objects.get_or_create(user=request.user)

    return render(request, 'characters/conversation.html', {
        'conversation': conversation,
        'messages': messages_qs,
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
