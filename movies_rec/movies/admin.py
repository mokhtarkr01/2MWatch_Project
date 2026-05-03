from django.contrib import admin, messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html
from .models import Movie, Genre, Rating, Watchlist
from .admin_site import admin_site


# ── helpers ──────────────────────────────────────────────────────────────────

def soft_delete_action(modeladmin, request, queryset):
    queryset.update(deleted_at=__import__('django.utils.timezone', fromlist=['timezone']).timezone.now())
    messages.success(request, f"{queryset.count()} item(s) moved to trash.")
soft_delete_action.short_description = "Move selected to trash"


# ── Genre ─────────────────────────────────────────────────────────────────────

class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_deleted']
    search_fields = ['name']
    actions = [soft_delete_action]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(deleted_at__isnull=True)

    def is_deleted(self, obj):
        return obj.deleted_at is not None
    is_deleted.boolean = True
    is_deleted.short_description = 'Deleted'

    def delete_model(self, request, obj):
        obj.soft_delete()

    def delete_queryset(self, request, queryset):
        from django.utils import timezone
        queryset.update(deleted_at=timezone.now())


# ── Movie ─────────────────────────────────────────────────────────────────────

class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_year', 'director', 'average_rating', 'rating_count']
    list_filter = ['genres', 'release_year']
    search_fields = ['title', 'director']
    filter_horizontal = ['genres']
    actions = [soft_delete_action]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(deleted_at__isnull=True)

    def delete_model(self, request, obj):
        obj.soft_delete()

    def delete_queryset(self, request, queryset):
        from django.utils import timezone
        queryset.update(deleted_at=timezone.now())


# ── Rating / Watchlist ────────────────────────────────────────────────────────

class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'score', 'created_at']
    list_filter = ['score']
    search_fields = ['user__username', 'movie__title']


class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'added_at']
    search_fields = ['user__username', 'movie__title']


# ── Register ──────────────────────────────────────────────────────────────────

admin_site.register(Genre, GenreAdmin)
admin_site.register(Movie, MovieAdmin)
admin_site.register(Rating, RatingAdmin)
admin_site.register(Watchlist, WatchlistAdmin)
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
