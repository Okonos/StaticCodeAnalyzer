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

    @classmethod
    def get_repo_archive(cls, url):
        """Downloads repo's zip archive using GitHub API"""
        response = requests.get(url + '/zipball')
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
        """Extract, analyze and return the statistics of all source files using pep8 checker."""
        cls.extract_py_files()
        # TODO checkery do wyboru
        style = pep8.StyleGuide()
        results = []
        for filename in os.listdir(cls.tempdir):
            filepath = os.path.join(cls.tempdir, filename)
            result = style.check_files([filepath])  # (os.listdir('/tmp/asdf'))
            # result.get_file_results()
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
