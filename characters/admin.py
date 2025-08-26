from django.contrib import admin
from .models import Character, Conversation, Message, UserCredit, CharacterRating

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'genre', 'status', 'total_conversations', 'created_at']
    list_filter = ['status', 'genre', 'created_at']
    search_fields = ['name', 'creator__username', 'description']

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'character', 'title', 'status', 'message_count', 'created_at']
    list_filter = ['status', 'created_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender', 'content_preview', 'timestamp']
    list_filter = ['sender', 'timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

@admin.register(UserCredit)
class UserCreditAdmin(admin.ModelAdmin):
    list_display = ['user', 'free_credits', 'created_at']
    
@admin.register(CharacterRating)
class CharacterRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'character', 'rating', 'created_at']