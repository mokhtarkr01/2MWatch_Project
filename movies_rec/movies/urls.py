from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('movies/', views.movie_list, name='movie_list'),
    path('movies/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('movies/<int:pk>/rate/', views.rate_movie, name='rate_movie'),
    path('movies/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('movies/<int:pk>/watchlist/', views.toggle_watchlist, name='toggle_watchlist'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('matches/', views.matches, name='matches'),
    path('matches/<int:match_id>/', views.chat, name='chat'),
]
