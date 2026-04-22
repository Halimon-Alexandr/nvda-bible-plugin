# Biblia

Aplikacja przeznaczona jest do wygodnego badania Pisma Świętego i oferuje zaawansowane narzędzia nawigacji, wyszukiwania oraz zarządzania tłumaczeniami biblijnymi. Umożliwia łatwe poruszanie się po tekście, przechodzenie między księgami, rozdziałami i wersami, pracę z różnymi tłumaczeniami oraz porównywanie miejsc biblijnych.

**Deweloper:** Halimon Aleksandr

**Email:** [halimon.alexandr@gmail.com](mailto:halimon.alexandr@gmail.com)

**Repozytorium:** [GitHub](https://github.com/Halimon-Alexandr/nvda-bible-plugin)

Wsparcie projektu

[PrivatBank Ukraine](https://www.privat24.ua/send/jkjck)  

[PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=halimon.alexandr@gmail.com)

---

## Główne możliwości

Aplikacja umożliwia:

- Korzystanie z systemu kart do jednoczesnej pracy z wieloma tekstami Pisma.
- Szybkie poruszanie się między księgami, rozdziałami, wersami i tłumaczeniami.
- Kopiowanie wersów i fragmentów z odniesieniem.
- Przeglądanie miejsc równoległych i podobnych pod względem kontekstu fragmentów.
- Korzystanie z wyszukiwania tekstowego z możliwością filtrowania według ksiąg, rozdziałów lub wersów, w tym inteligentnego wyszukiwania przy użyciu Gemini API.
- Pracę z planami czytania, śledzenie postępu i oznaczanie przeczytanych miejsc.
- Pobieranie i usuwanie tłumaczeń dla różnych języków oraz planów czytania.

---

### Okno główne

Okno główne zawiera:

- **Pole tekstowe** z tekstem Biblii, zajmujące większość ekranu.
- **Trzy listy rozwijane** do wyboru księgi, rozdziału i tłumaczenia.

Zawartość pola tekstowego odpowiada wybranym parametrom. W nagłówku okna wyświetlana jest aktualna księga, rozdział i tłumaczenie, co pomaga szybko określić, który fragment jest otwarty.

**Otwarcie okna:** `NVDA+X`

Uwaga: Podczas pierwszego uruchomienia aplikacji automatycznie otwiera się okno ustawień. Aby rozpocząć pracę, należy pobrać co najmniej jedno tłumaczenie Biblii, następnie zamknąć ustawienia i uruchomić aplikację ponownie.

**Nawigacja i sterowanie:**

- **Przełączanie między listami rozwijanymi i tekstem:** `Tab` / `Shift+Tab`
- **Przejście do następnej / poprzedniej księgi:** `B` / `Shift+B`
- **Przejście do następnego / poprzedniego rozdziału:** `C` / `Shift+C`
- **Przejście do następnego / poprzedniego tłumaczenia:** `T` / `Shift+T`
- **Przesunięcie kursora o 5 wersów wstecz / do przodu:** `PageUp` / `PageDown`
- **Przesunięcie kursora o 10 wersów wstecz / do przodu:** `Ctrl+PageUp` / `Ctrl+PageDown`
- **Szybkie przejście do wersu:** cyfry `0–9`

**Zarządzanie kartami:**

- **Utwórz nową kartę:** `Ctrl+T`
- **Zamknij bieżącą kartę:** `Ctrl+W`
- **Przełącz się na następną / poprzednią kartę:** `Ctrl+Tab` / `Ctrl+Shift+Tab`
- **Przejdź do karty 1–9:** `Ctrl+1` .. `Ctrl+9`

**Ustawienia widoku:**

- **Pokaż / ukryj numery wersów:** `Ctrl+H`
- **Powiększ / pomniejsz rozmiar czcionki:** `Ctrl++` / `Ctrl+-`

**Klawisze kontekstowe:**

- **Skopiuj bieżący wers lub zaznaczony tekst z odniesieniem biblijnym:** `Ctrl+Shift+C`
- **Otwórz okno odniesień równoległych dla bieżącego wersu:** `Ctrl+Shift+L`

**Pozostałe klawisze:**

- **Wyszukiwanie na stronie:** `Ctrl+Shift+F`
- **Przejście do następnego / poprzedniego wyniku wyszukiwania:** `F3` / `Shift+F3`
- **Wyszukiwanie w Biblii:** `Ctrl+F`
- **Plany czytania:** `Ctrl+R`
- **Przejście do odniesienia:** `Ctrl+L`
- **Zamknij okno:** `Alt+F4` lub `Esc`
- **Pomoc:** `F1`

---

### Okno wyszukiwania

Okno wyszukiwania służy do wyszukiwania wersów biblijnych według tekstu we wszystkich księgach lub w wybranych rozdziałach. Obsługuje filtrowanie według ksiąg, wyszukiwanie całych słów, z uwzględnieniem wielkości liter oraz z użyciem wyrażeń regularnych. Dostępne jest również inteligentne wyszukiwanie przy użyciu Gemini API.

**Główne elementy:**

- **Pole do wprowadzania zapytania wyszukiwania**
- **Pola wyboru parametrów wyszukiwania** (całe słowo, uwzględnienie wielkości liter, wyrażenia regularne)
- **Lista wyników wyszukiwania**

**Klawisze sterowania:**

- **Przełączanie między elementami okna:** `Tab` / `Shift+Tab`
- **Wyszukiwanie na stronie:** `Ctrl+Shift+F`
- **Przejście do następnego / poprzedniego wyniku wyszukiwania:** `F3` / `Shift+F3`
- **Przeglądanie wybranego wyniku w kontekście rozdziału:** `Ctrl+Q`
- **Otwarcie wybranego wyniku w oknie głównym:** `Enter`
- **Otwarcie wybranego wyniku w nowej karcie:** `Ctrl+Enter`
- **Zamknięcie okna wyszukiwania:** `Esc`
- **Otwarcie pomocy:** `F1`

---

### Okno planów czytania

Okno planów czytania służy do pracy z planami czytania Biblii i śledzenia postępu. Umożliwia oznaczanie przeczytanych dni i fragmentów, przełączanie się między dniami planu, zmianę tłumaczeń oraz przeglądanie zawartości każdego dnia.

**Główne elementy:**

- **Lista rozwijana dni** do wyboru konkretnego dnia planu.
- **Lista czytania** dla wybranego dnia.
- **Pole tekstowe** do wyświetlania tekstu wybranego fragmentu.

---
**Klawisze sterowania:**

- **Przełączanie między elementami okna:** `Tab` / `Shift+Tab`
- **Oznacz dzień lub fragment jako przeczytany / nieprzeczytany:** `Spacja`
- **Zmień tłumaczenie:** `T` / `Shift+T`
- **Zmień plan czytania:** `Ctrl+Tab` / `Ctrl+Shift+Tab`
- **Przesuń kursor o 5 wersów wstecz / do przodu:** `PageUp` / `PageDown`
- **Przesuń kursor o 10 wersów wstecz / do przodu:** `Ctrl+PageUp` / `Ctrl+PageDown`
- **Przejdź do wersu:** cyfry `0–9`
- **Powiększ rozmiar czcionki:** `Ctrl++`
- **Pomniejsz rozmiar czcionki:** `Ctrl+-`
- **Pokaż / ukryj numery wersów:** `Ctrl+H`
- **Wyszukiwanie na stronie:** `Ctrl+Shift+F`
- **Przejście do następnego / poprzedniego wyniku wyszukiwania:** `F3` / `Shift+F3`
- **Zamknięcie okna:** `Esc`
- **Pomoc:** `F1`

---

### Okno przejścia do odniesienia i tworzenia nowej karty

Te okna służą do szybkiego przejścia do konkretnej księgi, rozdziału lub wersu poprzez wprowadzenie odniesienia biblijnego, a także do otwarcia nowej karty z zadanymi parametrami. Obsługiwane są różne formaty wprowadzania odniesień, w tym skrócone nazwy ksiąg, numery rozdziałów i wersów. Lista dostępnych skrótów znajduje się w pomocy aplikacji.

Akceptowane są zarówno format wschodni (np. "J 3:16"), jak i zachodni ("J 3,16").

**Główne elementy:**

- **Pole do wprowadzania odniesienia** (zachowuje historię ostatnich przejść).
- **Przycisk domyślny** (otwiera Księgę Rodzaju, rozdział 1).
- **Przycisk potwierdzenia przejścia**.

**Klawisze sterowania:**

- **Przejdź do wprowadzonego odniesienia:** `Enter`
- **Zamknij okno:** `Esc`
- **Otwórz pomoc:** `F1`

---

### Okno odniesień równoległych

Okno odniesień równoległych służy do przeglądania i analizy miejsc równoległych oraz podobnych pod względem kontekstu fragmentów biblijnych dla wybranego wersu. Pomaga to głębiej zrozumieć treść tekstu i związki między różnymi częściami Pisma Świętego.

**Główne elementy:**

- **Pole tekstowe** z listą równoległych miejsc biblijnych.

**Klawisze sterowania:**

- **Wyszukiwanie na stronie:** `Ctrl+Shift+F`
- **Przejście do następnego / poprzedniego wyniku wyszukiwania:** `F3` / `Shift+F3`
- **Przeglądanie wybranego wyniku w kontekście rozdziału:** `Ctrl+Q`
- **Otwarcie wybranego wyniku w oknie głównym:** `Enter`
- **Otwarcie wybranego wyniku w nowej karcie:** `Ctrl+Enter`
- **Zamknięcie okna:** `Esc`
- **Otwarcie pomocy:** `F1`

---

### Menu programu

Menu programu w większości duplikuje funkcje skrótów klawiszowych i jest przeznaczone dla wygody użytkowników, którzy nie pamiętają wszystkich kombinacji klawiszy. Dostępne jest w oknie głównym i oknie planów czytania.

**Główne możliwości menu:**

- Wykonanie działań dostępnych przez skróty klawiszowe.
- Zarządzanie parametrami widoku i kartami.
- Dostęp do ustawień programu i pomocy.

---

### Menu kontekstowe

Menu kontekstowe umożliwia szybkie wykonywanie podstawowych działań na zaznaczonym tekście, bieżącym wersecie lub wybranym wyniku wyszukiwania w tekście Biblii.

Menu kontekstowe jest dostępne:

- w **oknie głównym**;
- w **oknie wyszukiwania**;
- w **oknie odniesień równoległych**.

Menu kontekstowe wywołuje się za pomocą:

- `Shift+F10` lub klawisza menu kontekstowego na klawiatury.

**Główne funkcje menu kontekstowego:**

- **Podgląd** — otwiera wybrany wynik w kontekście odpowiedniego rozdziału.
- **Otwórz w bieżącej karcie** — otwiera wybrane miejsce w aktywnej karcie.
- **Otwórz w nowej karcie** — otwiera wybrane miejsce w nowej karcie.
- **Kopiuj** zaznaczony tekst lub bieżący wers wraz z odniesieniem biblijnym (w oknie głównym).
- **Otwórz listę odniesień równoległych** dla bieżącego wersu (w oknie głównym).

---

### Ustawienia

Sekcja ustawień służy do zarządzania głównymi parametrami programu, w tym tłumaczeniami, planami czytania, integracją z Gemini API oraz parametrami aktualizacji.

**Główne możliwości:**

- **Zarządzanie tłumaczeniami** (pobieranie i usuwanie).
- **Zarządzanie planami czytania** (pobieranie, usuwanie i resetowanie postępu).
- **Wprowadzanie klucza API** w celu włączenia inteligentnego wyszukiwania.
- **Włączanie i wyłączanie** automatycznej sprawdzania aktualizacji.

**Jak otworzyć ustawienia:**

- Przez menu programu: **Narzędzia → Ustawienia**.
- Przez ustawienia NVDA: **NVDA+N → Parametry → Ustawienia → Biblia**.

---

### Licencja

Aplikacja "Biblia" jest rozpowszechniana na licencji **[GPL 2](https://www.gnu.org/licenses/gpl-2.0.html)**
