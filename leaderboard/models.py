from django.db import models
from django.db.models import QuerySet


class GithubUserManager(models.Manager):
    ...


class GithubUser(models.Model):
    id = models.IntegerField(primary_key=True)
    avatar_url = models.CharField(max_length=255)
    username = models.CharField(max_length=255)

    def __str__(self):
        return self.username

    @property
    def points(self):
        return sum(
            pr.points for pr in self.pullrequest_set.all()
        ) + sum(
            issue.points for issue in self.issue_set.all()
        )

    def issues(self) -> QuerySet['Issue']:
        return self.issue_set.filter(
            repository__consider_contributions=True,
        ).annotate(
            labels_points=models.Sum('labels__points')
        ).filter(
            labels_points__gt=0
        )

    def pull_requests(self):
        return self.pullrequest_set.filter(
            repository__consider_contributions=True,
        ).annotate(
            labels_points=models.Sum('labels__points')
        ).filter(
            labels_points__gt=0
        )


class Label(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    color = models.CharField(max_length=255)
    points = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Repository(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    consider_contributions = models.BooleanField(default=True)


class Issue(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.TextField()
    url = models.URLField()
    labels = models.ManyToManyField(Label)
    locked = models.BooleanField(default=False)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    state = models.CharField(max_length=255, choices=[('open', 'open'), ('closed', 'closed')])
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(GithubUser, on_delete=models.CASCADE)

    @property
    def points(self):
        return self.labels.aggregate(models.Sum('points'))['points__sum'] or 0

    @property
    def feature_labels(self):
        return self.labels.filter(points__gt=0)

    def __str__(self):
        return self.title


class PullRequest(models.Model):
    id = models.IntegerField(primary_key=True)
    url = models.URLField()
    title = models.TextField()
    body = models.TextField()
    state = models.CharField(max_length=255, choices=[('open', 'open'), ('closed', 'closed')])
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)
    merged_at = models.DateTimeField(null=True, blank=True)
    merged = models.BooleanField(default=False)
    labels = models.ManyToManyField(Label)
    user = models.ForeignKey(GithubUser, on_delete=models.CASCADE)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)

    @property
    def points(self):
        return self.labels.aggregate(models.Sum('points'))['points__sum'] or 0

    @property
    def feature_labels(self):
        return self.labels.filter(points__gt=0)

    def __str__(self):
        return self.title
