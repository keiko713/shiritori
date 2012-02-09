from games.models import *
from django.contrib import admin

class GameAdmin(admin.ModelAdmin):
    list_display = ('current_turn', 'create_date', 'finish_date')

admin.site.register(Game, GameAdmin)

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Player, PlayerAdmin)

class WordAdmin(admin.ModelAdmin):
    list_display = ('hiragana', 'katakana', 'midashigo', 'hinshi')

admin.site.register(Word, WordAdmin)

class GamePlayerAdmin(admin.ModelAdmin):
    list_display = ('game', 'player', 'turn_num', 'won')

admin.site.register(GamePlayer, GamePlayerAdmin)

class GameHistoryAdmin(admin.ModelAdmin):
    list_display = ('game', 'player', 'word')

admin.site.register(GameHistory, GameHistoryAdmin)
