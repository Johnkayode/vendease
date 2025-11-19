from django.db import models


class Product(models.Model):
    seller = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    cost = models.PositiveIntegerField(default=0)
    amount_available = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        indexes = [
            models.Index(fields=['seller']),
            models.Index(fields=['name']),
        ]