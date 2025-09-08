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

        if response.status_code in [200, 201]:
            # ✅ Store email in session
            request.session["email"] = email
            messages.success(request, "Registration successful. OTP sent to email.")
            return redirect("verify_otp_view")
        else:
            messages.error(request, response.json().get("error") or "Registration failed")

    return render(request, "auth/register.html")

def verify_otp_view(request):
    email = request.session.get("email")   # ✅ Fetch from session

    if not email:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register_view")

    if request.method == "POST":
        otp = request.POST.get("otp")

        payload = {
            "email": email,
            "otp": otp
        }

        response = requests.post(f"{API_BASE_URL}verify-otp/", json=payload)

        if response.status_code == 200:
            messages.success(request, "OTP verified. You can now log in.")
            return redirect("login_view")
        else:
            messages.error(request, response.json().get("error") or "OTP verification failed")

    return render(request, "auth/verify_otp.html", {"email": email})


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
            resp = redirect("home-view")

            # store tokens in cookies (HttpOnly = safer)
            resp.set_cookie("access", data['access'], httponly=True, secure=True, samesite="Lax")
            resp.set_cookie("refresh", data['refresh'], httponly=True, secure=True, samesite="Lax")
            resp.set_cookie("user_data", data['user_data'], httponly=False, secure=True, samesite="Lax")  

            messages.success(request, "Login successful")
            return resp
        else:
            messages.error(request, response.json().get("message") or "Login failed")

    return render(request, "auth/login.html")


def home_view(request):
        access_token = request.COOKIES.get('access')
        if not access_token:
            return redirect("login_view")
        response1 = requests.get(f"{API_BASE_URL}profile/", headers={"Authorization": f"Bearer {access_token}"})
        response2 = requests.get(f"{API_BASE_URL}api/getbooks", headers={"Authorization": f"Bearer {access_token}"})

        if response1.status_code == 200 and response2.status_code == 200:
            user_data = response1.json()
            books_data = response2.json()
            return render(request, "auth/home.html", {"user": user_data, "books": books_data})
        else:
            messages.error(request, "Failed to retrieve user profile.")
            return redirect("login_view")


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
