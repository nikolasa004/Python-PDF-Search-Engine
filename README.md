# PDF Search Engine - Python

A PDF search engine I developed in Python for a university data structures and algorithms project.

The main parts of the project are my own **Trie** and **directed graph** implementations. Each PDF page has a Trie for its words, while the graph represents references between pages. The program combines these structures to find and rank results, offer word suggestions, and export matching pages to a new PDF.

This started as a search tool for a specific textbook. I later fixed a few bugs and updated it to accept other PDF documents, while keeping the original algorithmic approach and command-line interface. Some of the code still reflects the way I was experimenting and learning at the time.

## Video demonstration

**[Watch the PDF Search Engine demo on YouTube](https://youtu.be/zhYy9SVIZeg)**

The video shows keyword and Boolean searches, phrase matching, autocomplete and spelling suggestions, and an exported PDF with highlighted matches. It uses a data structures textbook as the demonstration document; the book itself is not included in this repository.

## Screenshots

| Basic keyword search | Boolean search |
| :---: | :---: |
| ![Keyword search for data with ranked matching pages](docs/images/Screenshot%202026-10-23%20195821.png) | ![Boolean search using parentheses, AND and OR](docs/images/Screenshot%202026-10-23%20195909.png) |
| **Exact phrase search** | **Autocomplete and spelling suggestions** |
| ![Searching for the exact phrase data structures](docs/images/Screenshot%202026-10-23%20195940.png) | ![Trie autocomplete suggestions and corrections for misspelled words](docs/images/Screenshot%202026-10-23%20200129.png) |
| **Highlighted PDF export** | |
| ![Exported search result page with matching words highlighted in green](docs/images/Screenshot%202026-10-23%20200210.png) | |

## Features

- Keyword and multi-word searches with ranked results and matching text excerpts.
- Boolean queries with `AND`, `OR`, binary `NOT` (set difference), and parentheses.
- Quoted phrase searches, such as `"data structures"`.
- Prefix-based autocomplete through a Trie (for example, `alg*`).
- Spelling suggestions for words that may have been mistyped, using `fuzzywuzzy`.
- PDF export of up to ten top-ranked matching pages with green highlights on the searched terms.
- Index caching for individual PDF documents, so unchanged documents do not have to be indexed again every time.
- Recognition of some textual page references and internal PDF links for graph-based ranking.

## How it works

The program reads the text from each page using **PyMuPDF** and creates one graph node per PDF page. Each node contains a **Trie**, which stores words and their occurrence counts. This also supports searching for words by prefix.

The directed graph connects pages when the document contains recognizable page references or internal links. Search results are ranked using a custom heuristic combining word occurrences and page relationships. The graph idea is inspired by how linked pages can provide relevance signals, but **this is not an implementation of Google's PageRank algorithm**.

For Boolean expressions, the program converts the input into postfix notation and evaluates the operations using a stack. The `AND` and binary `NOT` operators have higher precedence than `OR`; parentheses can override that order.

The code is organized around the data structures and search algorithms rather than a graphical user interface.

## Running the project

You'll need **Python 3** and a PDF containing selectable/extractable text.

Clone or download the repository, open a terminal in its **root directory**, and install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

Then run:

```powershell
python "Projekat pretraga/pretraga.py"
```

The program will ask you for the path to a PDF file:

```text
Unesite putanju do PDF fajla:
```

You can also specify the PDF directly when launching the program:

```powershell
python "Projekat pretraga/pretraga.py" --pdf "C:\path\to\document.pdf"
```

Optional arguments:

- `--pdf`: select the document without being prompted.
- `--reindex`: rebuild its index instead of loading the cached one.
- `--page-offset 22`: map printed page references to their corresponding PDF pages using an offset. This was useful for the original textbook and is **not** needed for most documents.

For example:

```powershell
python "Projekat pretraga/pretraga.py" --pdf "C:\path\to\document.pdf" --reindex
```

On Windows you can use `py` instead of `python` if that is how Python is configured on your machine.

### Example queries

```text
data
python graph
(data OR python) AND graph
data NOT python
"data structures"
alg*
algoritm
```

After the first ten results of a search with more than ten matches, the program offers `sacuvaj` to export the first ten matching pages. The generated PDF is saved in `Projekat pretraga/Rezultati/`.

## Repository structure

```text
Python-PDF-Search-Engine/
├── Projekat pretraga/
│   ├── pretraga.py                 # Command-line interface and search flow
│   ├── pdf_modul.py                # PDF indexing, search, ranking and export
│   ├── trie.py                     # Trie implementation
│   ├── graf.py                     # Directed graph implementation
│   ├── obrada_logickih_izraza.py   # Boolean expression parsing
│   └── stek.py                     # Stack implementation
├── docs/
│   └── images/                     # Screenshots
├── requirements.txt
├── .gitignore
└── README.md
```

Generated indexes (`.cache/`), exported search results (`Rezultati/`), and input PDF documents are intentionally excluded from version control.

## Limitations and notes

- The PDF must contain an extractable text layer. Scanned image-only pages are not searchable without OCR, which is not part of this project.
- Graph references depend on the document: many PDFs have few or no recognizable links, and printed page numbers do not always match PDF page positions.
- This is a learning project, not a production search engine. Text extraction, exact phrase handling, and highlighting may be imperfect for unusual PDF layouts.
- The demonstration uses a third-party textbook for testing, but **no copy of that book or exported book pages is distributed in this repository**.

I wanted to preserve how I originally approached Trie structures, graphs, ranking and expression parsing, including some of the less elegant parts, rather than rewrite it into a completely different project.
