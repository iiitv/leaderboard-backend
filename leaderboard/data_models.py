import json
import re
from typing import List, Literal, Optional, Dict, Union

import dateutil.parser
import requests
from bs4 import BeautifulSoup

from leaderboard.models import Label, Issue, Repository, GithubUser, PullRequest
from leaderboard.utils import CONTRIBUTION_ACCEPTED_TOPIC, GITHUB_TOKEN


def get_data_model(data, items: List) -> List['FromDictMixin']:
    ret = []
    for item in items:
        if not issubclass(item, FromDictMixin):
            raise TypeError(f"{item} is not a subclass of FromDictMixin")
        # noinspection PyUnresolvedReferences
        ret.append(item.from_dict(data))
    return ret


class FromDictMixin:

    @classmethod
    def from_dict(cls, data: Dict):
        if key := getattr(cls, 'key', None):
            # noinspection PyArgumentList
            return cls(**data[key], parent_data=data)
        # noinspection PyArgumentList
        return cls(**data[cls.__name__.lower()])


class UserData(FromDictMixin):
    key = 'user'

    def __init__(
            self,
            login: str,
            id: int,
            avatar_url: str,
            **kwargs,
    ):
        self.login = login
        self.id = id
        self.avatar_url = avatar_url
        self.extra = kwargs

    def to_model(self) -> 'GithubUser':
        return GithubUser.objects.get_or_create(id=self.id, defaults={
            'username': self.login,
            'avatar_url': self.avatar_url,
        })[0]


class SenderData(UserData):
    key = 'sender'
    pass


class LabelData(FromDictMixin):
    key = 'label'

    def __init__(
            self,
            id: int,
            url: str,
            name: str,
            color: str,
            **kwargs,
    ):
        self.id = id
        self.url = url
        self.name = name
        self.color = color
        self.extra = kwargs

    def to_model(self) -> 'Label':
        return Label.objects.update_or_create(name=self.name, defaults={'color': self.color})[0]


class IssueData(FromDictMixin):
    key = 'issue'

    def __init__(
            self,
            id: int,
            title: str,
            url: str,
            repository_url: str,
            html_url: str,
            user: dict,
            labels: List[Dict],
            state: Literal['open', 'closed'],
            locked: bool,
            assignee: Optional[dict],
            created_at: str,
            updated_at: str,
            closed_at: Optional[str],
            parent_data: dict = None,
            repository: Union['RepositoryData', 'Repository'] = None,
            **kwargs
    ):
        self.id = id
        self.title = title
        self.url = url
        self.repository_url = repository_url
        self.html_url = html_url
        self.user = UserData(**user)
        self.labels = [LabelData(**label) for label in labels]
        self.state = state
        self.locked = locked
        self.assignee = UserData(**assignee) if assignee else None
        self.created_at = dateutil.parser.parse(created_at)
        self.updated_at = dateutil.parser.parse(updated_at)
        self.closed_at = dateutil.parser.parse(closed_at) if closed_at else None
        self.repository: Union[RepositoryData, Repository]
        if repository:
            self.repository = repository
        else:
            self.repository: RepositoryData = RepositoryData(**parent_data['repository'])
        self.extra = kwargs

    def to_model(self) -> 'Issue':
        issue = Issue.objects.update_or_create(
            id=self.id,
            defaults={
                'title': self.title,
                'url': self.url,
                'locked': self.locked,
                'repository': self.repository.to_model() if isinstance(
                    self.repository,
                    RepositoryData
                ) else self.repository,
                'state': self.state,
                'assignee': self.assignee.to_model() if self.assignee else None,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'closed_at': self.closed_at,
                'user': self.user.to_model(),
            }
        )[0]
        issue.labels.set([label.to_model() for label in self.labels])
        return issue


class RepositoryData(FromDictMixin):
    key = 'repository'

    def __init__(
            self,
            id: int,
            name: str,
            full_name: str,
            private: bool,
            topics: List[str],
            **kwargs,
    ):
        self.id = id
        self.name = name
        self.full_name = full_name
        self.private = private
        self.topics = topics
        self.extra = kwargs

    def to_model(self) -> 'Repository':
        return Repository.objects.update_or_create(
            id=self.id,
            defaults={
                'name': self.name,
                'consider_contributions': True if CONTRIBUTION_ACCEPTED_TOPIC in self.topics else False,
            }
        )[0]


class PullRequestData(FromDictMixin):
    key = 'pull_request'

    def __init__(
            self,
            id: int,
            url: str,
            html_url: str,
            state: Literal['open', 'closed'],
            locked: bool,
            title: str,
            user: Dict,
            body: str,
            created_at: str,
            updated_at: str,
            closed_at: Optional[str],
            merged_at: Optional[str],
            # labels: List[Dict],
            merged: bool,
            parent_data: dict = None,
            repository: Union['RepositoryData', 'Repository'] = None,
            **kwargs,
    ):
        self.id = id
        self.url = url
        self.html_url = html_url
        self.state = state
        self.locked = locked
        self.title = title
        self.user = UserData(**user)
        self.body = body
        self.created_at = dateutil.parser.parse(created_at)
        self.updated_at = dateutil.parser.parse(updated_at)
        self.closed_at = dateutil.parser.parse(closed_at) if closed_at else None
        self.merged_at = dateutil.parser.parse(merged_at) if merged_at else None
        # self.labels = [LabelData(**label) for label in labels]
        self.merged = merged
        self.repository: Union[RepositoryData, Repository]
        if repository:
            self.repository = repository
        else:
            self.repository: RepositoryData = RepositoryData(**parent_data['repository'])
        self.extra = kwargs

    def to_model(self) -> 'PullRequest':
        pr = PullRequest.objects.update_or_create(
            id=self.id,
            defaults={
                'url': self.url,
                'html_url': self.html_url,
                'title': self.title,
                'body': self.body,
                'state': self.state,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'closed_at': self.closed_at,
                'merged_at': self.merged_at,
                'merged': self.merged,
                'repository': self.repository.to_model() if isinstance(
                    self.repository,
                    RepositoryData
                ) else self.repository,
                'user': self.user.to_model(),
            }
        )[0]

        # pr.labels.set([label.to_model() for label in self.labels])
        self.update_linked_issues(pr)
        return pr

    @staticmethod
    def update_linked_issues(pr: 'PullRequest') -> 'list[Issue]':
        response = requests.get(pr.html_url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
        soup = BeautifulSoup(response.text, 'html.parser')
        issue_form = soup.find("form", {"aria-label": re.compile('Link issues')})
        issues: 'list[Issue]' = []
        if not issue_form:
            return issues

        for issue_tag in issue_form.find_all('a'):
            try:
                issue_url = issue_tag['href']
                issue_id = json.loads(issue_tag["data-hydro-click"])['payload']['issue_id']
                try:
                    issue = Issue.objects.get(id=issue_id)
                except Issue.DoesNotExist:
                    issue_data = requests.get(
                        issue_url.replace('https://github.com', 'https://api.github.com/repos'),
                        headers={'Authorization': f'token {GITHUB_TOKEN}'},
                    ).json()
                    issue = IssueData(**issue_data, repository=pr.repository).to_model()
                issues.append(issue)
            except KeyError:
                pass

        pr.issue_set.set(issues)

        return issues
