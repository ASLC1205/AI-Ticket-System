from rest_framework import serializers
from apps.accounts.models import User


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            'id',
            'username',
            'email',
            'phone',
            'role',
            'is_active',
            'date_joined',
        ]

        read_only_fields = [
            'id',
            'email',
            'role',
            'is_active',
            'date_joined',
        ]