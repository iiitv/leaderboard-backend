# Generated by Django 4.1.1 on 2022-10-05 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaderboard', '0003_issue_issue_opening_points_issue_pr_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='html_url',
            field=models.URLField(default=''),
            preserve_default=False,
        ),
    ]
