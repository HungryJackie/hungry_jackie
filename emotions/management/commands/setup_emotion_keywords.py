# emotions/management/commands/setup_emotion_keywords.py
from django.core.management.base import BaseCommand
from emotions.models import Emotion, EmotionKeyword


class Command(BaseCommand):
    help = '감정별 키워드 데이터를 초기 설정합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='기존 키워드를 모두 삭제하고 새로 생성합니다',
        )
        parser.add_argument(
            '--emotion',
            type=str,
            help='특정 감정의 키워드만 생성합니다',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(
                self.style.WARNING('기존 감정 키워드를 삭제합니다...')
            )
            EmotionKeyword.objects.all().delete()

        # 감정별 키워드 데이터
        keywords_data = {
            '우울해요': [
                # 핵심 키워드 (높은 가중치)
                ('위로', 3.0, '마음의 위안과 달램'),
                ('치유', 3.0, '상처받은 마음을 고치는 것'),
                ('따뜻함', 2.5, '포근하고 온화한 느낌'),
                ('희망', 2.5, '미래에 대한 긍정적 기대'),
                ('회복', 2.0, '원래 상태로 돌아가는 것'),
                ('안정', 2.0, '마음의 평안'),
                
                # 보조 키워드 (중간 가중치)
                ('공감', 1.5, '마음을 이해해주는 것'),
                ('이해', 1.5, '상황을 알아주는 것'),
                ('격려', 1.5, '용기를 북돋아주는 것'),
                ('지지', 1.5, '옆에서 도와주는 것'),
                ('평온', 1.0, '조용하고 고요한 상태'),
                ('휴식', 1.0, '쉬어가는 시간'),
                ('성장', 1.0, '발전하고 나아가는 것'),
                ('자립', 1.0, '스스로 일어서는 것'),
            ],
            
            '짜증나요': [
                ('시원함', 3.0, '답답함이 해결되는 느낌'),
                ('통쾌', 3.0, '속이 뚫리는 시원함'),
                ('복수', 2.5, '억울함에 대한 되갚음'),
                ('해결', 2.5, '문제가 풀리는 것'),
                ('속시원', 2.0, '막혔던 것이 뚫리는 것'),
                ('카타르시스', 2.0, '감정의 정화와 해방'),
                
                ('정의', 1.5, '옳고 바른 것'),
                ('응징', 1.5, '잘못에 대한 벌'),
                ('반격', 1.5, '맞서 싸우는 것'),
                ('승리', 1.5, '이기는 것'),
                ('발산', 1.0, '감정을 내뿜는 것'),
                ('해소', 1.0, '쌓인 것을 풀어내는 것'),
                ('보상', 1.0, '받을 만한 것을 받는 것'),
            ],
            
            '외로워요': [
                ('동반', 3.0, '함께 있어주는 것'),
                ('친구', 3.0, '마음을 나누는 사람'),
                ('소통', 2.5, '마음을 주고받는 것'),
                ('연결', 2.5, '관계를 이어가는 것'),
                ('유대', 2.0, '끈끈한 관계'),
                ('교감', 2.0, '마음이 통하는 것'),
                
                ('가족', 1.5, '혈연이나 정을 나누는 사이'),
                ('사랑', 1.5, '깊은 애정'),
                ('배려', 1.5, '남을 생각해주는 것'),
                ('관심', 1.5, '신경써주는 것'),
                ('대화', 1.0, '이야기를 나누는 것'),
                ('공유', 1.0, '함께 나누는 것'),
                ('신뢰', 1.0, '믿고 의지하는 것'),
            ],
            
            '자신없어요': [
                ('용기', 3.0, '두려움을 이겨내는 힘'),
                ('자신감', 3.0, '스스로를 믿는 마음'),
                ('성취', 2.5, '목표를 달성하는 것'),
                ('도전', 2.5, '어려운 일에 맞서는 것'),
                ('극복', 2.0, '어려움을 이겨내는 것'),
                ('발전', 2.0, '더 나아지는 것'),
                
                ('성공', 1.5, '목표를 이루는 것'),
                ('인정', 1.5, '능력을 받아들여지는 것'),
                ('칭찬', 1.5, '잘한 것을 인정받는 것'),
                ('격려', 1.5, '힘을 북돋아주는 것'),
                ('지원', 1.0, '도움을 받는 것'),
                ('능력', 1.0, '할 수 있는 힘'),
                ('가능성', 1.0, '될 수 있는 여지'),
            ],
            
            '불안해요': [
                ('안전', 3.0, '위험하지 않은 상태'),
                ('안정', 3.0, '마음이 편안한 상태'),
                ('평화', 2.5, '조용하고 고요한 상태'),
                ('확신', 2.5, '의심 없이 믿는 것'),
                ('신뢰', 2.0, '믿고 의지할 수 있는 것'),
                ('보장', 2.0, '확실히 지켜주는 것'),
                
                ('예측', 1.5, '미리 알 수 있는 것'),
                ('계획', 1.5, '앞일을 준비하는 것'),
                ('통제', 1.5, '상황을 다스리는 것'),
                ('질서', 1.5, '정돈된 상태'),
                ('규칙', 1.0, '정해진 원칙'),
                ('일관성', 1.0, '변하지 않는 것'),
                ('명확성', 1.0, '분명하고 확실한 것'),
            ],
            
            '신나요': [
                ('즐거움', 3.0, '기분좋고 재미있는 것'),
                ('흥미', 3.0, '관심을 끄는 것'),
                ('활기', 2.5, '생기있고 에너지 넘치는 것'),
                ('모험', 2.5, '새롭고 스릴있는 경험'),
                ('설렘', 2.0, '기대되고 두근거리는 것'),
                ('역동', 2.0, '활발하게 움직이는 것'),
                
                ('열정', 1.5, '뜨거운 마음'),
                ('도전', 1.5, '새로운 시도'),
                ('발견', 1.5, '새로운 것을 찾는 것'),
                ('성장', 1.5, '발전하는 것'),
                ('경험', 1.0, '직접 해보는 것'),
                ('변화', 1.0, '새로워지는 것'),
                ('가능성', 1.0, '될 수 있는 여지'),
            ],
            
            '평온해요': [
                ('고요', 3.0, '조용하고 잔잔한 상태'),
                ('평화', 3.0, '마음이 편안한 상태'),
                ('여유', 2.5, '급하지 않은 느긋함'),
                ('안정', 2.5, '흔들리지 않는 상태'),
                ('균형', 2.0, '조화로운 상태'),
                ('조화', 2.0, '어울리는 상태'),
                
                ('명상', 1.5, '마음을 가라앉히는 것'),
                ('성찰', 1.5, '자신을 돌아보는 것'),
                ('휴식', 1.5, '쉬는 시간'),
                ('자연', 1.5, '자연스러운 상태'),
                ('일상', 1.0, '평범한 하루'),
                ('소박', 1.0, '간소하고 꾸밈없는 것'),
                ('단순', 1.0, '복잡하지 않은 것'),
            ],
        }

        target_emotion = options.get('emotion')
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for emotion_name, keywords in keywords_data.items():
            # 특정 감정만 처리하는 경우
            if target_emotion and emotion_name != target_emotion:
                continue

            try:
                emotion = Emotion.objects.get(name=emotion_name)
            except Emotion.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'감정 "{emotion_name}"을 찾을 수 없습니다.')
                )
                continue

            self.stdout.write(f'\n{emotion_name} 키워드 생성 중...')

            for keyword, weight, description in keywords:
                keyword_obj, created = EmotionKeyword.objects.get_or_create(
                    emotion=emotion,
                    keyword=keyword,
                    defaults={
                        'weight': weight,
                        'description': description
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ {keyword} (가중치: {weight}) - {description}')
                    )
                    created_count += 1
                else:
                    # 기존 키워드 업데이트
                    if keyword_obj.weight != weight or keyword_obj.description != description:
                        keyword_obj.weight = weight
                        keyword_obj.description = description
                        keyword_obj.save()
                        self.stdout.write(
                            self.style.WARNING(f'  ↻ {keyword} 업데이트됨')
                        )
                        updated_count += 1
                    else:
                        skipped_count += 1

        # 최종 결과 표시
        self.stdout.write(
            self.style.SUCCESS(
                f'\n키워드 설정이 완료되었습니다!\n'
                f'- 생성됨: {created_count}개\n'
                f'- 업데이트됨: {updated_count}개\n'
                f'- 건너뜀: {skipped_count}개'
            )
        )

        # 활성 키워드 요약
        total_keywords = EmotionKeyword.objects.count()
        emotions_with_keywords = EmotionKeyword.objects.values('emotion__name').distinct().count()
        
        self.stdout.write(
            self.style.WARNING(
                f'\n전체 키워드 현황:\n'
                f'- 총 키워드 수: {total_keywords}개\n'
                f'- 키워드가 있는 감정 수: {emotions_with_keywords}개'
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n관리자 페이지에서 확인하세요:\n'
                f'http://127.0.0.1:8000/admin/emotions/emotionkeyword/'
            )
        )