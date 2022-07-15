from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..models import Family

@login_required
def dashboard(request):
    current_family = Family.objects.get(id=request.session['current_family_id'])

    return render(request, 'housekeeping_book/dashboard.html', {'current_family': current_family})