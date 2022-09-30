import hashlib
import hmac
import logging
from typing import Optional

from django.db.models import Sum, Subquery, OuterRef, F
from rest_framework import status
from rest_framework import views, generics
from rest_framework.exceptions import NotAcceptable
from rest_framework.request import Request
from rest_framework.response import Response

from .data_models import LabelData, IssueData, RepositoryData, get_data_model, PullRequestData
from .models import Label, Issue, PullRequest, GithubUser
from .serializers import GithubUserSerializer
from .utils import GITHUB_WEBHOOK_SECRET, CONTRIBUTION_ACCEPTED_TOPIC

logger = logging.getLogger(__name__)


class ContributorsListView(generics.ListAPIView):
    serializer_class = GithubUserSerializer
    queryset = GithubUser.objects.annotate(
        issue_total_points=Subquery(
            Issue.objects.filter(
                user__id=OuterRef('id'),
            ).annotate(Sum('labels__points')).values('labels__points__sum'),
        ),
        pr_total_points=Subquery(
            PullRequest.objects.filter(
                user__id=OuterRef('id'),
            ).annotate(Sum('labels__points')).values('labels__points__sum'),
        ),
    ).annotate(
        total_points=F('issue_total_points') + F('pr_total_points'),
    ).order_by('total_points')


class GithubWebhookListenerView(views.APIView):

    @staticmethod
    def verify_webhook(request: Request) -> bool:
        signature = request.headers.get('X-Hub-Signature')
        _, signature = signature.split('=')
        body = request.raw_body
        return signature == hmac.new(GITHUB_WEBHOOK_SECRET.encode(), body.encode(), hashlib.sha1).hexdigest()

    @staticmethod
    def to_consider(
            issue: Optional[IssueData] = None,
            repository: Optional[RepositoryData] = None,
            label: Optional[LabelData] = None,
            raise_exception: bool = True,
    ) -> bool:
        def _raise():
            if raise_exception:
                raise NotAcceptable
            else:
                return False

        if issue and not any(
                label.name in Label.objects.filter(points__gt=0).values_list('name', flat=True)
                for label in issue.labels
        ):
            return _raise()
        if repository and CONTRIBUTION_ACCEPTED_TOPIC not in repository.topics:
            return _raise()
        try:
            if label and Label.objects.get(name=label.name, points__gt=0):
                pass
        except Label.DoesNotExist:
            return _raise()

        return True

    def _handle_issues_labeled(self, request: Request):
        label, issue, repository = get_data_model(request.data, [LabelData, IssueData, RepositoryData])
        self.to_consider(repository=repository)
        label.to_model()
        issue.to_model()

    def _handle_issues_unlabeled(self, request: Request):
        label, issue, repository = get_data_model(request.data, [LabelData, IssueData, RepositoryData])
        self.to_consider(repository=repository)
        label.to_model()
        issue.to_model()

    def _handle_pull_request_labeled(self, request: Request):
        pull_request, label, repository = get_data_model(request.data, [PullRequestData, LabelData, RepositoryData])
        self.to_consider(repository=repository)
        label.to_model()
        pull_request.to_model()

    def _handle_pull_request_unlabeled(self, request: Request):
        pull_request, label, repository = get_data_model(request.data, [PullRequestData, LabelData, RepositoryData])
        self.to_consider(repository=repository)
        label.to_model()
        pull_request.to_model()

    def post(self, request: Request, *args, **kwargs):
        if not request.data or not self.verify_webhook(request):
            return Response(status=status.HTTP_403_FORBIDDEN)

        event = request.headers.get('X-GitHub-Event')
        action = request.data.get('action')

        if action:
            handler = getattr(self, f"_handle_{event}_{action}", None)
        else:
            handler = getattr(self, f"_handle_{event}", None)

        if handler:
            handler(request)
            return Response(status=status.HTTP_200_OK)
        else:
            logger.warning(f"handler for {action} not found")
            return Response(status=status.HTTP_404_NOT_FOUND)
