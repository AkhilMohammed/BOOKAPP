from django.urls import path
from .views import RegistrationView, VerifyOTPView,\
    LoginView,UserProfileView,LogoutView,NestedDataGenerationView
from . import django_views as views



urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='loginapi'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register-view/', views.register_view, name='register'),
    path('verify-otp-view/', views.verify_otp_view, name='verify_otp_view'),
    path('login-view/', views.login_view, name='login_view'),
    path('logout-view/', views.logout_view, name='logout'),
    path('profile-view/', views.profile_view, name='profile'),
    path('home-view/', views.home_view, name="home-view"),
    path('generate-synthetic/', NestedDataGenerationView.as_view(), name='generate-synthetic'),
]