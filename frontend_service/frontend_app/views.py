import logging

import requests

from django.core.cache import cache
from django.shortcuts import render, redirect
from django.urls import reverse

from frontend_app.utils import try_requests, token_auth
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
            response = redirect('login')  # Redirect to login
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

        logger.debug(f'Send request to: {get_users_login_url()}')
        users_response = try_requests(requests.post, get_users_login_url(), data=data)

        if users_response.get('status') == 200:
            response_json = users_response.get('response').json()

            access = response_json.get('access')
            refresh = response_json.get('refresh')
            user_data = response_json.get('user')
            cache.set(access, user_data, timeout=900)

            response = redirect('desktop')
            response.set_cookie(
                key='uat',
                value=access,
                max_age=900,
                secure=True,
                httponly=True,
                samesite='Lax',
            )
            response.set_cookie(
                key='urt',
                value=refresh,
                max_age=3600 * 24,
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


def logout(request):
    if request.method == 'GET':
        access = request.COOKIES.get('uat')
        cache.delete(access)
        response = redirect('login')
        response.delete_cookie('uat')
        response.delete_cookie('urt')
        return response


@token_auth
def desktop(request, user=None):
    context = {
        'title': 'Desktop',
    }
    if request.method == 'GET':
        context['user'] = user
        response = render(request, 'frontend_app/desktop.html', context)
        return response


def rating(request):
    context = {
        'title': 'Rating',
    }
    if request.method == 'GET':
        url = get_users_get_rating_url()
        method = requests.get
        rating_response = try_requests(method, url)
        context['users'] = rating_response.get('response').json().get('users')
        response = render(request, 'frontend_app/rating.html', context=context)
        return response


def profile(request, username):
    context = {
        'title': 'Profile',
    }
    if request.method == 'GET':
        url = get_users_get_profile_url()
        method = requests.get
        data = {'username': username}
        profile_response = try_requests(method, url, data=data)
        context['user'] = profile_response.get('response').json().get('profile')
        response = render(request, 'frontend_app/profile.html', context=context)
        return response


@token_auth
def global_lobby(request, user=None):
    context = {
        'title': 'Game lobby',
    }
    if request.method == 'GET':
        context['user'] = user
        response = render(request, 'frontend_app/global_lobby.html', context)
        return response


@token_auth
def game_lobby(request, room_token, user=None):
    context = {
        'title': 'Game lobby',
    }
    if request.method == 'GET':
        context['user'] = user
        context['room_token'] = room_token
        response = render(request, 'frontend_app/game_lobby.html', context)
        return response
