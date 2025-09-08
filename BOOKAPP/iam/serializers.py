from rest_framework import serializers
from .models import User, profile
'''
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
'''  



class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    otp = serializers.CharField( required=False)
    user_name = serializers.CharField(required=True, max_length=30)
    otp_expiry = serializers.DateTimeField( required=False)
    user_type = serializers.ChoiceField(choices=[
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('delivery', 'Delivery'),
        ('superadmin', 'SuperAdmin'),
    ], default='customer')

    class Meta:
        model = User
        fields = ['id','email' ,'password', 'first_name', 'last_name', 'otp','otp_expiry', 'user_name','user_type']
    
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



class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    D_no = serializers.CharField(max_length=255, required=False)
    street_name = serializers.CharField(max_length=255, required=False)
    city = serializers.CharField(max_length=100, required=False)
    state = serializers.CharField(max_length=100, required=False)
    country = serializers.CharField(max_length=100, required=False)
    zip_code = serializers.CharField(max_length=20, required=False)
    phone_number = serializers.CharField(max_length=15, required=False)

    class Meta:
        model = profile
        fields = ['user', 'D_no', 'street_name', 'city', 'state', 'country', 'zip_code', 'phone_number']

    def create(self, validated_data):
        user = self.context['request'].user
        profile_data = validated_data.copy()
        profile_data['user'] = user
        profile_instance = profile.objects.create(**profile_data)
        return profile_instance


class SyntheticGenSerializer(serializers.Serializer):
    model = serializers.CharField(help_text="app_label.ModelName e.g. store.Book")
    count = serializers.IntegerField(min_value=1, max_value=10_000, required=False, default=100)
    csv = serializers.FileField(required=False, allow_null=True, help_text="Optional CSV with sample rows")
    strategy = serializers.ChoiceField(
        choices=["cover_combinations", "randomized", "balanced"], default="balanced"
    )
    
