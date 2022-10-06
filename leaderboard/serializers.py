from rest_framework import serializers

from .models import GithubUser, Repository, Label, Issue, PullRequest


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ('name', 'color', 'points')


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = ('id', 'name',)


class IssueSerializer(serializers.ModelSerializer):
    points = serializers.IntegerField()
    labels = LabelSerializer(many=True, source='feature_labels')

    repository = RepositorySerializer()

    class Meta:
        model = Issue
        fields = (
            'id', 'title', 'url', 'labels', 'locked', 'state', 'created_at', 'updated_at', 'closed_at', 'points',
            'repository'
        )


class PullRequestSerializer(serializers.ModelSerializer):
    points = serializers.IntegerField()
    repository = RepositorySerializer()

    class Meta:
        model = PullRequest
        fields = (
            'id', 'title', 'url', 'state', 'created_at', 'updated_at', 'closed_at', 'points', 'repository'
        )


class GithubUserSerializer(serializers.ModelSerializer):
    issues = IssueSerializer(many=True)
    pull_requests = PullRequestSerializer(many=True)
    points = serializers.IntegerField()

    class Meta:
        model = GithubUser
        fields = ('id', 'username', 'avatar_url', 'points', 'issues', 'pull_requests')
