# characters/urls.py
from django.urls import path
from . import views

app_name = 'characters'

urlpatterns = [
    # 캐릭터 관리
    path('create/', views.character_create, name='character_create'),
    path('my/', views.my_characters, name='my_characters'),
    path('', views.character_list, name='character_list'),
    path('<int:character_id>/', views.character_detail, name='character_detail'),

    # 편집/삭제
    path('<int:character_id>/edit/', views.character_edit, name='character_edit'),
    path('<int:character_id>/delete/', views.character_delete, name='character_delete'),

    # 추천 캐릭터 (새로 추가)
    path('recommended/', views.recommended_characters, name='recommended_characters'),

    # 대화 관련
    path('<int:character_id>/chat/', views.start_conversation, name='start_conversation'),
    path('chat/<int:conversation_id>/', views.conversation_view, name='conversation'),
    path('chat/<int:conversation_id>/send/', views.send_message, name='send_message'),
]
