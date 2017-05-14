import os
import requests
import pep8
import io
from contextlib import redirect_stdout
import tempfile
import shutil
import zipfile


class Analyzer:
    tempdir = ''
    zip_path = ''
    url = ''

    @classmethod
    def get_repo_archive(cls, url):
        """
        Downloads repo's zip archive using GitHub API
        :param url: repository's URL
        :raise HTTPError: when request failed
        """
        url = url.split('/')
        url[2] = 'api.github.com'
        url.insert(3, 'repos')
        cls.url = '/'.join(url)
        response = requests.get(cls.url + '/zipball')
        if response.status_code == requests.codes.ok:
            cls.tempdir = tempfile.mkdtemp()
            cls.zip_path = os.path.join(cls.tempdir, 'repo.zip')
            with open(cls.zip_path, 'wb') as zf:
                zf.write(response.content)
        else:
            response.raise_for_status()

    @classmethod
    def extract_py_files(cls):
        """Extract .py files from repo zipball to tempdir and remove the zip"""
        with zipfile.ZipFile(cls.zip_path) as zip_handle:
            for member in filter(lambda x: x.endswith('.py'), zip_handle.namelist()):
                source = zip_handle.open(member)
                filename = member.partition('/')[2].replace('/', '-')
                target = open(os.path.join(cls.tempdir, filename), 'wb')
                with source, target:
                    shutil.copyfileobj(source, target)

        os.remove(cls.zip_path)

    @classmethod
    def analyze(cls):
        """
        Extract, analyze and return the statistics of all source files using pep8 checker.
        :return: list of dictionaries each featuring file info and stats
        """
        cls.extract_py_files()
        style = pep8.StyleGuide()
        results = []
        for filename in os.listdir(cls.tempdir):
            filepath = os.path.join(cls.tempdir, filename)
            result = style.check_files([filepath])
            f = io.StringIO()
            with redirect_stdout(f):
                result.print_statistics()
            statistics = f.getvalue()
            if statistics:
                results.append({'path': filename.replace('-', '/'),
                                'errors_num': result.total_errors,
                                'statistics': statistics})

        shutil.rmtree(cls.tempdir)
        return results

    @classmethod
    def find_email(cls, data):
        """
        Find user email in api's public events json response
        :param data: json containing user's public events
        :return: user's email or None if not found
        """
        if isinstance(data, dict):
            for k in data:
                if k == 'email':
                    return data[k]
                res = cls.find_email(data[k])
                if res is not None and 'noreply' not in res:
                    return res
        elif isinstance(data, list):
            for item in data:
                res = cls.find_email(item)
                if res is not None and 'noreply' not in res:
                    return res

        return None

    @classmethod
    def get_repo_subscribers(cls):
        """
        Get the repository subscribers' emails 
        :return: list of emails or empty list if no emails were found
        :raise HTTPError: when request failed
        """
        subs = requests.get(cls.url + '/subscribers')
        if subs.status_code == requests.codes.ok:
            emails = []
            for sub in subs.json():
                events_url = sub['events_url'].replace('{/privacy}', '/public')
                email = cls.find_email(requests.get(events_url).json())
                if email is not None:
                    emails.append(email)

            return emails
        else:
            subs.raise_for_status()
