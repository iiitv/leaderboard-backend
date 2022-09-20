from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

import requests
from ipaddress import ip_address, ip_network

@csrf_exempt
def hello(request):
    # Verify if request came from GitHub

    return HttpResponse('pong')