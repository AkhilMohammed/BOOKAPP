from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response 
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from iam.models import User
from .serializers import UserSerializer,OTPVerifyRequestSerializer, LoginSerializer
from django.contrib.auth import get_user_model
from django.conf import settings
import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
logger = logging.getLogger(__name__)
from rest_framework_simplejwt.tokens import RefreshToken,TokenError,AccessToken
from django.contrib.auth import authenticate


#User = get_user_model()

def generate_otp():
    """
    Generates a random 6-digit OTP.
    """
    return str(random.randint(100000, 999999))  

class RegistrationView(APIView):
    """
    Handles user registration.
    """
    @swagger_auto_schema(request_body=UserSerializer, responses={201: UserSerializer})
    def post(self, request, *args, **kwargs):
        try:
            email = request.data.get('email')
            if not email:
                return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
            existing_user = User.objects.get(email=email)
            if existing_user.is_active:
                return Response({"error": "User with this email already exists and is active."}, status=status.HTTP_400_BAD_REQUEST)
            elif not existing_user.is_active:
                logger.debug("User exists but is not active, sending OTP again.")
                otp = generate_otp()
                existing_user.otp = otp
                existing_user.otp_expiry = timezone.now() + timedelta(minutes=5)
                existing_user.save()
                send_mail(
                    'Your OTP for Book Online Sales',
                    f'Your OTP is {otp}. It is valid for 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [request.data.get('email')],
                    fail_silently=False,
                )
                return Response({"message": "User with this email already exists. A OTP has been sent again."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            try:
                otp = generate_otp()
                request.data['otp'] = otp
                request.data['otp_expiry'] = timezone.now() + timedelta(minutes=5)
                serializer = UserSerializer(data=request.data)
                if serializer.is_valid():
                    user = serializer.save()
                    send_mail(
                        'Your OTP for Book Online Sales',
                        f'Your OTP is {otp}. It is valid for 5 minutes.',
                        settings.DEFAULT_FROM_EMAIL,
                        [request.data.get('email')],
                        fail_silently=False,
                    )
                    logger.debug("User created successfully: %s", user)
                    return Response({"user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error("Error during registration: %s", e)
                return Response({"error": "An error occurred during registration." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       

class VerifyOTPView(APIView):
    """
    Handles OTP verification.
    """
    @swagger_auto_schema(
        request_body=OTPVerifyRequestSerializer,
        responses={
            200: openapi.Response('OTP verified successfully.'),
            400: openapi.Response('Invalid or expired OTP.'),
            404: openapi.Response('User not found.')
        }
    )
    def post(self, request, *args, **kwargs):
        logger.debug("Received OTP verification request: %s", request.data) 
        serializer = OTPVerifyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        try:
            logger.debug("Attempting to verify OTP for user: %s", email)
            user_list = User.objects.all()
            logger.debug("*****************************")
            logger.debug("Total users in database: %d", user_list.count(),user_list)
            user = User.objects.get(email=email)
            logger.debug("User found: %s", user)
            if user.otp == otp:
                if timezone.now() <= user.otp_expiry:
                    user.is_active = True
                    user.otp = None  # Clear OTP after successful verification
                    user.save(update_fields=['is_active', 'otp'])
                    return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class LoginView(APIView):
    """
    Handles user login.
    """

    @swagger_auto_schema(request_body=LoginSerializer, responses={200: UserSerializer})
    def post(self, request, *args, **kwargs):
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                logger.debug("Attempting to authenticate user: %s", serializer.validated_data['email'])
                user = authenticate(request, email=request.data['email'], password=request.data['password'])
                logger.debug("User authentication result: %s", user)
                if user :
                    refresh = RefreshToken.for_user(user)
                    payload_data = {
                            'email' : user.email,
                            'userName' : user.user_name,
                            'full_name' : ' '.join([user.first_name, user.last_name]).strip() if user.first_name or user.last_name else '',
                            'user_id' : user.id
                    }
                    refresh.payload.update(payload_data)

                    return Response({'data':{'refresh':str(refresh),'access':str(refresh.access_token),\
                        'user_data':payload_data}},status=status.HTTP_200_OK)
                else:
                    logger.warning("Invalid credentials for user: %s", serializer.validated_data['email'])
                    return Response({"message": "Invalid credentials or user is not active."}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Error during login: %s", e)
            return Response({"error": "An error occurred during login." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   


class UserProfileView(APIView):
    """
    Handles user profile retrieval.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: UserSerializer})
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error retrieving user profile: %s", e)
            return Response({"error": "An error occurred while retrieving the user profile." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

class LogoutView(APIView):
    """
    Handles user logout.
    """
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
            },
            required=['refresh'],
        ),
        responses={204: "No Content", 400: "Invalid token"}
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)    
        try:
            token = RefreshToken(refresh_token)
            # Blacklist the token
            token.blacklist()
            # Perform logout actions (e.g., blacklist tokens)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TokenError as e:
            logger.warning("Invalid refresh token provided for logout.")
            return Response({"error": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Error during logout: %s", e)
            return Response({"error": "An error occurred during logout." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
