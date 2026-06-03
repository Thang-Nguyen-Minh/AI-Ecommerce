"""payment_service URL Configuration"""
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    from django.db import connection
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    return JsonResponse({'service': 'payment-service', 'status': 'ok' if db_ok else 'degraded'})


urlpatterns = [
    path('payment/health/', health_check, name='health'),
    path('', include('payments.urls')),
]
