from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView

from ..forms import TagForm

from ..models import Family, Tag

class TagListView(LoginRequiredMixin, ListView):
    template_name = 'housekeeping_book/tag/tag_list.html'
    
    def get_queryset(self):
        return Tag.objects.filter(family=self.request.session['current_family_id'])

@login_required
def create_tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            new_tag = form.save(commit=False)
            new_tag.family = Family.objects.get(id=request.session['current_family_id'])
            try:
                new_tag.save()

                return redirect(reverse('housekeeping_book:tag_list'))
            except:
                messages.error(request, '꼬리표 이름은 중복될 수 없습니다.')
    else:
        form = TagForm()

    return render(request, 'housekeeping_book/tag/update_tag.html', {'form': form})

@login_required
def update_tag(request, pk):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.id = pk
            tag.family = Family.objects.get(id=request.session['current_family_id'])
            try:
                tag.save()

                return redirect(reverse('housekeeping_book:tag_list'))
            except:
                messages.error(request, '꼬리표 이름은 중복될 수 없습니다.')
    else:
        form = TagForm(instance=Tag.objects.get(id=pk))

    return render(request, 'housekeeping_book/tag/update_tag.html', {'form': form, 'pk': pk})

@login_required
def delete_tag(request, pk):
    tag = Tag.objects.get(id=pk)

    if request.method == 'POST':
        if request.user in tag.family.member.all():
            tag.delete()
            return redirect(reverse('housekeeping_book:tag_list'))
        else:
            messages.error(request, '꼬리표를 삭제할 권한이 없습니다.')

    return render(request, 'housekeeping_book/tag/delete_tag.html', {'tag': tag})