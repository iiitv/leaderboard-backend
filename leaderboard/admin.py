from django.contrib import admin

from .models import GithubUser, Label, Repository, Issue, PullRequest


@admin.register(GithubUser)
class GithubUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'avatar_url', 'points')
    search_fields = ('id', 'username')

    def has_add_permission(self, request):
        return False


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'points')
    search_fields = ('name',)


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'consider_contributions')
    search_fields = ('id', 'name')

    def has_add_permission(self, request):
        return False


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'url', 'locked', 'repository', 'state', 'pr', 'user')
    search_fields = (
        'title', 'url', 'state', 'user')

    def has_add_permission(self, request):
        return False


@admin.register(PullRequest)
class PullRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'url', 'state', 'user', 'merged')
    search_fields = (
        'id', 'title', 'url', 'user')

    def has_add_permission(self, request):
        return False
