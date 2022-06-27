from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from ..forms.family import ChoiceFamilyForm, CreateFamilyForm

from ..models import Family, Account, Tag

BASIC_ACCOUNT = {
    'code': [100, 110, 120, 200, 210, 300, 400, 410, 420, 430, 440, 450, 460, 510, 520, 530, 540, 550, 560, 570, 580, 590],
    'account': ['A', 'A', 'A', 'L', 'L', 'C', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E'],
    'title': ['저축', '주식', '부동산', '신용카드', '대출', '순자산', '근로소득', '콘텐츠소득', '사업소득', '부동산소득', '배당소득', '이자소득', '기타소득', '주거통신비', '보험의료비', '차량교통비', '식비', '생활용품비', '교육도서비', '모임경조사비', '이자비용', '기타비용'],
}

@login_required
def select_family(request):
    if request.method == 'POST':
        form = ChoiceFamilyForm(request.POST, user=request.user)
        if form.is_valid():
            request.session['current_family_id'] = request.POST['choice_family']

            return redirect(reverse('housekeeping_book:dashboard'))

    else:    
        form = ChoiceFamilyForm(user=request.user)

    return render(request, 'housekeeping_book/family/select_family.html', {'form': form})

@login_required
def create_family(request):
    if request.method == 'POST':
        form = CreateFamilyForm(request.POST)
        if form.is_valid():
            new_family = form.save()
            new_family.member.add(request.user)

            for num in range(len(BASIC_ACCOUNT['code'])):
                Account.objects.create(family=new_family, code=BASIC_ACCOUNT['code'][num], account=BASIC_ACCOUNT['account'][num], title=BASIC_ACCOUNT['title'][num])
            
            Tag.objects.create(family=new_family, name=new_family.name)

            return redirect(reverse('housekeeping_book:select_family'))
    else:
        form = CreateFamilyForm()

    return render(request, 'housekeeping_book/family/create_family.html', {'form': form})

@login_required
def invite_family(request):
    context_dict = {
        'fid': request.session['current_family_id'],
        'uid': request.user.username,
    }

    return render(request, 'housekeeping_book/family/invite_family.html', context=context_dict)

@login_required
def accept_invitation(request):
    if request.method == 'POST':
        family = Family.objects.get(id=request.POST['fid'])
        host = User.objects.get(username=request.POST['uid'])

        if host in family.member.all():
            family.member.add(request.user)
            return redirect(reverse('housekeeping_book:select_family'))
        else:
            return redirect(reverse('housekeeping_book:invitation_denied'))

    else:
        try:
            family = Family.objects.get(id=request.GET['fid'])
            host = User.objects.get(username=request.GET['uid'])
        except:
            return redirect(reverse('housekeeping_book:invitation_denied'))

    return render(request, 'housekeeping_book/family/accept_invitation.html', {'family': family, 'host': host})

@login_required
def invitation_denied(request):
    return render(request, 'housekeeping_book/family/invitation_denied.html')