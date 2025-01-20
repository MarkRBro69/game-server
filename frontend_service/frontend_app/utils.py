import requests


def try_requests(method, url, data=None, headers=None, timeout=5):
    context = {}
    response = None
    try:
        response = method(url, data=data, headers=headers, timeout=timeout)
        response.raise_for_status()
        context['status'] = response.status_code
        context['response'] = response
        return context

    except requests.exceptions.Timeout:
        # Handle timeout errors (server took too long to respond)
        context['status'] = 408
        context['errors'] = {'error': 'Request timed out. Please try again later.'}

    except requests.exceptions.ConnectionError:
        # Handle connection errors (unable to reach the server)
        context['status'] = 503
        context['errors'] = {'error': 'Connection error. Please check your network and try again.'}

    except requests.exceptions.HTTPError as e:
        if response is not None:
            context['status'] = 400
            # If a response was received, check for specific HTTP status codes
            if response.status_code == 400:
                # Parse and display field errors for invalid data
                errors = response.json().get('errors', [])
                field_errors = {field: response_messages for field, response_messages in errors}
                context['errors'] = field_errors
            else:
                context['errors'] = {'error': f'Unexpected error: {str(e)}'}
        else:
            # If no response was received, indicate server unavailability
            context['status'] = 503
            context['errors'] = {'error': 'Server is not responding, please try later.'}

    except requests.exceptions.RequestException:
        # Handle other general request errors
        context['status'] = 500
        context['errors'] = {'error': 'Unexpected error.'}

    return context
