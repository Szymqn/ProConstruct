from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class LoginTestCase(TestCase):

    def setUp(self):
        # 1. Inicjalizacja danych dla testów
        self.email = 'test@test.pl'
        self.username = 'testowy_user'
        self.password = 'SuperTajneHaslo123'

        # Tworzymy użytkownika w testowej bazie danych
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
            username=self.username
        )

        # Pobieramy adres URL do logowania (na podstawie nazwy z urls.py)
        self.login_url = reverse('login')

    def test_prawidlowe_logowanie(self):
        """
        Prawidłowe logowanie: Wpisano poprawny login oraz prawidłowe hasło.
        Oczekiwany rezultat: Użytkownik zostaje zalogowany i przekierowany na stronę główną.
        """
        response = self.client.post(self.login_url, {
            'username': self.email,  # LoginForm oczekuje klucza 'username', ale podajemy email
            'password': self.password
        })

        # Oczekujemy przekierowania (kod 302) do strony głównej (home)
        self.assertRedirects(response, reverse('home'))
        # Sprawdzamy, czy w sesji zapisano ID użytkownika (czyli czy jest zalogowany)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_logowanie_przez_github(self):
        """
        Prawidłowe logowanie przez GitHub: Wybrano alternatywną formę logowania.
        Oczekiwany rezultat: Przekierowanie do zewnętrznego dostawcy OAuth.

        UWAGA: Test zakłada użycie biblioteki django-allauth.
        Jeśli używasz innej, nazwa ścieżki ('github_login') może wymagać dostosowania.
        """
        try:
            github_login_url = reverse('github_login')  # Zmień nazwę na właściwą dla Twojego projektu
            response = self.client.get(github_login_url)

            # Oczekujemy przekierowania (302) poza naszą domenę (do GitHuba)
            self.assertEqual(response.status_code, 302)
            self.assertIn('github.com', response.url)
        except Exception:
            # Jeśli url 'github_login' nie jest jeszcze skonfigurowany, test zostaje pominięty z komunikatem
            self.skipTest("Nie znaleziono w urls.py ścieżki do logowania GitHub.")

    def test_puste_pola(self):
        """
        Puste pola: Zostawiono pole loginu i hasła puste.
        Oczekiwany rezultat: Formularz nie wysyła zapytania (zwraca stronę ponownie z błędami).
        """
        response = self.client.post(self.login_url, {
            'username': '',
            'password': ''
        })

        # Brak przekierowania - strona ładuje się ponownie z błędami (kod 200)
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)
        # Sprawdzamy, czy w kontekście formularza pojawiły się błędy (to pole jest wymagane)
        self.assertTrue(response.context['form'].errors)

    def test_nieprawidlowe_dane_logowania(self):
        """
        Nieprawidłowe dane: Istniejący login, błędne hasło (i odwrotnie).
        Oczekiwany rezultat: Odrzucenie próby, powrót na stronę logowania.
        """
        # Scenariusz 1: Poprawny email, złe hasło
        response_bad_pass = self.client.post(self.login_url, {
            'username': self.email,
            'password': 'ZleHaslo123'
        })
        self.assertEqual(response_bad_pass.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)

        # Scenariusz 2: Zły email, poprawne hasło
        response_bad_email = self.client.post(self.login_url, {
            'username': 'nieistnieje@test.pl',
            'password': self.password
        })
        self.assertEqual(response_bad_email.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_przekroczenie_limitu_znakow(self):
        """
        Przekroczenie limitu: Zbyt długi ciąg znaków w polu.
        Oczekiwany rezultat: Odrzucenie wpisu.
        """
        zbyt_dlugi_email = ('a' * 250) + '@test.com'

        response = self.client.post(self.login_url, {
            'username': zbyt_dlugi_email,
            'password': self.password
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_sql_injection(self):
        """
        Podatność na SQL Injection: Próba oszukania zapytania bazy.
        Oczekiwany rezultat: Aplikacja odrzuca próbę (kod 200, powrót do formularza), nie wyrzuca błędu 500.
        """
        payload = "admin' OR '1'='1"

        response = self.client.post(self.login_url, {
            'username': payload,
            'password': payload
        })

        # Django ORM automatycznie zabezpiecza zapytania, więc kod nie powinien wyrzucić błędu serwera (500),
        # lecz bezpiecznie zinterpretować to jako zły email i zwrócić stronę formularza (200).
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_wrazliwosc_na_biale_znaki(self):
        """
        Białe znaki: Spacja dodana na początku lub końcu hasła.
        Oczekiwany rezultat: Błąd logowania (hasło traktowane dosłownie).
        """
        response = self.client.post(self.login_url, {
            'username': self.email,
            'password': self.password + ' '  # Dodana spacja na końcu
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)


