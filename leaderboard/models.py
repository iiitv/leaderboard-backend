from django.db import models
from django.db.models import QuerySet, Subquery, OuterRef, Sum, F


class States(models.TextChoices):
    OPEN = 'open'
    CLOSED = 'closed'


class GithubUser(models.Model):
    id = models.IntegerField(primary_key=True)
    avatar_url = models.CharField(max_length=255)
    username = models.CharField(max_length=255)

    def __str__(self):
        return self.username

    @property
    def points(self):
        points = sum([issue.points for issue in self.issue_set.all()])
        points += sum([pr.points for pr in self.pullrequest_set.all()])
        return points

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
            merged=True,
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
    state = models.CharField(max_length=255, choices=States.choices)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(GithubUser, on_delete=models.CASCADE)
    assignee = models.ForeignKey(GithubUser, on_delete=models.CASCADE, null=True, blank=True, related_name='assignee')
    issue_opening_points = models.IntegerField(default=10)
    pr = models.ForeignKey('PullRequest', on_delete=models.CASCADE, null=True, blank=True)

    @property
    def feature_labels(self):
        return self.labels.filter(points__gt=0)

    @property
    def points(self):
        if not self.feature_labels.aggregate(Sum('points'))['points__sum']:
            return 0
        return self.issue_opening_points

    def __str__(self):
        return self.title


class PullRequest(models.Model):
    id = models.IntegerField(primary_key=True)
    url = models.URLField()
    html_url = models.URLField()
    title = models.TextField()
    body = models.TextField()
    state = models.CharField(max_length=255, choices=States.choices)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)
    merged_at = models.DateTimeField(null=True, blank=True)
    merged = models.BooleanField()
    # labels = models.ManyToManyField(Label)
    user = models.ForeignKey(GithubUser, on_delete=models.CASCADE)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)

    merge_points = models.IntegerField(default=10)

    @property
    def points(self):
        points = 0
        if self.merged:
            points += self.issue_set.annotate(
                labels_points=Subquery(
                    Issue.objects.filter(
                        id=OuterRef('id'),
                    ).annotate(Sum('labels__points')).values('labels__points__sum'),
                )
            ).aggregate(
                labels_point_sum=models.Sum('labels_points')
            )['labels_point_sum'] or 0

            if points:
                points += self.merge_points

        return points

    def __str__(self):
        return self.title
