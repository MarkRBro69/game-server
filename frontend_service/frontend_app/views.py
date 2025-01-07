import requests
from django.http import HttpResponse
from django.shortcuts import render

from frontend_service.microservices.users_api import get_users_registration_url


def home(request):
    """
    Home page view that returns a simple greeting message.
    """
    context = {
        'title': 'Home',
    }
    response = render(request, 'frontend_app/home.html', context)
    return response


def registration(request):
    """
    Handles user registration. On GET request, renders the registration form.
    On POST request, sends user data to the backend and processes the response.
    If the registration is successful, redirects the user to the desktop page.
    If any errors occur during the request, displays relevant error messages.
    """
    context = {'title': 'Registration'}  # Context for the registration template

    # Handle GET request: render the registration form
    if request.method == 'GET':
        return render(request, 'frontend_app/registration.html', context)

    # Handle POST request: send user data to the backend for registration
    if request.method == 'POST':
        user_data = request.POST  # Get user data from the form
        users_response = None  # Variable to store the response from the backend
        status_code = 200  # Default to OK (200)

        try:
            # Send the POST request to the backend API
            users_response = requests.post(get_users_registration_url(), data=user_data)
            # Raise an error if the HTTP response status code indicates failure (e.g., 400 or 500)
            users_response.raise_for_status()

            # If registration is successful (status code 201), show the success message
            if users_response.status_code == 201:
                message = users_response.json().get('message')  # Extract success message from the response
                context['title'] = 'Desktop'
                context['message'] = message  # Display the success message
                response = render(request, 'frontend_app/desktop.html', context)
                response.status_code = 201
                return response

        except requests.exceptions.Timeout:
            # Handle timeout errors (server took too long to respond)
            context['errors'] = {'error': 'Request timed out. Please try again later.'}
            status_code = 503
        except requests.exceptions.ConnectionError:
            # Handle connection errors (unable to reach the server)
            context['errors'] = {'error': 'Connection error. Please check your network and try again.'}
            status_code = 503
        except requests.exceptions.RequestException as e:
            # Handle other general request errors
            if users_response is not None:
                # If a response was received, check for specific HTTP status codes
                if users_response.status_code == 400:
                    # Parse and display field errors for invalid data
                    errors = users_response.json().get('errors', [])
                    field_errors = {field: response_messages for field, response_messages in errors}
                    context['errors'] = field_errors
                    status_code = 400
                else:
                    context['errors'] = {'error': f'Unexpected error: {str(e)}'}
                    status_code = 500
            else:
                # If no response was received, indicate server unavailability
                context['errors'] = {'error': 'Server is not responding, please try later.'}
                status_code = 503

        # Render the registration form with the error context if an error occurred
        response = render(request, 'frontend_app/registration.html', context)
        response.status_code = status_code
        return response
