from django.shortcuts import render

def index(request):
    return render(request, 'housekeeping_book/index.html')