from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.conf import settings


def load_designtemp(request):
    
    return render(request, 'designs/overview.html')
