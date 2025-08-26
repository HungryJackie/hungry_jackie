# emotions/management/commands/setup_emotions.py
from django.core.management.base import BaseCommand
from emotions.models import Emotion, Genre, EmotionGenreRecommendation


class Command(BaseCommand):
    help = '감정, 장르, 추천 데이터를 초기 설정합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='기존 데이터를 모두 삭제하고 새로 생성합니다',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(
                self.style.WARNING('기존 데이터를 삭제합니다...')
            )
            EmotionGenreRecommendation.objects.all().delete()
            Genre.objects.all().delete()
            Emotion.objects.all().delete()

        # 감정 데이터 생성
        emotions_data = [
            {
                'name': '우울해요',
                'emoji': '😢',
                'color_code': '#667eea',
                'description': '마음이 무겁고 힘이 빠져요',
                'sub_description': '답답하고 힘들어요',
                'order': 1
            },
            {
                'name': '짜증나요',
                'emoji': '😤',
                'color_code': '#f093fb',
                'description': '스트레스가 쌓이고 화가 나요',
                'sub_description': '스트레스 받아요',
                'order': 2
            },
            {
                'name': '외로워요',
                'emoji': '😔',
                'color_code': '#4facfe',
                'description': '혼자인 것 같고 공허해요',
                'sub_description': '혼자인 것 같아요',
                'order': 3
            },
            {
                'name': '자신없어요',
                'emoji': '😰',
                'color_code': '#43e97b',
                'description': '위축되고 용기가 나지 않아요',
                'sub_description': '위축되고 불안해요',
                'order': 4
            },
            {
                'name': '불안해요',
                'emoji': '😟',
                'color_code': '#fa709a',
                'description': '걱정이 많고 초조해요',
                'sub_description': '걱정이 많아요',
                'order': 5
            },
            {
                'name': '신나요',
                'emoji': '😊',
                'color_code': '#a8edea',
                'description': '기분이 좋고 들떠 있어요',
                'sub_description': '기분이 좋아요',
                'order': 6
            },
            {
                'name': '평온해요',
                'emoji': '😌',
                'color_code': '#d299c2',
                'description': '차분하고 안정되어 있어요',
                'sub_description': '차분하고 안정돼요',
                'order': 7
            }
        ]

        self.stdout.write('감정 데이터를 생성합니다...')
        emotions = {}
        for emotion_data in emotions_data:
            emotion, created = Emotion.objects.get_or_create(
                name=emotion_data['name'],
                defaults=emotion_data
            )
            emotions[emotion_data['name']] = emotion
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {emotion.emoji} {emotion.name} 생성됨')
                )

        # 장르 데이터 생성
        genres_data = [
            {
                'name': '치유물',
                'description': '마음의 상처를 천천히 치유하고 희망을 찾아가는 따뜻한 이야기들',
                'category': '웹툰'
            },
            {
                'name': '일상물',
                'description': '소소한 일상 속 따뜻함과 평범한 하루의 특별한 순간들',
                'category': '웹툰'
            },
            {
                'name': '동물물',
                'description': '동물들의 순수한 사랑과 따뜻한 교감을 통한 힐링 스토리',
                'category': '웹툰'
            },
            {
                'name': '사이다물',
                'description': '답답한 상황이 시원하게 해결되는 통쾌한 이야기들',
                'category': '웹툰'
            },
            {
                'name': '복수물',
                'description': '억울한 일에 대한 정의로운 복수와 응징의 이야기',
                'category': '웹툰'
            },
            {
                'name': '액션물',
                'description': '역동적인 액션과 박진감 넘치는 전개로 스트레스 해소',
                'category': '웹툰'
            },
            {
                'name': '우정물',
                'description': '진정한 우정과 동료애를 그린 따뜻한 이야기들',
                'category': '웹툰'
            },
            {
                'name': '가족물',
                'description': '가족 간의 사랑과 유대감을 다룬 감동적인 스토리',
                'category': '웹툰'
            },
            {
                'name': '성장물',
                'description': '주인공이 점진적으로 발전하고 성장하는 과정을 그린 이야기',
                'category': '웹툰'
            },
            {
                'name': '로맨스물',
                'description': '달콤하고 설레는 사랑 이야기',
                'category': '웹툰'
            },
            {
                'name': '모험물',
                'description': '새로운 세계를 탐험하는 흥미진진한 모험담',
                'category': '웹툰'
            },
            {
                'name': '판타지물',
                'description': '현실을 벗어난 상상의 세계에서 펼쳐지는 이야기',
                'category': '웹툰'
            },
            {
                'name': '미스터리물',
                'description': '수수께끼와 추리로 긴장감을 주는 흥미로운 이야기',
                'category': '웹툰'
            },
            {
                'name': '스포츠물',
                'description': '열정과 노력으로 승리를 향해 나아가는 스포츠 이야기',
                'category': '웹툰'
            }
        ]

        self.stdout.write('장르 데이터를 생성합니다...')
        genres = {}
        for genre_data in genres_data:
            genre, created = Genre.objects.get_or_create(
                name=genre_data['name'],
                defaults=genre_data
            )
            genres[genre_data['name']] = genre
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {genre.name} 생성됨')
                )

        # 감정-장르 추천 매핑 데이터
        recommendations_data = [
            # 우울해요
            ('우울해요', '치유물', 1, '주인공이 천천히 마음의 상처를 치유하고 성장하는 과정을 보며, 당신도 함께 위로받고 희망을 찾을 수 있어요.', 95),
            ('우울해요', '일상물', 2, '평범한 일상 속 소소한 즐거움과 따뜻한 순간들을 통해 마음의 안정을 찾을 수 있어요.', 88),
            ('우울해요', '동물물', 3, '동물들의 순수하고 따뜻한 사랑을 통해 자연스럽게 마음이 편안해지고 웃음을 되찾을 수 있어요.', 82),

            # 짜증나요
            ('짜증나요', '사이다물', 1, '답답했던 상황이 시원하게 해결되는 모습을 보며 쌓인 스트레스를 풀 수 있어요.', 92),
            ('짜증나요', '복수물', 2, '억울한 일에 대한 정의로운 응징을 보며 카타르시스를 느낄 수 있어요.', 89),
            ('짜증나요', '액션물', 3, '역동적인 액션과 박진감 넘치는 전개로 스트레스를 발산할 수 있어요.', 85),

            # 외로워요
            ('외로워요', '우정물', 1, '진정한 우정과 동료애를 통해 따뜻한 연결감을 느낄 수 있어요.', 90),
            ('외로워요', '가족물', 2, '가족 간의 사랑과 유대감을 보며 소속감과 따뜻함을 느낄 수 있어요.', 87),
            ('외로워요', '치유물', 3, '서로를 위로하고 치유하는 관계를 통해 외로움을 달랠 수 있어요.', 84),

            # 자신없어요
            ('자신없어요', '성장물', 1, '주인공이 점진적으로 성장하는 모습을 보며 자신감과 용기를 얻을 수 있어요.', 93),
            ('자신없어요', '사이다물', 2, '주인공이 어려움을 극복하는 통쾌한 장면들로 자신감을 회복할 수 있어요.', 88),
            ('자신없어요', '치유물', 3, '자신을 받아들이고 사랑하는 과정을 통해 내면의 힘을 찾을 수 있어요.', 85),

            # 불안해요
            ('불안해요', '판타지물', 1, '현실과 다른 상상의 세계로 잠시 현실의 걱정을 잊을 수 있어요.', 91),
            ('불안해요', '미스터리물', 2, '흥미진진한 추리에 집중하면서 자연스럽게 불안한 생각을 차단할 수 있어요.', 86),
            ('불안해요', '일상물', 3, '평온한 일상의 이야기로 마음을 차분하게 만들 수 있어요.', 82),

            # 신나요
            ('신나요', '로맨스물', 1, '달콤하고 설레는 연애 이야기로 기분 좋은 감정을 더욱 끌어올릴 수 있어요.', 94),
            ('신나요', '모험물', 2, '흥미진진한 모험담으로 신나는 기분을 계속 유지할 수 있어요.', 89),
            ('신나요', '스포츠물', 3, '열정적이고 에너지 넘치는 스포츠 이야기와 잘 어울려요.', 86),

            # 평온해요
            ('평온해요', '일상물', 1, '잔잔하고 평화로운 일상의 이야기로 현재의 평온함을 더 깊이 느낄 수 있어요.', 92),
            ('평온해요', '치유물', 2, '따뜻하고 차분한 치유의 이야기로 마음의 평화를 유지할 수 있어요.', 88),
            ('평온해요', '동물물', 3, '동물들과의 순수한 교감을 통해 자연스러운 평안함을 느낄 수 있어요.', 84),
        ]

        self.stdout.write('감정-장르 추천 매핑을 생성합니다...')
        for emotion_name, genre_name, priority, reason, match_percentage in recommendations_data:
            emotion = emotions[emotion_name]
            genre = genres[genre_name]
            
            recommendation, created = EmotionGenreRecommendation.objects.get_or_create(
                emotion=emotion,
                genre=genre,
                defaults={
                    'priority': priority,
                    'reason': reason,
                    'match_percentage': match_percentage
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {emotion_name} → {genre_name} ({priority}순위) 매핑 생성됨')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n성공적으로 초기 데이터가 설정되었습니다!\n'
                f'- 감정: {len(emotions)}개\n'
                f'- 장르: {len(genres)}개\n'
                f'- 추천 매핑: {len(recommendations_data)}개'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f'\n이제 다음 URL에서 테스트해보세요:\n'
                f'http://127.0.0.1:8000/emotions/'
            )
        )