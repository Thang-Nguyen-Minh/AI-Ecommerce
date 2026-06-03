"""product_service URL Configuration"""
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse({"status": "ok", "service": "product-service"})


urlpatterns = [
    path("products/health/", health_check, name="health"),
    path("", include("products.urls")),
]
