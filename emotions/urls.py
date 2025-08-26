# emotions/urls.py
from django.urls import path
from . import views

app_name = 'emotions'

urlpatterns = [
    # 메인 감정 선택 페이지
    path('', views.emotion_selection, name='emotion_selection'),
    
    # 추천 결과 페이지
    path('recommendations/<int:emotion_id>/', views.get_recommendations, name='get_recommendations'),
    
    # 감정 기록 저장
    path('save-entry/', views.save_emotion_entry, name='save_emotion_entry'),
    
    # 사용자 감정 히스토리
    path('history/', views.user_emotion_history, name='emotion_history'),
    
    # API 엔드포인트들
    path('api/emotions/', views.api_emotions, name='api_emotions'),
    path('api/recommendations/<int:emotion_id>/', views.api_recommendations, name='api_recommendations'),
]