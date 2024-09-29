from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, 'main/index.html', {'posts': []})


def search(request):
    # menu = Menu.objects.all()
    return render(request, 'main/search.html', {"menu": [], "active": "home"})
