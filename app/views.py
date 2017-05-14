from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import ModelFormMixin
from django.db.models import Sum
from django.contrib import messages
from django.core.mail import send_mail
from datetime import datetime
from requests import exceptions

from .models import Repository, File
from .forms import RepositoryForm
from .analyzer import Analyzer


def analyze_and_update_files(repo):
    results = Analyzer.analyze()
    # delete files that no longer are in repo
    paths = [f['path'] for f in results]
    File.objects.filter(repo=repo).exclude(path__in=paths).delete()
    for filestats in results:
        File.objects.update_or_create(repo=repo, path=filestats['path'], defaults=filestats)


def mail_subscribers(name, url):
    mail_subject = 'Repository {} analysis report'.format(name)
    mail_msg = ('The {} repository has been analyzed against PEP8 conventions.\n'
                'The results can be seen here:\n'
                '[Here goes the url of the webapp]'
                ).format(url)
    emails = Analyzer.get_repo_subscribers()
    if emails:
        print("-------------------------------------------------------------------------------")
        send_mail(mail_subject, mail_msg, 'notifier@codeanalyzer.pl', emails, fail_silently=False)
    else:
        print('No emails found')


class IndexView(ListView, ModelFormMixin):
    model = Repository
    form_class = RepositoryForm
    template_name = 'app/index.html'
    context_object_name = 'repositories'
    paginate_by = 5

    def get(self, request, *args, **kwargs):
        self.object = None
        self.form = self.get_form(self.form_class)
        return ListView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = None
        self.form = self.get_form(self.form_class)

        if self.form.is_valid():
            repo = self.form.save(commit=False)
            url_split = repo.url.split('/')[:5]
            repo.url = '/'.join(url_split)

            try:
                Analyzer.get_repo_archive(repo.url)
            except exceptions.HTTPError:
                messages.error(request, "Error 404: Repository not found.")
                return HttpResponseRedirect(reverse('app:home'))

            name = '/'.join(url_split[-2:])
            repo, _ = Repository.objects.update_or_create(url=repo.url, name=name,
                                                          defaults={'analysis_date': datetime.now()})

            analyze_and_update_files(repo)
            mail_subscribers(repo.name, repo.url)
            messages.success(request, "Repository analyzed successfully. Here are the results.")
            return HttpResponseRedirect(reverse('app:detail', kwargs={'pk': repo.id}))

        return self.get(self, request, *args, **kwargs)

    def get_queryset(self):
        return Repository.objects.order_by('-analysis_date')

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['form'] = self.form
        return context


class RepoDetailView(DetailView):
    model = Repository
    template_name = 'app/detail.html'

    def get_context_data(self, **kwargs):
        context = super(RepoDetailView, self).get_context_data(**kwargs)
        context['files'] = File.objects.filter(repo=self.kwargs['pk'])
        context['sum'] = context['files'].aggregate(Sum('errors_num'))['errors_num__sum']
        return context

    def post(self, request, *args, **kwargs):
        try:
            url = request.POST['url']
            Analyzer.get_repo_archive(url)
            repo = Repository.objects.get(url=url)
            repo.analysis_date = datetime.now()
            repo.save()
            analyze_and_update_files(repo)
            mail_subscribers(repo.name, repo.url)
            messages.success(request, "Repository analyzed successfully. Report has been updated.")
        except exceptions.HTTPError:
            messages.error(request, "Failure: Repository not found.")

        return self.get(self, request, *args, **kwargs)
