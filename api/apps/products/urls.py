from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.apps.products.views import ProductViewSet, BuyProductView

router = DefaultRouter()
router.register('', ProductViewSet, basename='product')

urlpatterns = [
    path('buy/', BuyProductView.as_view(), name='buy_product'),
] + router.urls