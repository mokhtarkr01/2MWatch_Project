from django.contrib.admin import AdminSite
from django.db.models import Avg, Count
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib import messages
from django.utils import timezone
from .models import Movie, Rating, Watchlist, Genre, AdminAlert, Match, Message


class MovieAdminSite(AdminSite):
    site_header = "2MWatch Administration"
    site_title = "2MWatch Admin"
    index_title = "Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('trash/', self.admin_view(self.trash_view), name='trash'),
            path('trash/restore/<str:model>/<int:pk>/', self.admin_view(self.restore_view), name='trash_restore'),
            path('trash/delete/<str:model>/<int:pk>/', self.admin_view(self.hard_delete_view), name='trash_delete'),
            path('alerts/', self.admin_view(self.alerts_view), name='alerts'),
            path('alerts/mark-read/', self.admin_view(self.alerts_mark_read), name='alerts_mark_read'),
            path('alerts/clear/', self.admin_view(self.alerts_clear), name='alerts_clear'),
            path('matches/', self.admin_view(self.matches_view), name='matches'),
            path('matches/<int:match_id>/', self.admin_view(self.match_chat_view), name='match_chat'),
        ]
        return custom + urls

    # ── Trash list ────────────────────────────────────────────────────────────

    def trash_view(self, request):
        deleted_movies = Movie.objects.filter(deleted_at__isnull=False).order_by('-deleted_at')
        deleted_genres = Genre.objects.filter(deleted_at__isnull=False).order_by('-deleted_at')
        context = {
            **self.each_context(request),
            'title': 'Trash',
            'deleted_movies': deleted_movies,
            'deleted_genres': deleted_genres,
        }
        return TemplateResponse(request, 'admin/trash.html', context)

    # ── Restore ───────────────────────────────────────────────────────────────

    def restore_view(self, request, model, pk):
        obj = self._get_trashed(model, pk)
        if obj:
            obj.restore()
            messages.success(request, f'"{obj}" has been restored.')
        return redirect('admin:trash')

    # ── Hard delete ───────────────────────────────────────────────────────────

    def hard_delete_view(self, request, model, pk):
        if request.method == 'POST':
            obj = self._get_trashed(model, pk)
            if obj:
                name = str(obj)
                obj.delete()
                messages.success(request, f'"{name}" permanently deleted.')
        return redirect('admin:trash')

    # ── Helper ────────────────────────────────────────────────────────────────

    def _get_trashed(self, model, pk):
        mapping = {'movie': Movie, 'genre': Genre}
        Model = mapping.get(model)
        if not Model:
            return None
        try:
            return Model.objects.get(pk=pk, deleted_at__isnull=False)
        except Model.DoesNotExist:
            return None

    # ── Alerts ────────────────────────────────────────────────────────────────

    def alerts_view(self, request):
        alerts = AdminAlert.objects.all()[:100]
        # mark all as read on open
        AdminAlert.objects.filter(read=False).update(read=True)
        context = {
            **self.each_context(request),
            'title': 'Alerts',
            'alerts': alerts,
        }
        return TemplateResponse(request, 'admin/alerts.html', context)

    def alerts_mark_read(self, request):
        AdminAlert.objects.filter(read=False).update(read=True)
        return redirect('admin:alerts')

    def alerts_clear(self, request):
        if request.method == 'POST':
            AdminAlert.objects.all().delete()
        return redirect('admin:alerts')

    # ── Matches ───────────────────────────────────────────────────────────────

    def matches_view(self, request):
        from django.db.models import Count, Q
        matches = (
            Match.objects.select_related('user1', 'user2')
            .annotate(msg_count=Count('messages'))
            .order_by('-created_at')
        )
        match_data = []
        for m in matches:
            # shared same-score movies
            u1_ratings = {r.movie_id: r.score for r in Rating.objects.filter(user=m.user1)}
            u2_ratings = {r.movie_id: r.score for r in Rating.objects.filter(user=m.user2)}
            shared_ids = [mid for mid, score in u1_ratings.items() if u2_ratings.get(mid) == score]
            shared_movies = Movie.objects.filter(pk__in=shared_ids[:5])
            match_data.append({
                'match': m,
                'shared': shared_movies,
                'shared_count': len(shared_ids),
            })
        context = {
            **self.each_context(request),
            'title': 'User Matches',
            'match_data': match_data,
        }
        return TemplateResponse(request, 'admin/matches.html', context)

    def match_chat_view(self, request, match_id):
        match = Match.objects.select_related('user1', 'user2').get(pk=match_id)
        messages_qs = match.messages.select_related('sender').all()
        context = {
            **self.each_context(request),
            'title': f'Chat: {match.user1.username} ↔ {match.user2.username}',
            'match': match,
            'messages': messages_qs,
        }
        return TemplateResponse(request, 'admin/match_chat.html', context)

    # ── Dashboard index ───────────────────────────────────────────────────────

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}

        top_movies = (
            Movie.objects.filter(deleted_at__isnull=True)
            .annotate(avg=Avg('ratings__score'), cnt=Count('ratings'))
            .filter(cnt__gt=0)
            .order_by('-avg', '-cnt')[:8]
        )
        active_users = (
            User.objects.annotate(
                rating_count=Count('ratings'),
                watchlist_count=Count('watchlist'),
            )
            .filter(rating_count__gt=0)
            .order_by('-rating_count')[:8]
        )
        recent_ratings = (
            Rating.objects.select_related('user', 'movie')
            .order_by('-created_at')[:10]
        )
        genres_qs = Genre.objects.filter(deleted_at__isnull=True).annotate(count=Count('movies')).order_by('-count')[:10]
        max_count = genres_qs[0].count if genres_qs else 1
        genre_stats = [
            {'name': g.name, 'count': g.count, 'pct': round(g.count / max_count * 100)}
            for g in genres_qs
        ]
        trash_count = (
            Movie.objects.filter(deleted_at__isnull=False).count() +
            Genre.objects.filter(deleted_at__isnull=False).count()
        )
        unread_alerts = AdminAlert.objects.filter(read=False).count()
        total_matches = Match.objects.count()

        extra_context.update({
            'stats': {
                'movies': Movie.objects.filter(deleted_at__isnull=True).count(),
                'users': User.objects.count(),
                'ratings': Rating.objects.count(),
                'watchlist': Watchlist.objects.count(),
                'genres': Genre.objects.filter(deleted_at__isnull=True).count(),
            },
            'top_movies': top_movies,
            'active_users': active_users,
            'recent_ratings': recent_ratings,
            'genre_stats': genre_stats,
            'trash_count': trash_count,
            'unread_alerts': unread_alerts,
            'total_matches': total_matches,
        })
        return super().index(request, extra_context)


admin_site = MovieAdminSite(name='admin')
