import time
from django.shortcuts import render, HttpResponse, redirect, reverse
from user.forms.issues import IssuesModelForm


def issues(request, project_id):
    form = IssuesModelForm()
    return render(request, 'user/manage/issues.html', {'form': form})
