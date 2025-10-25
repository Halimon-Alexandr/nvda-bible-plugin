## Bible

**Developer Oleksandr Halimon:** [halimon.alexandr@gmail.com](mailto:halimon.alexandr@gmail.com)
**Homepage:** [GitHub](https://github.com/Halimon-Alexandr/nvda-bible-plugin)
**File Link:** [bible.nvda-addon](https://github.com/Halimon-Alexandr/nvda-bible-plugin/releases/latest/download/bible.nvda-addon)

Welcome to our application — your reliable assistant in studying the Word of God!

The Bible is a tool designed to work with the texts of Scripture.

However, unlike most similar programs, our application offers a fully accessible interface optimized for non-visual access.

It consists of a main window designed to display Scripture text, as well as control elements for changing the book, chapter, and translation.

In addition to the main window, the application contains several auxiliary dialog windows that provide additional features — in particular, quick search for words or phrases in the text, navigation to a Bible reference, and viewing parallel passages of Scripture.

The program window opens using the key combination **NVDA+x**.

At the **first launch** of the application, the settings window opens automatically. In this window, you need to select **at least one Bible translation** from the list of available options and click the **"OK"** button to save your choice and continue working.

> **Important:** Without selecting a translation, working with Bible texts will be impossible.

Later, this window can be opened through **NVDA settings**:

NVDA Menu (**NVDA+N** → **Preferences** → **Settings** → **Bible**).

### Main Window

It contains four main elements: a large text field for displaying the Bible text, which occupies most of the screen, and three dropdown lists for selecting the book, chapter, and translation.

Additionally, the main program window can contain extra tabs, each of which can independently open a different book, chapter, or translation.

The text field displays the selected Bible passage according to the specified parameters, and the window title always shows the book name, chapter number, current translation, and tab number, helping you orient yourself in the current state of the program.

#### Text Navigation

Standard navigation keys are used to move through the text,

as well as additional combinations for navigating through verses:

- **PageDown** and **PageUp** — move the cursor forward or backward by 5 verses.
- **Ctrl+PageDown** and **Ctrl+PageUp** — move the cursor forward or backward by 10 verses.
- Pressing any digit in the text field moves the cursor to the specified verse. If you need to move the cursor to a verse consisting of two digits (e.g., 12 or 45), you need to quickly press the corresponding keys on the keyboard.

#### Switching Between Elements in the Main Window

To navigate between interface elements (text field and selection lists), you can use:

- **Tab** — move to the next element.
- **Shift+Tab** — move to the previous element.

Hotkeys are also available for changing the book, chapter, and translation:

- **B** — next book
- **Shift+B** — previous book
- **C** — next chapter
- **Shift+C** — previous chapter
- **T** — next translation
- **Shift+T** — previous translation

#### Context Menu

To open the context menu for the selected verse, press the **Applications** key or **Shift+F10**.

The context menu offers the following actions:

- View **parallel passages**.
- **Copy** the current verse with a reference, or a range of verses if multiple are selected.

#### Other Key Combinations

- **Ctrl+F** — open the Bible search window.
- **Ctrl+L** — go to a location by Bible reference.
- **Ctrl+T** — create a new tab.
- **Ctrl+1–9** — go to the tab with the corresponding number.
- **Ctrl+Tab** / **Ctrl+Shift+Tab** — cycle through tabs.
- **Ctrl+F4** or **Ctrl+W** — close the current tab.
- **Alt+F4** or **Esc** — close the main program window.


### Search Window  

The search window offers more controls than the main window, enabling flexible text searches within the Bible.  

#### Controls:  
- **Results Text Field** -Displays search results after entering a query.  
- **Search Query Field** -Stores the last 10 queries for quick access.  
- **Search Category Dropdown** -Available categories: "All Books," "None of the Books," "Old Testament Books," "New Testament Books." Selecting a category automatically marks the corresponding group of books in the book list.  
- **Bible Book Dropdown** -Allows selecting specific books for the search. By default, the number of selected books depends on the chosen category.  

#### Additional Search Options:  
- **Checkboxes for Search Options:**  
  - **Whole Word Search** -Searches for exact word matches.  
  - **Case-Sensitive** -Enables case sensitivity.  
  - **Regular Expression** -Allows using regex for advanced searches.  
  - **AI search** -uses the Gemini model to perform semantic search. Requires an API key.  
  - **"Search" Button** -Initiates the search. Pressing **Enter** in the query field also starts the search.  

#### Additional Features:  

Pressing the Enter key on a selected result in the search results field opens that text in the current tab of the main program window, while Ctrl+Enter opens it in a new tab, automatically closing the search window.

- The search window can also be closed using **Alt+F4** or **Esc**.  

### Parallel References Window

The Parallel References window allows you to view biblical passages that thematically or contextually correspond to the verse on which this window was invoked.

It opens through the context menu of the relevant verse.

The window consists of two main elements:

**List of References** — contains a list of biblical locations that are parallel to the current verse.

When the selected item in the list changes, the text of the chapter containing the corresponding reference is automatically updated below.

**Text Field** — displays the full text of the chapter in which the selected verse is located.

The focus is automatically set to the corresponding verse so that it can be read immediately.

Navigation in the text window is available using the same keys as in the main program window:

- **PageDown / PageUp** — move forward or backward by 5 verses.
- **Ctrl+PageDown / Ctrl+PageUp** — move forward or backward by 10 verses.
- Entering a digit or multiple digits — jump to the verse with the corresponding number.

The window title displays the scripture location to which the current parallel references belong, as well as the number of references found.

To open the selected location, you can press:
- **Enter** — opens the selected reference in the current tab.
- **Ctrl+Enter** — opens the selected reference in a new tab.

The window can be closed using the **Esc** or **Alt+F4** keys.

### Go to Reference Window

The Go to Reference window opens with the key combinations **Ctrl+L** or **Ctrl+T**.

The difference between them is that the first command opens the entered reference in the current tab, while the second opens it in a new tab.

The window consists of the following elements:

**Field for Entering Verse Reference** — accepts a verse reference in abbreviated form.

Supports a history of the last 10 transitions, allowing you to quickly return to recently opened places in the text.

Both Eastern format ("Jn. 3:16") and Western format ("Jn 3, 16") are accepted.

- **"Default"** button opens the initial location — Genesis, chapter 1, verse 1.
- **"Open"** button opens the specified reference.
- **"Cancel"** button closes the window without performing the transition.

The window can also be closed using the **Alt+F4** or **Esc** keys.

#### Bible Book Abbreviations  

The following abbreviations are used:  

- "Gen" -Genesis  
- "Ex" -Exodus  
- "Lev" -Leviticus  
- "Num" -Numbers  
- "Deut" -Deuteronomy  
- "Josh" -Joshua  
- "Judg" -Judges  
- "Ruth" -Ruth  
- "1Sam" -1 Samuel  
- "2Sam" -2 Samuel  
- "1Kgs" -1 Kings  
- "2Kgs" -2 Kings  
- "1Chr" -1 Chronicles  
- "2Chr" -2 Chronicles  
- "Ezra" -Ezra  
- "Neh" -Nehemiah  
- "Est" -Esther  
- "Job" -Job  
- "Ps" -Psalms  
- "Prov" -Proverbs  
- "Eccl" -Ecclesiastes  
- "Song" -Song of Songs  
- "Isa" -Isaiah  
- "Jer" -Jeremiah  
- "Lam" -Lamentations  
- "Ezek" -Ezekiel  
- "Dan" -Daniel  
- "Hos" -Hosea  
- "Joel" -Joel  
- "Amos" -Amos  
- "Obad" -Obadiah  
- "Jonah" -Jonah  
- "Mic" -Micah  
- "Nah" -Nahum  
- "Hab" -Habakkuk  
- "Zeph" -Zephaniah  
- "Hag" -Haggai  
- "Zech" -Zechariah  
- "Mal" -Malachi  
- "Mt" -Matthew  
- "Mk" -Mark  
- "Lk" -Luke  
- "Jn" -John  
- "Acts" -Acts  
- "Rom" -Romans  
- "1Cor" -1 Corinthians  
- "2Cor" -2 Corinthians  
- "Gal" -Galatians  
- "Eph" -Ephesians  
- "Phil" -Philippians  
- "Col" -Colossians  
- "1Thess" -1 Thessalonians  
- "2Thess" -2 Thessalonians  
- "1Tim" -1 Timothy  
- "2Tim" -2 Timothy  
- "Titus" -Titus  
- "Phlm" -Philemon  
- "Heb" -Hebrews  
- "Jas" -James  
- "1Pet" -1 Peter  
- "2Pet" -2 Peter  
- "1Jn" -1 John  
- "2Jn" -2 John  
- "3Jn" -3 John  
- "Jude" -Jude  
- "Rev" -Revelation  

### License  

The "Bible" app is distributed under the **[GPL 2](https://www.gnu.org/licenses/gpl-2.0.html)** license.  `;
  