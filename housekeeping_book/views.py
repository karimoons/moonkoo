from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .forms import ChoiceFamilyForm, CreateFamilyForm

from .models import Family

@login_required
def index(request):
    if request.method == 'POST':
        form = ChoiceFamilyForm(request.POST, user=request.user)
        if form.is_valid():
            request.session['current_family_id'] = request.POST['choice_family']
            return redirect(reverse('housekeeping_book:dashboard'))

    else:    
        form = ChoiceFamilyForm(user=request.user)

    return render(request, 'housekeeping_book/index.html', {'form': form})

@login_required
def create_family(request):
    if request.method == 'POST':
        form = CreateFamilyForm(request.POST)
        if form.is_valid():
            new_family = form.save()
            new_family.member.add(request.user)

            return redirect(reverse('housekeeping_book:index'))
    else:
        form = CreateFamilyForm()

    return render(request, 'housekeeping_book/create_family.html', {'form': form})

@login_required
def dashboard(request):
    current_family = Family.objects.get(id=request.session['current_family_id'])

    return render(request, 'housekeeping_book/dashboard.html', {'current_family': current_family})