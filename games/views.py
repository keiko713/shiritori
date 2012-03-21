# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.template import RequestContext
from datetime import datetime
from games.models import *
from shiritori.extern import romkan
from jcconv import *
from social_auth import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from games.forms import *
import re
import json
import urlparse

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


@login_required
def new_game(request):
    if request.method == 'POST':
        form = NewGameForm(data=request.POST)
        if form.is_valid():
            players = Player.objects.filter(user=request.user)
            if players:
                player = players[0]
            else:
                # the case that player logged in using social auth,
                # player is not made yet
                player = Player(user=request.user, name=request.user.username)
                player.save()
            game = form.save()
            game_player = GamePlayer(game=game, player=player)
            game_player.save()
            return HttpResponseRedirect(reverse('games.views.open_game', args=(game_player.id,)))
    else:
        form = NewGameForm()

    # get ongoing games
    game_number = len(Game.objects.filter(finish_date=None).exclude(current_turn=-1))

    return render_to_response('newgame/index.html', {
        'game_number': game_number,
        'form': form,
    }, context_instance=RequestContext(request))


@login_required
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

    error_message = None
    player_hist = GameHistory.objects.filter(game=game, player=player)
    if not player_hist:
        error_message = "Welcome to New Game!"

    return render_to_response('game/index.html', {
        'game_player': game_player,
        'player': player,
        'game': game,
        'history': history,
        'player_list': player_list,
        'turn_player': turn_player,
        'error_message': error_message,
    }, context_instance=RequestContext(request))


@login_required
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
                            error_message = last_word + " and " + dic_word.hiragana + " are not connected!"
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


# For ajax and check update
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


@login_required
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


def join_game(request, game_player_id):
    game_player = get_object_or_404(GamePlayer, pk=game_player_id)
    if request.user.is_authenticated():
        players = Player.objects.filter(user=request.user)
        if players:
            player = players[0]
        else:
            # the case that player logged in using social auth,
            # player is not made yet
            player = Player(user=request.user, name=request.user.username)
            player.save()
        game = game_player.game 
        # this player is already in the room?
        check_gps = GamePlayer.objects.filter(game=game, player=player)
        if check_gps:
            my_game_player = check_gps[0]
        else:
            gps = GamePlayer.objects.filter(game=game).exclude(turn_num=-1)
            my_game_player = GamePlayer(game=game, player=player, turn_num=len(gps))
            my_game_player.save()

        return HttpResponseRedirect(reverse('games.views.open_game', args=(my_game_player.id,)))
    else:
        # show the static page that lead invited user to the login page
        owner_name = game_player.player.name
        return render_to_response('newgame/join.html', {
            'owner_name': owner_name,
            'game_player_id': game_player_id,
        }, context_instance=RequestContext(request))


@csrf_protect
@never_cache
def login_form(request):
    redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, '')
    netloc = urlparse.urlparse(redirect_to)[1]
    # default event is login
    event = 'login'
    form1, form2 = None, None

    # Use default setting if redirect_to is empty
    if not redirect_to:
        redirect_to = settings.LOGIN_REDIRECT_URL

    # Security check -- don't allow redirection to a different
    # host.
    elif netloc and netloc != request.get_host():
        redirect_to = settings.LOGIN_REDIRECT_URL

    # if the user already logged in, redirect to top page
    if request.user.is_authenticated():
        return HttpResponseRedirect(redirect_to)

    if request.method == 'POST':
        event = request.POST.get('event', False)
            
        if event:
            # make a new user
            if event == 'new':
                form1 = MyUserCreationForm(data=request.POST)
                if form1.is_valid():
                    form1.save()
                    user = authenticate(username=form1.cleaned_data['username'],
                        password=form1.cleaned_data['password2'])
                    login(request, user)
                    # make the Player object at the same time
                    player = Player(user=user, name=user.username)
                    player.save()
                    if request.session.test_cookie_worked():
                        request.session.delete_test_cookie()

                    return HttpResponseRedirect(redirect_to)

            # login
            elif event == 'login':
                form2 = MyAuthenticationForm(data=request.POST)
                if form2.is_valid():
                    login(request, form2.get_user())

                    if request.session.test_cookie_worked():
                        request.session.delete_test_cookie()

                    return HttpResponseRedirect(redirect_to)

    if not form1:
        form1 = MyUserCreationForm()
    if not form2:
        form2 = MyAuthenticationForm()

    request.session.set_test_cookie()

    return render_to_response('login_form.html', {
        'form1': form1,
        'form2': form2,
        'event': event,
        'next': redirect_to,
    }, context_instance=RequestContext(request))

