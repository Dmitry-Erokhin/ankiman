import re
import spacy
import requests
import fitz
from ankiman import ANKI_CONNECT_URL

ALLOWED_POS = ('ADJ', 'ADV', 'NOUN', 'PART', 'SCONJ', 'VERB')

BASE_PROMPT = """
Here is the list of German words: 
%words%. 

You need to create CSV file from them with following columns (e.g. for words `Hauptbahnhof` and `aufhören`):
- base: word itself
- full: full form (for nouns with article and plural ending; for verbs - tenses)
- plural_postfix: postfix in plural form (if applicable)
- article: definitive article for nouns
- translation: translation to English
- -: empty column
- -: empty column
- -: empty column
- example: example in German
- example_translation: translation of example
- -: empty column
- -: empty column
- -: empty column
- -: empty column
- tags: fixed value for each row: %tags%

Provide output pipe(|) separated in a code block.

Example:
```
base|full|plural_postfix|article|translation|-|-|-|example|example_translation|-|-|-|-|tags
Hauptbahnhof|der Hauptbahnhof, -e|-e|der|main train station|-|-|-|Treffen wir uns am Hauptbahnhof?|Do we meet at the main station?|||||%tags%
aufhören|aufhören, hört auf, hörte auf, hat aufgehört|||to stop|-|-|-|Es hört nicht auf zu schneien.|It does not stop snowing.|||||%tags%
```"""

def ensure_spacy_model():
    try:
        spacy.load("de_core_news_lg")
    except OSError:
        print("Downloading spaCy model de_core_news_lg...")
        spacy.cli.download("de_core_news_lg")


def read_pdf(file_path):
    """Read text from a PDF file using PyMuPDF."""
    text = ""
    document = fitz.open(file_path)
    for page in document:
        text += page.get_text()
    return text


def read_txt(file_path):
    """Read text from a TXT file using UTF-8 encoding."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def process_words(nlp, text):
    """Extract allowed tokens from text and return unique lemmas."""
    doc = nlp(text)
    words = {token.lemma_ for token in doc if token.pos_ in ALLOWED_POS and re.match(r'^[a-zA-ZäöüÄÖÜß-]+$', token.lemma_)}
    return list(words)


def check_words_in_anki(words, deck):
    """Check if words are present in Anki; return present and absent lists."""
    words_present = set()
    words_absent = set(words)

    for word in words:
        query = {
            "action": "findNotes",
            "version": 6,
            "params": {"query": f"deck:{deck} base:{word}"}
        }
        response = requests.post(ANKI_CONNECT_URL, json=query)
        if response.status_code == 200 and response.json().get('result'):
            words_present.add(word)
            words_absent.discard(word)
        else:
            print(f"Failed to check word: {word}")
    return list(words_present), list(words_absent)


def add_tags_to_anki(words_present, tags):
    """Add tags to notes in Anki for the given words."""
    tag_str = " ".join(tags)
    for word in words_present:
        query = {
            "action": "findNotes",
            "version": 6,
            "params": {"query": f"base:{word}"}
        }
        response = requests.post(ANKI_CONNECT_URL, json=query)
        note_ids = response.json().get('result') if response.status_code == 200 else []
        if note_ids:
            note_id = note_ids[0]
            query = {
                "action": "addTags",
                "version": 6,
                "params": {"notes": [note_id], "tags": tag_str}
            }
            requests.post(ANKI_CONNECT_URL, json=query)


def create_chatgpt_prompts(words_absent, tags, batch_size):
    """Create ChatGPT prompts for words absent in Anki."""
    prompts = []
    for i in range(0, len(words_absent), batch_size):
        batch = words_absent[i:i+batch_size]
        prompt = BASE_PROMPT.replace("%tags%", " ".join(tags)).replace("%words%", "\n".join(batch))
        prompts.append(prompt)
    return prompts

def run_process_file(file, deck, tags, batch):
    """Process the file, integrate with Anki, and output ChatGPT prompts."""
    ensure_spacy_model()
    if file.lower().endswith('.pdf'):
        text = read_pdf(file)
    elif file.lower().endswith('.txt'):
        text = read_txt(file)
    else:
        print("Unsupported file format. Only PDF and TXT are supported.")
        exit(1)

    nlp = spacy.load('de_core_news_lg')
    words = process_words(nlp, text)
    print(f"Total unique words: {len(words)}")

    words_present, words_absent = check_words_in_anki(words, deck)
    print(f"{len(words_present)} words present in Anki, {len(words_absent)} missing")

    add_tags_to_anki(words_present, tags)
    print(f"Tagged {len(words_present)} words with tags: {tags}")

    prompts = create_chatgpt_prompts(words_absent, tags, batch)
    print(f"{len(prompts)} prompt(s) created for {len(words_absent)} missing words.\n")

    for i, prompt in enumerate(prompts, 1):
        print(f"==============Prompt #{i} of {len(prompts)}==============")
        print(prompt)
        print("==========================================================\n")

# For testing purposes
if __name__ == "__main__":
    file_path = "temp/in.txt"
    deck = "DE::Classes::B1-prep"
    tags = ["test"]
    batch_size = 50
    run_process_file(file_path, deck, tags, batch_size)
