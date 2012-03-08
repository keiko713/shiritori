from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'games.views.index'),
    url(r'^newgame/$', 'games.views.new_game'),
    url(r'^newgame/join/(?P<game_player_id>\d+)/$', 'games.views.join_game'),
    url(r'^game/(?P<game_player_id>\d+)/$', 'games.views.open_game'),
    url(r'^game/(?P<game_player_id>\d+)/add/$', 'games.views.add_word'),
    url(r'^game/(?P<game_player_id>\d+)/check/(?P<history_len>\d+)/(?P<player_num>\d+)/$', 'games.views.check_update'),
    url(r'^game/(?P<game_player_id>\d+)/leave/$', 'games.views.leave_room'),

    url(r'', include('social_auth.urls')),
    url(r'^logged-in/$', 'games.views.logged_in'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', 
        {'next_page': '/'}),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
