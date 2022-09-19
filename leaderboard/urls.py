from . import views
from django.urls import path

urlpatterns = [
    path("contribute-a-thon/", views.hello),
]