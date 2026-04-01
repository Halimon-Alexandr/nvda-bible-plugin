# Bible

Aplikace je určena pro pohodlné studium Písma svatého a poskytuje pokročilé nástroje pro navigaci, vyhledávání a správu biblických překladů. Umožňuje snadno se orientovat v textu, přecházet mezi knihami, kapitolami a verši, pracovat s různými překlady a porovnávat biblická místa.

**Vývojář:** Halimon Alexandr

**Email:** [halimon.alexandr@gmail.com](mailto:halimon.alexandr@gmail.com)

**Repozitář:** [GitHub](https://github.com/Halimon-Alexandr/nvda-bible-plugin)

---

## Hlavní funkce

Aplikace umožňuje:

- Používat systém záložek pro současnou práci s více texty Písma.
- Rychle se pohybovat mezi knihami, kapitolami, verši a překlady.
- Kopírovat verše a úryvky s odkazem.
- Prohlížet paralelní místa a podobné kontextové úryvky.
- Používat vyhledávání podle textu s možností filtrování podle knih, kapitol nebo veršů, včetně inteligentního vyhledávání pomocí Gemini API.
- Pracovat s plány čtení, sledovat postup a označovat přečtená místa.
- Stahovat a odstraňovat překlady pro různé jazyky a plány čtení.

---

### Hlavní okno

Hlavní okno obsahuje:

- **Textové pole** s biblickým textem, které zabírá většinu obrazovky.
- **Tři rozbalovací seznamy** pro výběr knihy, kapitoly a překladu.

Obsah textového pole odpovídá vybraným parametrům. V záhlaví okna se zobrazuje aktuální kniha, kapitola a překlad, což pomáhá rychle určit, který úryvek je otevřen.

**Otevření okna:** `NVDA+X`

Poznámka: Při prvním spuštění aplikace se automaticky otevře okno nastavení. Pro zahájení práce je nutné stáhnout alespoň jeden překlad Bible, poté zavřít nastavení a aplikaci spustit znovu.

**Navigace a ovládání:**

- **Přepínání mezi rozbalovacími seznamy a textem:** `Tab` / `Shift+Tab`
- **Přejít na další/předchozí knihu:** `B` / `Shift+B`
- **Přejít na další/předchozí kapitolu:** `C` / `Shift+C`
- **Přejít na další/předchozí překlad:** `T` / `Shift+T`
- **Posunout kurzor o 5 veršů zpět/vpřed:** `PageUp` / `PageDown`
- **Posunout kurzor o 10 veršů zpět/vpřed:** `Ctrl+PageUp` / `Ctrl+PageDown`
- **Rychlý přechod na verš:** číslice `0–9`

**Správa záložek:**

- **Vytvořit novou záložku:** `Ctrl+T`
- **Zavřít aktuální záložku:** `Ctrl+W`
- **Přepnout na další/předchozí záložku:** `Ctrl+Tab` / `Ctrl+Shift+Tab`
- **Přejít na záložku 1–9:** `Ctrl+1` .. `Ctrl+9`

**Nastavení zobrazení:**

- **Zobrazit/skrýt čísla veršů:** `Ctrl+H`
- **Zvětšit/zmenšit velikost písma:** `Ctrl++` / `Ctrl+-`

**Kontextové klávesy:**

- **Kopírovat aktuální verš nebo vybraný text s biblickým odkazem:** `Ctrl+Shift+C`
- **Otevřít okno paralelních odkazů pro aktuální verš:** `Ctrl+Shift+L`

**Ostatní klávesy:**

- **Hledat na stránce:** `Ctrl+Shift+F`
- **Přejít na další/předchozí výsledek hledání:** `F3` / `Shift+F3`
- **Hledat v Bibli:** `Ctrl+F`
- **Plány čtení:** `Ctrl+R`
- **Přejít na odkaz:** `Ctrl+L`
- **Zavřít okno:** `Alt+F4` nebo `Esc`
- **Nápověda:** `F1`

---

### Okno vyhledávání

Okno vyhledávání slouží k vyhledávání biblických veršů podle textu ve všech knihách nebo ve vybraných kapitolách. Podporuje filtrování podle knih, vyhledávání celých slov, s rozlišováním velikosti písmen a pomocí regulárních výrazů. K dispozici je také inteligentní vyhledávání pomocí Gemini API.

**Hlavní prvky:**

- **Pole pro zadání vyhledávacího dotazu**
- **Zaškrtávací políčka parametrů vyhledávání** (celá slova, citlivost na velikost písmen, regulární výrazy)
- **Seznam výsledků vyhledávání**

**Klávesy pro ovládání:**

- **Přepínání mezi prvky okna:** `Tab` / `Shift+Tab`
- **Hledat na stránce:** `Ctrl+Shift+F`
- **Přejít na další/předchozí výsledek hledání:** `F3` / `Shift+F3`
- **Zobrazit vybraný výsledek v kontextu kapitoly:** `Ctrl+Q`
- **Otevřít vybraný výsledek v hlavním okně:** `Enter`
- **Otevřít vybraný výsledek v nové záložce:** `Ctrl+Enter`
- **Zavřít okno vyhledávání:** `Esc`
- **Otevřít nápovědu:** `F1`

---

### Okno plánů čtení

Okno plánů čtení slouží k práci s plány čtení Bible a sledování postupu. Umožňuje označovat přečtené dny a úryvky, přepínat mezi dny plánu, měnit překlady a prohlížet obsah každého dne.

**Hlavní prvky:**

- **Rozbalovací seznam dnů** pro výběr konkrétního dne plánu.
- **Seznam čtení** pro vybraný den.
- **Textové pole** pro zobrazení textu vybraného úryvku.

**Klávesy pro ovládání:**

- **Přepínání mezi prvky okna:** `Tab` / `Shift+Tab`
- **Označit den nebo úryvek jako přečtený/nepřečtený:** `Mezerník`
- **Změnit překlad:** `T` / `Shift+T`
- **Změnit plán čtení:** `Ctrl+Tab` / `Ctrl+Shift+Tab`
- **Posunout kurzor o 5 veršů zpět/vpřed:** `PageUp` / `PageDown`
- **Posunout kurzor o 10 veršů zpět/vpřed:** `Ctrl+PageUp` / `Ctrl+PageDown`
- **Přejít na verš:** číslice `0–9`
- **Zvětšit velikost písma:** `Ctrl++`
- **Zmenšit velikost písma:** `Ctrl+-`
- **Zobrazit/skrýt čísla veršů:** `Ctrl+H`
- **Hledat na stránce:** `Ctrl+Shift+F`
- **Přejít na další/předchozí výsledek hledání:** `F3` / `Shift+F3`
- **Zavřít okno:** `Esc`
- **Nápověda:** `F1`

---

### Okno přechodu na odkaz a vytvoření nové záložky

Tato okna slouží k rychlému přechodu na konkrétní knihu, kapitolu nebo verš zadáním biblického odkazu a také k otevření nové záložky s danými parametry. Podporují různé formáty zadávání odkazů, včetně zkratek názvů knih, čísel kapitol a veršů. Seznam dostupných zkratek je uveden v nápovědě aplikace.

Přijímány jsou jak východní formát zápisu (např. "Jan 3:16"), tak západní formát ("Jan 3,16").

**Hlavní prvky:**

- **Pole pro zadání odkazu** (uchovává historii posledních přechodů).
- **Výchozí tlačítko** (otevírá Genesis, 1. kapitolu).
- **Tlačítko pro potvrzení přechodu**.

**Klávesy pro ovládání:**

- **Přejít na zadaný odkaz:** `Enter`
- **Zavřít okno:** `Esc`
- **Otevřít nápovědu:** `F1`

---

### Okno paralelních odkazů

Okno paralelních odkazů slouží k prohlížení a analýze paralelních míst a podobných kontextových biblických úryvků pro vybraný verš. To pomáhá hlouběji porozumět obsahu textu a vztahům mezi různými částmi Písma svatého.

**Hlavní prvky:**

- **Textové pole** se seznamem paralelních biblických míst.

**Klávesy pro ovládání:**

- **Hledat na stránce:** `Ctrl+Shift+F`
- **Přejít na další/předchozí výsledek hledání:** `F3` / `Shift+F3`
- **Zobrazit vybraný výsledek v kontextu kapitoly:** `Ctrl+Q`
- **Otevřít vybraný výsledek v hlavním okně:** `Enter`
- **Otevřít vybraný výsledek v nové záložce:** `Ctrl+Enter`
- **Zavřít okno:** `Esc`
- **Otevřít nápovědu:** `F1`

---

### Menu aplikace

Menu aplikace převážně duplikuje funkce klávesových zkratek a je určeno pro pohodlí uživatelů, kteří si nepamatují všechny kombinace kláves. Je dostupné v hlavním okně a v okně plánů čtení.

**Hlavní možnosti menu:**

- Provádění akcí dostupných pomocí klávesových zkratek.
- Správa nastavení zobrazení a záložek.
- Přístup k nastavení aplikace a nápovědě.

---

### Kontextové menu

Kontextové menu umožňuje rychle provádět základní akce s vybraným textem, aktuálním veršem nebo vybraným výsledkem vyhledávání v textu Bible.

Kontextové menu je dostupné:

- v **hlavním okně**,
- v **okně vyhledávání**,
- v **okně paralelních odkazů**.

Kontextové menu se otevře pomocí:

- `Shift+F10` nebo klávesy kontextového menu na klávesnici.

**Hlavní funkce kontextového menu:**

- **Rychlý náhled** – otevře vybraný výsledek v kontextu příslušné kapitoly.
- **Otevřít v aktuální záložce** – otevře vybrané místo v aktivní záložce.
- **Otevřít v nové záložce** – otevře vybrané místo v nové záložce.
- **Kopírovat** vybraný text nebo aktuální verš spolu s biblickým odkazem (v hlavním okně).
- **Otevřít seznam paralelních odkazů** pro aktuální verš (v hlavním okně).

---

### Nastavení

Sekce nastavení slouží ke správě hlavních parametrů aplikace, včetně překladů, plánů čtení, integrace s Gemini API a nastavení aktualizací.

**Hlavní možnosti:**

- **Správa překladů** (stahování a odstraňování).
- **Správa plánů čtení** (stahování, odstraňování a resetování postupu).
- **Zadání API klíče** pro povolení inteligentního vyhledávání.
- **Zapnutí/vypnutí** automatické kontroly aktualizací.

**Jak otevřít nastavení:**

- Prostřednictvím menu aplikace: **Nástroje → Nastavení**.
- Prostřednictvím nastavení NVDA: **NVDA+N → Parametry → Nastavení → Bible**.

---

### Licence

Aplikace "Bible" je šířena pod licencí **[GPL 2](https://www.gnu.org/licenses/gpl-2.0.html)**.