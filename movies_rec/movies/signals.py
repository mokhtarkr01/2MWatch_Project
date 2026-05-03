from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Rating, AdminAlert


@receiver(post_save, sender=Rating)
def alert_on_rating(sender, instance, created, **kwargs):
    if created:
        AdminAlert.objects.create(
            alert_type='rating',
            message=f"{instance.user.username} rated \"{instance.movie.title}\" {instance.score}★",
        )


@receiver(post_save, sender=User)
def alert_on_register(sender, instance, created, **kwargs):
    if created:
        AdminAlert.objects.create(
            alert_type='register',
            message=f"New user registered: {instance.username}",
        )
