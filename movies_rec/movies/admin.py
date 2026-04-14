from django.contrib import admin
from .models import Movie, Genre, Rating, Watchlist


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_year', 'director', 'average_rating', 'rating_count']
    list_filter = ['genres', 'release_year']
    search_fields = ['title', 'director']
    filter_horizontal = ['genres']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'score', 'created_at']
    list_filter = ['score']
    search_fields = ['user__username', 'movie__title']


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'added_at']
    search_fields = ['user__username', 'movie__title']
