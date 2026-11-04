from django.urls import path

from .views import (
    CustomerProfileAPIView,
    CustomerInfoAPIView,
    CustomerListAPIView,
    CustomerDetailAPIView,
    CustomerStatusAPIView,
)

urlpatterns = [

    # Customer profile
    path(
        'profile/',
        CustomerProfileAPIView.as_view(),
        name='customer-profile'
    ),

    # Customer information
    path(
        'info/',
        CustomerInfoAPIView.as_view(),
        name='customer-info'
    ),

    # Admin customer management
    path(
        'admin/',
        CustomerListAPIView.as_view(),
        name='customer-list'
    ),

    path(
        'admin/<int:pk>/',
        CustomerDetailAPIView.as_view(),
        name='customer-detail'
    ),

    path(
        'admin/<int:pk>/status/',
        CustomerStatusAPIView.as_view(),
        name='customer-status'
    ),
]