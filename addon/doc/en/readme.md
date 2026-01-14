# Bible

The application is designed for convenient study of the Holy Scriptures and provides advanced tools for navigation, search, and management of Bible translations. It allows you to easily navigate through the text, move between books, chapters, and verses, work with different translations, and compare biblical passages.

**Developer:** Alexandr Halimon

**Email:** [halimon.alexandr@gmail.com](mailto:halimon.alexandr@gmail.com)

**Repository:** [GitHub](https://github.com/Halimon-Alexandr/nvda-bible-plugin)

---

## Key Features

The application allows you to:

- Use a tab system to work with multiple Scripture texts simultaneously.
- Quickly navigate between books, chapters, verses, and translations.
- Copy verses and fragments with references.
- View parallel passages and contextually similar fragments.
- Use text search with filtering by books, chapters, or verses, including smart search via the Gemini API.
- Work with reading plans, track progress, and mark read passages.
- Download and remove translations for different languages and reading plans.

---

### Main Window

The main window contains:

- A **text field** with the Bible text, occupying most of the screen.
- **Three dropdown lists** for selecting the book, chapter, and translation.

The content of the text field corresponds to the selected parameters. The window title displays the current book, chapter, and translation, helping you quickly identify which passage is open.

**Open the window:** `NVDA+X`

*Note:* On the first launch, the settings window opens automatically. To start, you need to download at least one Bible translation, then close the settings and restart the application.

**Navigation and Control:**

- **Switch between dropdown lists and text:** `Tab` / `Shift+Tab`
- **Move to the next/previous book:** `B` / `Shift+B`
- **Move to the next/previous chapter:** `C` / `Shift+C`
- **Move to the next/previous translation:** `T` / `Shift+T`
- **Move the cursor 5 verses back/forward:** `PageUp` / `PageDown`
- **Move the cursor 10 verses back/forward:** `Ctrl+PageUp` / `Ctrl+PageDown`
- **Quick jump to a verse:** digits `0–9`

**Tab Management:**

- **Create a new tab:** `Ctrl+T`
- **Close the current tab:** `Ctrl+W`
- **Switch to the next/previous tab:** `Ctrl+Tab` / `Ctrl+Shift+Tab`
- **Go to tab 1–9:** `Ctrl+1` .. `Ctrl+9`

**View Settings:**

- **Show/hide verse numbers:** `Ctrl+H`
- **Increase/decrease font size:** `Ctrl++` / `Ctrl+-`

**Context-sensitive keys:**

- **Copy the current verse or selected text with a Bible reference:** `Ctrl+Shift+C`
- **Open the parallel references window for the current verse:** `Ctrl+Shift+L`

**Other Keys:**

- **Search on page:** `Ctrl+Shift+F`
- **Navigate to next / previous search result:** `F3` / `Shift+F3`
- **Search the Bible:** `Ctrl+F`
- **Reading plans:** `Ctrl+R`
- **Go to reference:** `Ctrl+L`
- **Close window:** `Alt+F4` or `Esc`
- **Help:** `F1`

---

### Search Window

The search window is designed to search for Bible verses by text in all books or selected chapters. It supports filtering by books, whole-word search, case sensitivity, and regular expressions. Smart search via the Gemini API is also available.

**Main Elements:**

- **Search query input field**
- **Search option checkboxes** (whole word, case sensitivity, regular expressions)
- **Search results list**

**Control Keys:**

- **Switch between window elements:** `Tab` / `Shift+Tab`
- **View the selected result in the context of the chapter:** `Ctrl+Q`
- **Open the selected result in the main window:** `Enter`
- **Open the selected result in a new tab:** `Ctrl+Enter`
- **Close the window:** `Esc`
- **Open help:** `F1`

---

### Reading Plans Window

The reading plans window is designed to work with Bible reading plans and track progress. It allows you to mark days and passages as read, switch between plan days, change translations, and view the content of each day.

**Main Elements:**

- **Dropdown list of days** to select a specific day of the plan.
- **Reading list** for the selected day.
- **Text field** to display the text of the selected passage.

**Control Keys:**

- **Switch between window elements:** `Tab` / `Shift+Tab`
- **Mark a day or passage as read/unread:** `Space`
- **Change translation:** `T` / `Shift+T`
- **Change reading plan:** `Ctrl+Tab` / `Ctrl+Shift+Tab`
- **Move the cursor 5 verses back/forward:** `PageUp` / `PageDown`
- **Move the cursor 10 verses back/forward:** `Ctrl+PageUp` / `Ctrl+PageDown`
- **Go to verse:** digits `0–9`
- **Increase font size:** `Ctrl++`
- **Decrease font size:** `Ctrl+-`
- **Show/hide verse numbers:** `Ctrl+H`
- **Search on page:** `Ctrl+Shift+F`
- **Navigate to next / previous search result:** `F3` / `Shift+F3`
- **Close window:** `Esc`
- **Help:** `F1`

---

### Reference Navigation and New Tab Window

These windows are designed for quick navigation to a specific book, chapter, or verse by entering a Bible reference, as well as opening a new tab with specified parameters. Various input formats are supported, including abbreviated book names, chapter, and verse numbers. A list of available abbreviations is provided in the application's help.

Both Eastern (e.g., "Jn. 3:16") and Western formats (e.g., "Jn 3, 16") are accepted.

**Main Elements:**

- **Reference input field** (saves history of recent navigations).
- **Default button** (opens Genesis, chapter 1).
- **Confirm navigation button**.

**Control Keys:**

- **Navigate to the entered reference:** `Enter`
- **Close window:** `Esc`
- **Open help:** `F1`

---

### Parallel References Window

The Parallel References window is designed for viewing and analyzing parallel passages and contextually related biblical excerpts for the selected verse. This helps to gain a deeper understanding of the text and the connections between different parts of the Holy Scripture.

**Main elements:**

- **Text field** containing a list of parallel biblical passages.

**Keyboard shortcuts**

- **View the selected result in the context of the chapter:** `Ctrl+Q`
- **Open the selected result in the main window:** `Enter`
- **Open the selected result in a new tab:** `Ctrl+Enter`
- **Close the window:** `Esc`
- **Open help:** `F1`

---

### Program Menu

The program menu largely duplicates the functions of hotkeys and is designed for the convenience of users who do not remember all key combinations. It is available in the main window and the reading plans window.

**Main Menu Features:**

- Perform actions available via hotkeys.
- Manage view settings and tabs.
- Access program settings and help.

---

### Context Menu

The context menu allows you to quickly perform common actions with selected text, the current verse, or a selected search result within the Bible text.

The context menu is available:

- in the **main window**;
- in the **search window**;
- in the **parallel references window**.

The context menu can be opened using:

- `Shift+F10` or the context menu key on the keyboard.

**Main context menu actions:**

- **Quick view** — opens the selected result in the context of the corresponding chapter.
- **Open in current tab** — opens the selected passage in the active tab.
- **Open in new tab** — opens the selected passage in a new tab.
- **Copy** — copies the selected text or the current verse together with the biblical reference (in the main window).
- **Open parallel references list** for the current verse (in the main window).

---

### Settings

The settings section is designed to manage the main program parameters, including translations, reading plans, Gemini API integration, and update settings.

**Main Features:**

- **Translation management** (download and delete).
- **Reading plan management** (download, delete, and reset progress).
- **API key input** to enable smart search.
- **Enable/disable** automatic update checks.

**How to Open Settings:**

- Via the program menu: **Tools → Settings**.
- Via NVDA settings: **NVDA+N → Preferences → Settings → Bible**.

---

### License

The "Bible" application is distributed under the **[GPL 2](https://www.gnu.org/licenses/gpl-2.0.html)** license.
