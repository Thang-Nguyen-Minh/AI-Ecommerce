from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    from django.db import connection
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    return JsonResponse({'service': 'order-service', 'status': 'ok' if db_ok else 'degraded'})


urlpatterns = [
    path('orders/health/', health_check, name='health'),
    path('', include('orders.urls')),
]
