from django.db.models import Q
from .models import Match, Message


def unread_matches(request):
    if not request.user.is_authenticated:
        return {}
    count = Message.objects.filter(
        match__in=Match.objects.filter(Q(user1=request.user) | Q(user2=request.user)),
        read=False,
    ).exclude(sender=request.user).count()
    return {'unread_matches': count}
