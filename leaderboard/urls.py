from django.urls import path

from .views import GithubWebhookListenerView, ContributorsListView

urlpatterns = [
    path("webhook/github/", GithubWebhookListenerView.as_view(), name="github_webhook_listener"),
    path("contributors/", ContributorsListView.as_view(), name="contributors_list"),
]
