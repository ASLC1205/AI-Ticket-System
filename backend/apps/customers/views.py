from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from .serializers import CustomerSerializer
from .permissions import IsCustomer, IsAdmin


# 1. View and update own customer profile
class CustomerProfileAPIView(generics.RetrieveUpdateAPIView):

    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_object(self):
        return self.request.user


# 2. View and update own customer information
class CustomerInfoAPIView(CustomerProfileAPIView):
    pass


# 3. Admin: List all customers and search customers
class CustomerListAPIView(generics.ListAPIView):

    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        queryset = User.objects.filter(role='CUSTOMER')

        search_query = self.request.query_params.get('q')

        if search_query:
            queryset = queryset.filter(
                username__icontains=search_query
            ) | queryset.filter(
                email__icontains=search_query
            )

        return queryset.order_by('-date_joined')


# 4. Admin: View a particular customer
class CustomerDetailAPIView(generics.RetrieveAPIView):

    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return User.objects.filter(role='CUSTOMER')


# 5. Admin: Activate or deactivate a customer
class CustomerStatusAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):

        customer = get_object_or_404(
            User,
            pk=pk,
            role='CUSTOMER'
        )

        is_active = request.data.get('is_active')

        if not isinstance(is_active, bool):
            return Response(
                {
                    'error': 'is_active must be true or false.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        customer.is_active = is_active
        customer.save(update_fields=['is_active'])

        return Response(
            {
                'message': 'Customer account status updated.',
                'customer_id': customer.id,
                'is_active': customer.is_active
            },
            status=status.HTTP_200_OK
        )