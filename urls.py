from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'games.views.index'),
    url(r'^newgame/$', 'games.views.new_game'),
    url(r'^newgame/create/$', 'games.views.create_game'),
    url(r'^game/(?P<game_player_id>\d+)/$', 'games.views.open_game'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
