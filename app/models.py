from django.db import models
from django.core.exceptions import ValidationError


def validate_url(url):
    if not url.startswith('https://github.com/'):
        raise ValidationError("Only Github repos supported.")


class Repository(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField(validators=[validate_url])
    analysis_date = models.DateTimeField('last analysis date')


class File(models.Model):
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE)
    path = models.CharField(max_length=100)
    errors_num = models.PositiveIntegerField(default=0)
    statistics = models.TextField()
