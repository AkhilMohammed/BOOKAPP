from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response 
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from iam.models import User,profile
from .serializers import UserSerializer,OTPVerifyRequestSerializer, LoginSerializer,UserProfileSerializer
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
from iam.permissions import IsAdminUser
from django.apps import apps
import pandas as pd
from .serializers import SyntheticGenSerializer
from iam.agentic_ai.generator import SynthGenerator


from .tasks import generate_and_insert_nested


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
                existing_user.password = request.data.get('password') 
                existing_user.user_name = request.data.get('user_name') 
                existing_user.first_name = request.data.get('first_name')  # Keep the existing first_name
                existing_user.last_name = request.data.get('last_name')  # Keep the existing last_name
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
                logger.debug(f"Generated OTP {otp} with expiry{request.data['otp_expiry']}")
                serializer = UserSerializer(data=request.data)
                if serializer.is_valid():
                    logger.debug(f"Serializer is valid for user {serializer.validated_data}")
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
            user = User.objects.get(email=email)
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


       
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            current_user = User.objects.get(email=user.email)
            user_data = {
                'id': current_user.id,
                'email':current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'username': current_user.username,
                'user_type': current_user.user_type}
            return Response(user_data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            logger.error(f"User with email {request.user.email} does not exist.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving user profile: {str(e)}")
            return Response({"error": "An error occurred while retrieving the user profile." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, *args, **kwargs):
        try:
            user = request.user
            current_user = User.objects.get(email=user.email)
            for key,value in request.data.items():
                if key == "first_name":
                    current_user.first_name = value
                elif key == "last_name":
                    current_user.last_name = value
                elif key == "user_type":
                    current_user.user_type = value
                elif key == "password":
                    current_user.set_password(value)
                else:
                    return Response({"error": f"Invalid field: {key}"}, status=status.HTTP_400_BAD_REQUEST)
            current_user.save()
            user_data = {
                'id': current_user.id,
                'email': current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'user_type': current_user.user_type      
            }
            logger.info(f"User profile updated for {user.email}.")
            return Response(user_data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            logger.error(f"User with email {user.email} does not exist.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return Response({"error": "An error occurred while updating the user profile." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, *args, **kwargs):
        try:
            user = request.user
            current_user = User.objects.get(email=user.email)
            current_user.is_active = False
            current_user.save()
            logger.info(f"User {user.email} has been deactivated.")
            return Response({"message": "User account deactivated successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            logger.error(f"User with email {user.email} does not exist.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deactivating user account: {str(e)}")
            return Response({"error": "An error occurred while deactivating the user account." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            logger.debug(f"Creating profile for user {user} with data: {request.data}")
            profile_data = request.data
            profile_data['user'] = user
            logger.debug(f"Creating profile for user {user.email} with data: {profile_data}")
            serializer = UserProfileSerializer(data=profile_data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Profile created for user {user.email}.")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
            return Response({"error": "An error occurred while creating the user profile." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            profile_obj = profile.objects.get(user=user)
            profile_data = {
                'D_no': profile_obj.D_no,
                'street_name': profile_obj.street_name, 
                'city': profile_obj.city,
                'state': profile_obj.state,
                'country': profile_obj.country, 
                'zip_code': profile_obj.zip_code,
                'phone_number': profile_obj.phone_number
            }
            logger.info(f"Profile retrieved for user {user.email}.")
            return Response(profile_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error retrieving user profile: {str(e)}")
            return Response({"error": "An error occurred while retrieving the user profile." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, *args, **kwargs):
        try: 
            user = request.user
            profile_obj = profile.objects.get(user=user)
            for key, value in request.data.items():
                if hasattr(profile_obj, key):
                    setattr(profile_obj, key, value)
            profile_obj.save()
            profile_data = {
                'D_no': profile_obj.D_no,
                'street_name': profile_obj.street_name,
                'city': profile_obj.city,
                'state': profile_obj.state,
                'country': profile_obj.country,
                'zip_code': profile_obj.zip_code,
                'phone_number': profile_obj.phone_number
            }
            logger.info(f"Profile updated for user {user.email}.")
            return Response(profile_data, status=status.HTTP_200_OK)
        except profile.DoesNotExist:
            logger.error(f"Profile for user {user.email} does not exist.")
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return Response({"error": "An error occurred while updating the user profile." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UserListView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request, *args, **kwargs):
        try:
            if request.user.user_type == 'admin':
                users = User.objects.all()
                user_data = []
                for user in users:
                    user_data.append({
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'username': user.username,
                        'user_type': user.user_type,
                        'is_active': user.is_active,
                        'date_joined': user.date_joined
                    })
                    logger.debug(f"User data for {user.email}: {user_data[-1]}")
                logger.info("User list retrieved successfully.")
                return Response(user_data, status=status.HTTP_200_OK)
            return Response({"error": "You do not have permission to view this resource."}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error retrieving user list: {str(e)}")
            return Response({"error": "An error occurred while retrieving the user list." + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class GenerateSyntheticDataView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        s = SyntheticGenSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        try:
            app_label, model_name = data['model'].split('.')
            Model = apps.get_model(app_label, model_name)
        except Exception as e:
            return Response({"error": f"Invalid model name: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        df_samples  = None
        if data.get('csv'):
            try:
                df_samples = pd.read_csv(data['csv'])
            except Exception as e:
                return Response({"error": f"Invalid CSV file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        gen = SynthGenerator(Model)
        try:
            created = gen.generate_and_insert(
                count=data["count"],
                strategy=data["strategy"],
                sample_df=df_samples
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

        return Response({"inserted": created}, status=status.HTTP_201_CREATED)
    

class NestedDataGenerationView(APIView):
    def post(self, request):
        """
        {
          "models": ["books.Author","books.Book"],
          "counts": {"books.Author":5,"books.Book":50}
        }
        """
        models = request.data.get("models",[])
        counts = request.data.get("counts",{})
        task = generate_and_insert_nested.delay(models, counts)
        return Response({"task_id": task.id, "message":"Nested data generation started"})
