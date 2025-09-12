from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def language_test_view(request):
    """Test view to demonstrate language switching."""
    context = {
        'redirect_to': request.GET.get('next', '/'),
    }
    return render(request, 'language_test.html', context)

# Simple health check view
def health_check(request):
    return JsonResponse({
        'status': 'OK',
        'message': 'Django server is running',
        'method': request.method,
        'path': request.path
    })
