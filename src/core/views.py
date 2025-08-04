# core/views.py content placeholder
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def landing_page(request):
    return render(request, 'core/landing_page.html')

@login_required
def lobby(request):
    announcements = ["Welcome to ShadowNexus!", "Character Generator v1 launching soon."]
    feed = ["You registered an account.", "You viewed the character generator."]
    return render(request, 'core/lobby.html', {'announcements': announcements, 'feed': feed})
