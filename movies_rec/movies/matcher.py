from django.contrib.auth.models import User
from .models import Rating, Match


def find_and_create_matches(user):
    """
    After a user rates a movie, check all other users.
    If they share ≥3 movies rated with the exact same score, create a Match.
    """
    my_ratings = {r.movie_id: r.score for r in Rating.objects.filter(user=user)}
    if len(my_ratings) < 3:
        return

    for other in User.objects.exclude(pk=user.pk):
        # Skip if match already exists (either direction)
        u1, u2 = (user, other) if user.pk < other.pk else (other, user)
        if Match.objects.filter(user1=u1, user2=u2).exists():
            continue

        other_ratings = {r.movie_id: r.score for r in Rating.objects.filter(user=other)}
        shared = sum(
            1 for movie_id, score in my_ratings.items()
            if other_ratings.get(movie_id) == score
        )
        if shared >= 3:
            Match.objects.get_or_create(user1=u1, user2=u2)
