from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process', views.process, name='process'),
    path('search_games', views.search_games_view, name='search_games'),
]

