from django.conf.urls import url

from .views import IndexView, RepoDetailView

app_name = 'app'
urlpatterns = [
    url(r'^$', IndexView.as_view(), name='home'),
    url(r'^(?P<pk>[0-9]+)$', RepoDetailView.as_view(), name='detail')
]