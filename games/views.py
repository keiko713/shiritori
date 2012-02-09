# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.template import RequestContext
from datetime import datetime
from games.models import *
from shiritori.extern import romkan
from jcconv import *
import re
import json

JAPANESE_KOMOJI = {
    u"ぁ": u"あ",
    u"ぃ": u"い",
    u"ぅ": u"う",
    u"ぇ": u"え",
    u"ぉ": u"お",
    u"ゃ": u"や",
    u"ゅ": u"ゆ",
    u"ょ": u"よ",
    u"っ": u"つ",
    u"ゎ": u"わ",
}

def index(request):
    error_message = None 
    if request.method == 'POST':
        game_id = request.POST.get('game_id', False)
        if game_id:
            name = request.POST.get('player_name' + game_id, False)
            if name:
                player = Player(name=name)
                player.save()
                game = get_object_or_404(Game, pk=game_id)
                gps = GamePlayer.objects.filter(game=game).exclude(turn_num=-1)
                game_player = GamePlayer(game=game, player=player, turn_num=len(gps))
                game_player.save()
                return HttpResponseRedirect(reverse('games.views.open_game', args=(game_player.id,)))
        error_message = "Name is required to join the game!"

    # the game that finish_date is None
    ongoing_games = Game.objects.filter(finish_date=None).exclude(current_turn=-1)
    gameplayers_list = []
    for game in ongoing_games:
        gameplayers_list.append(GamePlayer.objects.filter(game=game).exclude(turn_num=-1))
    return render_to_response('index.html', {
        'gameplayers_list': gameplayers_list,
        'error_message': error_message,
    }, context_instance=RequestContext(request))


def new_game(request):
    # get ongoing games
    game_number = len(Game.objects.filter(finish_date=None).exclude(current_turn=-1))
    return render_to_response('newgame/index.html', {
        'game_number': game_number,
    }, context_instance=RequestContext(request))


def create_game(request):
    name = request.POST.get('player_name', False)
    if not name:
        game_number = len(Game.objects.filter(finish_date=None).exclude(current_turn=-1))
        return render_to_response('newgame/index.html', {
                'game_number': game_number,
                'error_message': "Name is required!",
        }, context_instance=RequestContext(request))
            
    player = Player(name=name)
    player.save()
    game = Game()
    game.save()
    game_player = GamePlayer(game=game, player=player)
    game_player.save()
    return render_to_response('newgame/created.html', {
        'player_name': player.name,
        'game_id': game.id,
        'game_player_id': game_player.id,
    }, context_instance=RequestContext(request))


def open_game(request, game_player_id):
    game_player = get_object_or_404(GamePlayer, pk=game_player_id)
    if game_player.turn_num == -1:
        raise Http404
    player = get_object_or_404(Player, pk=game_player.player.id)
    game = get_object_or_404(Game, pk=game_player.game.id)
    if game.current_turn == -1:
        raise Http404
    history = GameHistory.objects.filter(game=game).order_by('-pk')
    gps = GamePlayer.objects.filter(game=game).order_by('turn_num').exclude(turn_num=-1)
    player_list = []

    turn_player = None
    for gp in gps:
        player_list.append(gp.player)
        if game.current_turn == gp.turn_num:
            turn_player = gp.player

    return render_to_response('game/index.html', {
        'game_player': game_player,
        'player': player,
        'game': game,
        'history': history,
        'player_list': player_list,
        'turn_player': turn_player,
    }, context_instance=RequestContext(request))

