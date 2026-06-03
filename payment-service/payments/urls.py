from django.urls import path
from . import views

urlpatterns = [
    path('payment/pay',    views.pay,            name='payment-pay'),
    path('payment/status', views.payment_status, name='payment-status'),
]
