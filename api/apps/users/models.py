from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class Role(models.TextChoices):
    BUYER = ('buyer', 'Buyer')
    SELLER = ('seller', 'Seller')


class User(AbstractUser):
    role = models.CharField(max_length=10, choices=Role.choices, null=False, blank=False)
    deposit = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Deposit amount (cents)"
    )

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def reset_deposit(self):
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=self.pk)
            user.deposit = 0
            user.save(update_fields=['deposit'])
        return user.deposit


class ActiveSessionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(expiry_date__gt=timezone.now())


class ActiveSession(models.Model):
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name='active_sessions'
    )
    session_id = models.UUIDField(unique=True, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # other details
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    expiry_date = models.DateTimeField(null=True, blank=True)

    objects = ActiveSessionManager()
    all_objects = models.Manager()
    
    class Meta:
        db_table = 'active_sessions'
        indexes = [
            models.Index(fields=['user', 'session_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.session_id}"