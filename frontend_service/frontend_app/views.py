import logging

import requests

from django.core.cache import cache
from django.shortcuts import render, redirect
from django.urls import reverse

from frontend_app.utils import try_requests
from frontend_service.microservices.users_api import *


logger = logging.getLogger('game_server')


def home(request):
    """
    Home page view that returns a simple greeting message.
    """
    if request.method == 'GET':
        context = {
            'title': 'Home',
        }
        response = render(request, 'frontend_app/home.html', context)
        return response


def registration(request):
    context = {'title': 'Registration'}  # Context for the registration template

    # Handle GET request: render the registration form
    if request.method == 'GET':
        return render(request, 'frontend_app/registration.html', context)

    # Handle POST request: send user data to the backend for registration
    if request.method == 'POST':
        user_data = request.POST  # Get user data from the form

        logger.debug(get_users_registration_url())
        users_response = try_requests(requests.post, get_users_registration_url(), data=user_data)

        if users_response.get('status') == 201:
            success_url = reverse('login')  # Get login url
            response = redirect(success_url)  # Redirect to login
            response.status_code = 201  # Change status code to 201
            return response

        else:
            context['errors'] = users_response.get('errors')
            response = render(request, 'frontend_app/registration.html', context)
            response.status_code = users_response.get('status')
            return response


def login(request):
    context = {
        'title': 'Login',
    }
    if request.method == 'GET':
        response = render(request, 'frontend_app/login.html', context)
        return response

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        data = {'username': username, 'password': password}

        users_response = try_requests(requests.post, get_users_login_url(), data=data)

        if users_response.get('status') == 200:
            response_json = users_response.get('response').json()

            access = response_json.get('access')
            refresh = response_json.get('refresh')
            user_data = response_json.get('user')
            cache.set(refresh, user_data, timeout=3600)

            success_url = reverse('desktop')
            response = redirect(success_url)
            response.set_cookie(
                key='uat',
                value=access,
                secure=True,
                httponly=True,
                samesite='Lax',
            )
            response.set_cookie(
                key='urt',
                value=refresh,
                secure=True,
                httponly=True,
                samesite='Lax',
            )
            return response

        else:
            context['errors'] = users_response.get('errors')
            response = render(request, 'frontend_app/login.html', context)
            response.status_code = users_response.get('status')
            return response


def desktop(request):
    context = {
        'title': 'Desktop',
    }
    if request.method == 'GET':
        refresh = request.COOKIES.get('urt')
        user = cache.get(refresh)
        context['user'] = user
        response = render(request, 'frontend_app/desktop.html', context)
        return response


def global_lobby(request):
    context = {
        'title': 'Game lobby',
    }
    if request.method == 'GET':
        refresh = request.COOKIES.get('urt')
        user = cache.get(refresh)
        context['user'] = user
        response = render(request, 'frontend_app/global_lobby.html', context)
        return response


def game_lobby(request, room_token):
    context = {
        'title': 'Game lobby',
    }
    if request.method == 'GET':
        refresh = request.COOKIES.get('urt')
        user = cache.get(refresh)
        context['user'] = user
        context['room_token'] = room_token
        response = render(request, 'frontend_app/game_lobby.html', context)
        return response
