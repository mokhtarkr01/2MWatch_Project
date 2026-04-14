from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Avg
from .models import Movie, Rating, Watchlist, Genre
from .recommender import get_recommendations, get_similar_movies


@login_required
def home(request):
    """Home page: personalized recommendations + recently rated."""
    movies, scored = get_recommendations(request.user, top_n=12)

    user_ratings = {r.movie_id: r.score for r in request.user.ratings.all()}
    watchlist_ids = set(request.user.watchlist.values_list('movie_id', flat=True))

    # Fallback if no recommendations yet
    if not movies:
        movies = list(Movie.objects.prefetch_related('genres').order_by('?')[:12])
        scored = [(m, m.average_rating()) for m in movies]

    recently_rated = (
        Rating.objects.filter(user=request.user)
        .select_related('movie')
        .prefetch_related('movie__genres')
        .order_by('-updated_at')[:6]
    )

    genres = Genre.objects.all().order_by('name')

    return render(request, 'movies/home.html', {
        'scored_movies': scored,
        'recently_rated': recently_rated,
        'user_ratings': user_ratings,
        'watchlist_ids': watchlist_ids,
        'genres': genres,
        'has_ratings': request.user.ratings.exists(),
    })


@login_required
def movie_list(request):
    """Browse all movies with search and genre filter."""
    q = request.GET.get('q', '').strip()
    genre_id = request.GET.get('genre', '')
    sort = request.GET.get('sort', 'title')

    movies = Movie.objects.prefetch_related('genres')

    if q:
        movies = movies.filter(Q(title__icontains=q) | Q(director__icontains=q))
    if genre_id:
        movies = movies.filter(genres__id=genre_id)

    if sort == 'year':
        movies = movies.order_by('-release_year')
    elif sort == 'rating':
        movies = movies.annotate(avg_rating=Avg('ratings__score')).order_by('-avg_rating')
    else:
        movies = movies.order_by('title')

    user_ratings = {r.movie_id: r.score for r in request.user.ratings.all()}
    watchlist_ids = set(request.user.watchlist.values_list('movie_id', flat=True))
    genres = Genre.objects.all().order_by('name')

    return render(request, 'movies/movie_list.html', {
        'movies': movies,
        'user_ratings': user_ratings,
        'watchlist_ids': watchlist_ids,
        'genres': genres,
        'query': q,
        'selected_genre': genre_id,
        'sort': sort,
    })


@login_required
def movie_detail(request, pk):
    """Movie detail page with similar movies."""
    movie = get_object_or_404(Movie.objects.prefetch_related('genres'), pk=pk)
    similar = get_similar_movies(movie, top_n=6)

    user_rating = None
    try:
        user_rating = Rating.objects.get(user=request.user, movie=movie)
    except Rating.DoesNotExist:
        pass

    in_watchlist = Watchlist.objects.filter(user=request.user, movie=movie).exists()
    all_ratings = movie.ratings.select_related('user').order_by('-created_at')[:10]
    user_ratings_map = {r.movie_id: r.score for r in request.user.ratings.all()}
    watchlist_ids = set(request.user.watchlist.values_list('movie_id', flat=True))

    # Convert YouTube URL to nocookie embed format
    trailer_embed_url = None
    trailer_video_id = None
    if movie.trailer_url:
        url = movie.trailer_url.strip()
        if '/watch?v=' in url:
            trailer_video_id = url.split('v=')[1].split('&')[0]
        elif '/embed/' in url:
            trailer_video_id = url.split('/embed/')[1].split('?')[0]
        elif 'youtu.be/' in url:
            trailer_video_id = url.split('youtu.be/')[1].split('?')[0]
        if trailer_video_id:
            trailer_embed_url = f'https://www.youtube-nocookie.com/embed/{trailer_video_id}'
        else:
            trailer_embed_url = url

    return render(request, 'movies/movie_detail.html', {
        'movie': movie,
        'similar_movies': similar,
        'user_rating': user_rating,
        'in_watchlist': in_watchlist,
        'all_ratings': all_ratings,
        'user_ratings_map': user_ratings_map,
        'watchlist_ids': watchlist_ids,
        'trailer_embed_url': trailer_embed_url,
        'trailer_video_id': trailer_video_id,
    })


@login_required
@require_POST
def add_comment(request, pk):
    """Submit or update a comment on a movie (requires an existing rating)."""
    movie = get_object_or_404(Movie, pk=pk)
    comment_text = request.POST.get('comment', '').strip()

    rating, created = Rating.objects.get_or_create(
        user=request.user, movie=movie,
        defaults={'score': 1, 'comment': comment_text}
    )
    if not created:
        rating.comment = comment_text
        rating.save(update_fields=['comment', 'updated_at'])

    return redirect('movie_detail', pk=pk)


@login_required
@require_POST
def rate_movie(request, pk):
    """AJAX endpoint to rate a movie."""
    movie = get_object_or_404(Movie, pk=pk)
    score = int(request.POST.get('score', 0))

    if not (1 <= score <= 5):
        return JsonResponse({'error': 'Invalid score'}, status=400)

    rating, created = Rating.objects.update_or_create(
        user=request.user, movie=movie,
        defaults={'score': score}
    )

    return JsonResponse({
        'score': score,
        'avg_rating': movie.average_rating(),
        'rating_count': movie.rating_count(),
        'created': created,
    })


@login_required
@require_POST
def toggle_watchlist(request, pk):
    """AJAX endpoint to add/remove from watchlist."""
    movie = get_object_or_404(Movie, pk=pk)
    obj, created = Watchlist.objects.get_or_create(user=request.user, movie=movie)
    if not created:
        obj.delete()
        in_watchlist = False
    else:
        in_watchlist = True

    return JsonResponse({'in_watchlist': in_watchlist})


@login_required
def watchlist(request):
    """User's watchlist."""
    items = (
        request.user.watchlist
        .select_related('movie')
        .prefetch_related('movie__genres')
        .order_by('-added_at')
    )
    user_ratings = {r.movie_id: r.score for r in request.user.ratings.all()}
    watchlist_ids = set(request.user.watchlist.values_list('movie_id', flat=True))

    return render(request, 'movies/watchlist.html', {
        'items': items,
        'user_ratings': user_ratings,
        'watchlist_ids': watchlist_ids,
    })


@login_required
def profile(request):
    """User profile with rating history."""
    ratings = (
        request.user.ratings
        .select_related('movie')
        .prefetch_related('movie__genres')
        .order_by('-updated_at')
    )
    watchlist_count = request.user.watchlist.count()

    rating_dist = {i: 0 for i in range(1, 6)}
    for r in ratings:
        rating_dist[r.score] += 1

    return render(request, 'movies/profile.html', {
        'ratings': ratings,
        'watchlist_count': watchlist_count,
        'rating_dist': rating_dist,
        'total_ratings': ratings.count(),
    })


def register(request):
    """User registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'movies/register.html', {'form': form})

def landing(request):
    """Landing page with user/admin login choice."""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'movies/landing.html')
