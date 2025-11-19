from django.urls import path, include

urlpatterns = [
    path("api/users/", include("api.apps.users.urls")),
    path("api/products/", include("api.apps.products.urls")),
]
