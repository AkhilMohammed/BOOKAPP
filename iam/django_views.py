# django_views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
import requests
from django.conf import settings

API_BASE_URL = settings.API_BASE_URL  # e.g., http://localhost:8000/api/


def register_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password")
        user_name = request.POST.get("user_name")   

        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
            "user_name": user_name
        }

        response = requests.post(f"{API_BASE_URL}register/", json=payload)

        if response.status_code == 201:
            messages.success(request, "Registration successful. OTP sent to email.")
            return redirect("verify_otp_view")
        elif response.status_code == 200:
            messages.info(request, response.json().get("message") or "User already exists. OTP sent again.")
            return redirect("verify_otp_view")
        else:
            messages.error(request, response.json().get("error") or "Registration failed")

    return render(request, "auth/register.html")


def verify_otp_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")

        payload = {
            "email": email,
            "otp": otp
        }

        response = requests.post(f"{API_BASE_URL}verify-otp/", json=payload)

        if response.status_code == 200:
            messages.success(request, "OTP verified. You can now log in.")
            return redirect("login-view")
        else:
            messages.error(request, response.json().get("error") or "OTP verification failed")

    return render(request, "auth/verify_otp.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        payload = {
            "email": email,
            "password": password
        }

        response = requests.post(f"{API_BASE_URL}login/", json=payload)

        if response.status_code == 200:
            data = response.json().get("data")
            request.session['access'] = data['access']
            request.session['refresh'] = data['refresh']
            request.session['user_data'] = data['user_data']
            messages.success(request, "Login successful")
            return redirect("profile-view")
        else:
            messages.error(request, response.json().get("message") or "Login failed")

    return render(request, "auth/login.html")


def profile_view(request):
    access_token = request.session.get('access')
    if not access_token:
        return redirect("login-view")

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{API_BASE_URL}profile/", headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        return render(request, "auth/profile.html", {"user": user_data})
    else:
        messages.error(request, "Session expired. Please login again.")
        return redirect("login-view")


def logout_view(request):
    refresh_token = request.session.get('refresh')
    if refresh_token:
        requests.post(f"{API_BASE_URL}logout/", json={"refresh": refresh_token})
    logout(request)
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect("login-view")
