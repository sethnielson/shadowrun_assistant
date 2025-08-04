from django.shortcuts import render
from .models import Character

def character_list(request):
    characters = Character.objects.filter(owner=request.user) if request.user.is_authenticated else []
    return render(request, 'charcreator/character_list.html', {'characters': characters})