def add_word(request, game_player_id):
    game_player = get_object_or_404(GamePlayer, pk=game_player_id)
    player = get_object_or_404(Player, pk=game_player.player.id)
    game = get_object_or_404(Game, pk=game_player.game.id)

    error_message = None
    word = request.POST.get('word', False)
    if not word:
        # input check
        error_message = "Oh! input your word!"
    else:
        # change all input to katakana
        # if some letters are alphabet, change to katakana
        regex = u"[A-z|\-]"
        result = re.search(regex, word)
        if result:
            word = romkan.to_kana(word)
            
        # if some letters are hiragana, change to katakana
        regex = u"[ぁ-ゔ|ー]"
        result = re.search(regex, word)
        if result:
            word = hira2kata(word)
            # change the letter from hiragana to katakana manually
            # only the case of "ゔ"
            if u"ゔ" in word:
                word = word.replace(u"ゔ", u"ヴ")

        # check if all letters are katakana
        regex = u"^[ァ-ヴ|ー]*$"
        result = re.search(regex, word)
        if not result:
            error_message = "your input word includes unrecognizable letter"
        else:
            # exist check
            # TODO think about the case that there are more than 2 words in the dictionary
            # which have same hiragana
            # now, just avoid the problem, use the top hit word in the dictionary
            dic_words = Word.objects.filter(katakana=word)
            if not dic_words:
                error_message = word + " is not acceptable word. You can only input nouns"
            else:
                dic_word = dic_words[0]
                # history check
                if GameHistory.objects.filter(game=game_player.game, word=dic_word):
                    error_message = dic_word.hiragana + " is already used by someone!!"
                else:
                    # connect check
                    last_histories = GameHistory.objects.filter(game=game).order_by('-pk')
                    if last_histories:
                        last_history = last_histories[0]
                        last_word = last_history.word.hiragana
                        last_letter = last_word[-1]
                        # translate last letter if it's exception case
                        if last_letter == u"ー":
                            last_letter = last_word[-2]
                        if JAPANESE_KOMOJI.get(last_letter, False):
                            last_letter = JAPANESE_KOMOJI[last_letter]
                        if dic_word.hiragana[0] != last_letter:
                            error_message = last_word + " and " + dic_word.word + " are not connected!"
                    # end with "ん" check
                    if dic_word.hiragana[-1] == u"ん":
                        error_message = "Game Over!"

    if not error_message:
        his = GameHistory(game=game, player=player, word=dic_word)
        his.save()
        player_amount = len(GamePlayer.objects.filter(game=game))
        game.current_turn += 1
        if game.current_turn == player_amount:
            game.current_turn = 0
        game.save()

    history = GameHistory.objects.filter(game=game).order_by('-pk')
    gps = GamePlayer.objects.filter(game=game).order_by('turn_num').exclude(turn_num=-1)
    player_list = []

    turn_player = None
    for gp in gps:
        player_list.append(gp.player)
        if game.current_turn == gp.turn_num:
            turn_player = gp.player

    return render_to_response('game/index.html', {
        'game_player': game_player,
        'player': player,
        'game': game,
        'history': history,
        'player_list': player_list,
        'turn_player': turn_player,
        'error_message': error_message,
    }, context_instance=RequestContext(request))


def check_update(request, game_player_id, history_len, player_num):
    game_player = get_object_or_404(GamePlayer, pk=game_player_id)
    gps = GamePlayer.objects.filter(game=game_player.game).exclude(turn_num=-1)
    history = GameHistory.objects.filter(game=game_player.game)
    updated = False
    if int(history_len) < len(history) or int(player_num) != len(gps):
        updated = True
    result = { 
        'updated': updated,
    }

    data = json.dumps(result)
    return json_response(data)


# For ajax(json) #
def json_response(data, code=200, mimetype='application/json'):
    resp = HttpResponse(data, mimetype)
    resp.code = code
    return resp


def leave_room(request, game_player_id):
    # need to think about the case that there is only one player
    game_player = get_object_or_404(GamePlayer, pk=game_player_id)
    gps = GamePlayer.objects.filter(game=game_player.game).exclude(turn_num=-1)
    game = get_object_or_404(Game, pk=game_player.game.id)
    # case that leaving player is the only person in the room
    if len(gps) == 1:
        game.current_num = -1
        game.finish_date = datetime.now()
        game.save()
    else:
        turn_num = game_player.turn_num
        for gp in gps:
            if gp.turn_num > turn_num:
                gp.turn_num -= 1
                gp.save()
        if game.current_turn > turn_num:
            game.current_turn -= 1
            game.save()
        if game.current_turn == turn_num and turn_num == (len(gps) - 1):
            game.current_turn = 0
            game.save()

    game_player.turn_num = -1
    game_player.save()
    return HttpResponseRedirect(reverse('games.views.index'))
