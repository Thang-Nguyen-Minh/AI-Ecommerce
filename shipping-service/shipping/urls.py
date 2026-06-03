from django.urls import path
from . import views

urlpatterns = [
    path('shipping/create',  views.create_shipment, name='shipping-create'),
    path('shipping/status',  views.shipment_status, name='shipping-status'),
    path('shipping/<int:pk>', views.update_shipment, name='shipping-update'),
]
