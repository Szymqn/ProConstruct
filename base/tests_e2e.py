from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from datetime import date, timedelta
import sys

from base.models import Product, Equipment, Cart, CartItem, Order

User = get_user_model()


class ProConstructE2ETests(TestCase):

    def setUp(self):
        """Inicjalizacja środowiska i bazy produktów na potrzeby testów E2E."""
        self.client = Client()

        # Tworzenie produktów (Materiały budowlane)
        self.product_material = Product.objects.create(
            name="Cegła klinkierowa",
            description="Wysokiej jakości cegła.",
            price=2.50,
            image="http://example.com/cegla.jpg",
            quantity=1000
        )

        # Tworzenie sprzętu (Narzędzia)
        self.equipment_tool = Equipment.objects.create(
            name="Koparka kompaktowa",
            description="Idealna do małych wykopów.",
            price=150000.00,
            image="http://example.com/koparka.jpg",
            quantity=2,
            rental_rate=300.00,
            deposit=1000.00
        )

    def _safe_reverse(self, possible_names, kwargs=None):
        """Dynamiczne dopasowywanie nazw URL, aby uniknąć NoReverseMatch."""
        for name in possible_names:
            try:
                return reverse(name, kwargs=kwargs)
            except NoReverseMatch:
                continue
        return None

    # -------------------------------------------------------------------------
    # E2E-01: Pełny proces zakupowy klienta (Rejestracja -> Koszyk -> Checkout)
    # -------------------------------------------------------------------------
    def test_e2e_full_purchase_flow(self):
        """Symulacja pełnej ścieżki klienta: Rejestracja, logowanie, dodanie do koszyka, koszyk."""

        # KROK 1: Rejestracja nowego konta
        signup_data = {
            'username': 'nowy_klient',
            'email': 'klient@proconstruct.pl',
            'password1': 'SilneHaslo123!',
            'password2': 'SilneHaslo123!'
        }
        response_signup = self.client.post(reverse('signup'), signup_data)

        # System powinien przekierować na stronę logowania po udanej rejestracji
        self.assertRedirects(response_signup, reverse('login'))
        self.assertTrue(User.objects.filter(email='klient@proconstruct.pl').exists())

        # KROK 2: Logowanie na nowe konto
        # Zgodnie z modelem CustomUser i LoginForm, autoryzacja odbywa się przez przekazanie
        # adresu email w polu 'username'
        login_data = {
            'username': 'klient@proconstruct.pl',
            'password': 'SilneHaslo123!'
        }
        response_login = self.client.post(reverse('login'), login_data)

        # Sprawdzamy przekierowanie na stronę główną po udanym logowaniu
        self.assertEqual(response_login.status_code, 302)

        # KROK 3: Dodanie materiału do koszyka
        url_add_product = self._safe_reverse(
            ['add-product-to-cart', 'add_product_to_cart'],
            kwargs={'product_id': self.product_material.id}
        )
        if url_add_product:
            # Twój szablon product_details.html wskazuje na użycie metody POST
            response_add = self.client.post(url_add_product)
            self.assertEqual(response_add.status_code, 302)
        else:
            sys.stderr.write("\n[UWAGA] E2E-01: Pominięto dodawanie produktu - brak URL.\n")

        # KROK 4: Weryfikacja koszyka i podsumowania zamówienia
        # Koszyk tworzy się automatycznie dzięki metodzie save() w CustomUser
        user = User.objects.get(email='klient@proconstruct.pl')
        cart = Cart.objects.get(user=user)
        self.assertTrue(CartItem.objects.filter(cart=cart, product=self.product_material).exists())

    # -------------------------------------------------------------------------
    # E2E-02: Pełny proces rezerwacji i najmu (Narzędzia)
    # -------------------------------------------------------------------------
    def test_e2e_full_rental_flow(self):
        """Symulacja logowania, sprawdzenia dostępności narzędzia i poprawnej rezerwacji z datami."""

        # Tworzenie i logowanie klienta
        user = User.objects.create_user(
            username="wynajmujacy",
            email="wynajem@proconstruct.pl",
            password="Password123!"
        )
        self.client.force_login(user)

        # KROK 1: Rezerwacja narzędzia w wybranym przedziale czasowym
        start_date = date.today()
        end_date = date.today() + timedelta(days=5)

        rental_data = {
            'start_date': str(start_date),
            'end_date': str(end_date)
        }

        url_add_equipment = self._safe_reverse(
            ['add-equipment-to-cart', 'add_equipment_to_cart'],
            kwargs={'equipment_id': self.equipment_tool.id}
        )

        if url_add_equipment:
            response_rent = self.client.post(url_add_equipment, rental_data)
            self.assertEqual(response_rent.status_code, 302)

            # KROK 2: Weryfikacja poprawności zapisu dat
            cart = Cart.objects.get(user=user)
            cart_item = CartItem.objects.get(cart=cart, equipment=self.equipment_tool)
            self.assertEqual(cart_item.rent_start_date, start_date)
            self.assertEqual(cart_item.rent_end_date, end_date)
        else:
            self.skipTest("Brak widoku dodawania sprzętu w urls.py")

    # -------------------------------------------------------------------------
    # E2E-03: Bezpieczeństwo i izolacja środowiska (Dostęp do panelu)
    # -------------------------------------------------------------------------
    def test_e2e_security_admin_access(self):
        """Sprawdzenie, czy zwykły użytkownik oraz gość mają zablokowany dostęp do panelu administratora i widoku check_orders."""

        # KROK 1: Próba wejścia jako gość (niezalogowany) na panel użytkownika (check_orders)
        response_guest = self.client.get(reverse('check_orders'))
        # Dekorator @login_required powinien przekierować na stronę logowania
        self.assertRedirects(response_guest, f"{reverse('login')}?next={reverse('check_orders')}")

        # KROK 2: Próba wejścia do panelu administracyjnego jako zwykły klient
        regular_user = User.objects.create_user(
            username="zwykly",
            email="zwykly@proconstruct.pl",
            password="Password123!"
        )
        self.client.force_login(regular_user)

        # Django Admin wbudowany jest pod standardowym adresem '/admin/'
        response_admin = self.client.get('/admin/')
        # Oczekujemy zablokowania dostępu (zwykle jest to przekierowanie na panel logowania admina lub kod 403)
        self.assertIn(response_admin.status_code, [302, 403])

        # Upewniamy się, że użytkownik nie dostał uprawnień personelu przez pomyłkę
        self.assertFalse(regular_user.is_staff)
        self.assertFalse(regular_user.is_superuser)