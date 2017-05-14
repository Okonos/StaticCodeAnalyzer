# StaticCodeAnalyzer


### Uruchomienie projektu

W virtualenv z pythonem 3 zainstalować niezbędne moduły z pliku requirements.txt:
```sh
pip install -r requirements.txt
```

Uruchomienie:
```sh
python manage.py runserver
```


### Opis projektu

Funkcjonalność aplikacji obejmuje wszystkie wymienione punkty poza możliwością wybrania checkerów z kilkoma zastrzeżeniami:
 * Wspierane są wyłącznie repozytoria na GitHubie.
 * Analiza kodu wykonywana jest przy pomocy modułu pep8/pycodestyle (https://pep8.readthedocs.io/en/latest/index.html).
 * Repozytorium dodawane jest w momencie zlecenia jego analizy.
 * Mail powiadamiający subskrybentów projektu "wysyłany" jest poprzez backend konsolowy, czyli drukowany jest na konsoli.
 Mając do dyspozycji serwer SMTP nietrudno o rzeczywisty wysył maili -- wystarczy w [settings.py](StaticCodeAnalyzer/settings.py)
 usunąć [linię 125](StaticCodeAnalyzer/settings.py#L125) lub podmienić ją na `'django.core.mail.backends.smtp.EmailBackend'`
 oraz dodać kilka stałych opisujących informacje połączeniowe z serwerem (`EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, ew. EMAIL_USE_{TLS, SSL}`).


### Komentarz

Logika dotycząca analizy kodu zaimplementowana została w pliku [analyzer.py](app/analyzer.py).

W celu analizy repozytorium przy użyciu GitHub API pobierane jest jego archiwum zip,
wypakowywane są z niego pliki z rozszerzeniem ".py" i ostatecznie każdy wypakowany plik jest analizowany.
Po analizie archiwum i pliki są usuwane.

Powyższy plik zawiera również kod pozyskujący emaile subskrybentów projektu. Z uwagi na fakt, że email użytkownika
wyświetlany jest jedynie jeśli został on ustawiony przez niego jako publiczny i co więcej
jedynie dla uwierzytelnionych użytkowników, na potrzeby tego zadania stażowego odbywa się to niejako "na około",
stosując "hack", wyłuskujący email z publicznych wydarzeń użytkownika.
W rzeczywistych warunkach, zakładając, że każdy z subskrybentów projektu miałby swój adres ustawiony jako publiczny,
wystarczyłby Personal Access Token w nagłówku żądania `GET /users/:username`.

Aplikacja nie była pisana z myślą o wspołbieżnym dostępie, dlatego jednoczesne zlecenie analizy tego samego repozytorium
mogłoby poskutkować dwukrotnym jego dodaniem do bazy danych.
Rozwiązaniem tego problemu mogłoby być np. nadanie atrybutu unikalności [polu nazwy repozytorium](app/models.py#L11).
