from django.db import models
from django.contrib.auth.models import User

class Game(models.Model):
    # turn_num=-1: this game is deleted
    current_turn = models.IntegerField(default=0)
    create_date = models.DateTimeField(auto_now_add=True)
    finish_date = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return u'%s (%s, %s, %s)' % (self.id, self.current_turn, self.create_date, self.finish_date)

class Player(models.Model):
    user = models.ForeignKey(User)
    # user.username is the default
    name = models.CharField(max_length=10)

    def __unicode__(self):
        return u'%s' % (name)

class Word(models.Model):
    hiragana = models.CharField(max_length=50)
    katakana = models.CharField(max_length=50)
    midashigo = models.CharField(max_length=50)
    hinshi = models.CharField(max_length=30)

class GamePlayer(models.Model):
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player)
    # turn_num=-1: this player left this game
    turn_num = models.IntegerField(default=0)
    passes = models.IntegerField(default=0)
    won = models.BooleanField(default=False)

class GameHistory(models.Model):
    game = models.ForeignKey(Game)
    player = models.ForeignKey(Player)
    word = models.ForeignKey(Word)
