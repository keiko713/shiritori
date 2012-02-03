from django.db import models

class Game(models.Model):
    create_date = models.DateTimeField(auto_now_add=True)
    finish_date = models.DateTimeField(blank=True, null=True)

class Player(models.Model):
    name = models.CharField(max_length=10)

class Word(models.Model):
    word = models.CharField(max_length=30)
    kanji = models.CharField(max_length=30)
    hinshi = models.CharField(max_length=30)

class GamePlayer(models.Model):
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player)
    elapse_time = models.BigIntegerField(default=0)
    won = models.BooleanField(default=False)

class GameHistory(models.Model):
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player)
    word = models.ForeignKey(Word)
