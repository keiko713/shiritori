from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from games.models import *

def index(request):
    # the game that finish_date is None
    ongoing_games = Game.objects.filter(finish_date=None)
    gameplayers_list = []
    for game in ongoing_games:
        gameplayers_list.append(GamePlayer.objects.filter(game=game))
    return render_to_response('index.html', {'gameplayers_list': gameplayers_list})


def new_game(request):
    # get ongoing games
    ongoing_games = Game.objects.filter(finish_date=None)
    game_number = 0
    if ongoing_games:
        game_number = len(ongoing_games)
    return render_to_response('newgame/index.html', {
        'game_number': game_number,
    }, context_instance=RequestContext(request))


def create_game(request):
    name = request.POST.get('player_name', False)
    if not name:
        # get ongoing games TODO: duplicated codes, it need to be fixed.
        ongoing_games = Game.objects.filter(finish_date=None)
        game_number = 0
        if ongoing_games:
            game_number = len(ongoing_games)
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
    })


def open_game(request, game_player_id):
    game_player = get_object_or_404(GamePlayer, pk=game_player_id)
    player = get_object_or_404(Player, pk=game_player.player.id)
    game = get_object_or_404(Game, pk=game_player.game.id)
    history = GameHistory.objects.filter(game=game_player.game, player=game_player.player)
    gps = GamePlayer.objects.filter(game=game_player.game)
    player_list = []
    for gp in gps:
        if not gp.player == player:
            player_list.append(gp.player)

    return render_to_response('game/index.html', {
        'game_player': game_player,
        'player': player,
        'game': game,
        'history': history,
        'player_list': player_list,
    })
