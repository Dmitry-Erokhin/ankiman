import re
import spacy
import requests
from ankiman import ANKI_CONNECT_URL

ALLOWED_POS = ('ADJ', 'ADV', 'NOUN', 'PART', 'SCONJ', 'VERB')

def ensure_spacy_model():
    try:
        spacy.load("de_core_news_lg")
    except OSError:
        print("Downloading spaCy model de_core_news_lg...")
        spacy.cli.download("de_core_news_lg")


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
            "params": {"query": f"deck:{deck} base_d:{word}"}
        }
        response = requests.post(ANKI_CONNECT_URL, json=query)
        if response.status_code == 200:
            if response.json().get('result'):
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
            "params": {"query": f"base_d:{word}"}
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


def run_process_text(content, deck, tags):
    """Process the text, integrate with Anki, and output results."""
    ensure_spacy_model()
    
    nlp = spacy.load('de_core_news_lg')
    words = process_words(nlp, content)
    print(f"Total unique words: {len(words)}")

    words_present, words_absent = check_words_in_anki(words, deck)
    print(f"{len(words_present)} words present in Anki, {len(words_absent)} missing")

    add_tags_to_anki(words_present, tags)
    print(f"Tagged {len(words_present)} words with tags: {', '.join(tags)}")
    
    if words_absent:
        print(f"\nMissing words ({len(words_absent)}):")
        for word in sorted(words_absent):
            print(f"  - {word}")

# For testing purposes
if __name__ == "__main__":
    example_text = "Der Hund ist braun. Die Katze ist schwarz."
    deck = "DE::Classes::B1-prep"
    tags = ["test"]
    run_process_text(example_text, deck, tags)