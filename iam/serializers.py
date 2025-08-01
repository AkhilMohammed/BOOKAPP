from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    otp = serializers.CharField(read_only=True, required=False)
    user_name = serializers.CharField(required=True, max_length=30)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'otp', 'user_name']

    def validate_email(self, value):
        if User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False  # User is inactive until OTP verification
        user.save()
        return user
    
class OTPVerifyRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    