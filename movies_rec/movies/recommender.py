"""
Collaborative Filtering Recommendation Engine
Uses User-Based CF with Pearson Correlation + Item-Based CF fallback
"""
import math
from collections import defaultdict
from .models import Rating, Movie


def get_user_ratings_dict(user_id):
    """Returns {movie_id: score} for a given user."""
    return {r.movie_id: r.score for r in Rating.objects.filter(user_id=user_id)}


def get_all_ratings():
    """Returns {user_id: {movie_id: score}} for all users."""
    data = defaultdict(dict)
    for r in Rating.objects.all().values('user_id', 'movie_id', 'score'):
        data[r['user_id']][r['movie_id']] = r['score']
    return dict(data)


def pearson_correlation(ratings_a, ratings_b):
    """Compute Pearson correlation between two users' ratings on shared movies."""
    shared = set(ratings_a.keys()) & set(ratings_b.keys())
    n = len(shared)
    if n < 2:
        return 0

    sum_a = sum(ratings_a[m] for m in shared)
    sum_b = sum(ratings_b[m] for m in shared)
    sum_sq_a = sum(ratings_a[m] ** 2 for m in shared)
    sum_sq_b = sum(ratings_b[m] ** 2 for m in shared)
    sum_ab = sum(ratings_a[m] * ratings_b[m] for m in shared)

    num = sum_ab - (sum_a * sum_b / n)
    den = math.sqrt(
        max(0, (sum_sq_a - sum_a ** 2 / n)) *
        max(0, (sum_sq_b - sum_b ** 2 / n))
    )
    return num / den if den != 0 else 0


def cosine_similarity(ratings_a, ratings_b):
    """Cosine similarity fallback."""
    shared = set(ratings_a.keys()) & set(ratings_b.keys())
    if not shared:
        return 0
    dot = sum(ratings_a[m] * ratings_b[m] for m in shared)
    mag_a = math.sqrt(sum(v ** 2 for v in ratings_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in ratings_b.values()))
    return dot / (mag_a * mag_b) if mag_a * mag_b else 0


def get_similar_users(target_user_id, all_ratings, top_n=10):
    """Find the most similar users to the target user."""
    target_ratings = all_ratings.get(target_user_id, {})
    if not target_ratings:
        return []

    similarities = []
    for user_id, ratings in all_ratings.items():
        if user_id == target_user_id:
            continue
        sim = pearson_correlation(target_ratings, ratings)
        if sim > 0:
            similarities.append((user_id, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_n]


def user_based_recommendations(target_user_id, top_n=10):
    """
    User-Based Collaborative Filtering.
    Predicts ratings for unseen movies using weighted average from similar users.
    """
    all_ratings = get_all_ratings()
    target_ratings = all_ratings.get(target_user_id, {})
    similar_users = get_similar_users(target_user_id, all_ratings)

    if not similar_users:
        return item_based_recommendations(target_user_id, top_n)

    # Weighted sum of ratings from similar users for movies target hasn't seen
    score_sum = defaultdict(float)
    sim_sum = defaultdict(float)

    for user_id, similarity in similar_users:
        for movie_id, score in all_ratings[user_id].items():
            if movie_id not in target_ratings:
                score_sum[movie_id] += similarity * score
                sim_sum[movie_id] += abs(similarity)

    predicted = []
    for movie_id, total in score_sum.items():
        if sim_sum[movie_id] > 0:
            predicted_score = total / sim_sum[movie_id]
            predicted.append((movie_id, round(predicted_score, 2)))

    predicted.sort(key=lambda x: x[1], reverse=True)
    movie_ids = [m[0] for m in predicted[:top_n]]

    # Preserve ordering
    movies = list(Movie.objects.filter(pk__in=movie_ids).prefetch_related('genres'))
    id_to_score = dict(predicted[:top_n])
    movies.sort(key=lambda m: id_to_score.get(m.pk, 0), reverse=True)
    return movies, [(m, id_to_score.get(m.pk, 0)) for m in movies]


def item_based_recommendations(target_user_id, top_n=10):
    """
    Item-Based CF fallback using movie-movie similarity.
    """
    all_ratings = get_all_ratings()
    target_ratings = all_ratings.get(target_user_id, {})

    if not target_ratings:
        # Cold start: return top-rated movies
        rated_movie_ids = list(target_ratings.keys())
        movies = Movie.objects.exclude(pk__in=rated_movie_ids).prefetch_related('genres')
        top_movies = sorted(movies, key=lambda m: m.average_rating(), reverse=True)[:top_n]
        return top_movies, [(m, m.average_rating()) for m in top_movies]

    # Build movie → {user: rating} matrix
    movie_ratings = defaultdict(dict)
    for uid, ratings in all_ratings.items():
        for mid, score in ratings.items():
            movie_ratings[mid][uid] = score

    # For each movie the user has rated, find similar unrated movies
    score_sum = defaultdict(float)
    sim_sum = defaultdict(float)

    for rated_movie, user_score in target_ratings.items():
        for candidate_movie, candidate_ratings in movie_ratings.items():
            if candidate_movie in target_ratings:
                continue
            sim = cosine_similarity(movie_ratings[rated_movie], candidate_ratings)
            if sim > 0:
                score_sum[candidate_movie] += sim * user_score
                sim_sum[candidate_movie] += sim

    predicted = [
        (mid, score_sum[mid] / sim_sum[mid])
        for mid in score_sum if sim_sum[mid] > 0
    ]
    predicted.sort(key=lambda x: x[1], reverse=True)
    movie_ids = [m[0] for m in predicted[:top_n]]
    movies = list(Movie.objects.filter(pk__in=movie_ids).prefetch_related('genres'))
    id_to_score = dict(predicted[:top_n])
    movies.sort(key=lambda m: id_to_score.get(m.pk, 0), reverse=True)
    return movies, [(m, round(id_to_score.get(m.pk, 0), 2)) for m in movies]


def get_recommendations(user, top_n=10):
    """Main entry point: returns (movies, scored_movies) tuple."""
    movies, scored = user_based_recommendations(user.id, top_n)
    return movies, scored


def get_similar_movies(movie, top_n=6):
    """Find movies similar to a given movie using item-based CF."""
    all_ratings = get_all_ratings()
    movie_ratings = defaultdict(dict)
    for uid, ratings in all_ratings.items():
        for mid, score in ratings.items():
            movie_ratings[mid][uid] = score

    if movie.pk not in movie_ratings:
        # Genre fallback
        genre_ids = movie.genres.values_list('id', flat=True)
        return Movie.objects.filter(genres__in=genre_ids).exclude(pk=movie.pk).distinct()[:top_n]

    sims = []
    for other_id, other_ratings in movie_ratings.items():
        if other_id == movie.pk:
            continue
        sim = cosine_similarity(movie_ratings[movie.pk], other_ratings)
        if sim > 0:
            sims.append((other_id, sim))

    sims.sort(key=lambda x: x[1], reverse=True)
    top_ids = [s[0] for s in sims[:top_n]]
    similar = list(Movie.objects.filter(pk__in=top_ids).prefetch_related('genres'))
    id_to_sim = dict(sims[:top_n])
    similar.sort(key=lambda m: id_to_sim.get(m.pk, 0), reverse=True)
    return similar
