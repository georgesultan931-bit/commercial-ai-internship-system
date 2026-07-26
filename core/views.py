from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        'message': 'Welcome to InternHub API',
        'version': '1.0',
        'endpoints': {
            'users': '/api/v1/users/',
            'organizations': '/api/v1/organizations/',
            'internships': '/api/v1/internships/',
            'applications': '/api/v1/applications/',
        }
    })
