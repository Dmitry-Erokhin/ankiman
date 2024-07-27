import re
import click
import spacy
import requests
import fitz


ALLOWED_POS = ('ADJ', 'ADV', 'NOUN', 'PART', 'SCONJ', 'VERB')

BASE_PROMPT = """
Here is the list of German words: 
%words%. 

You need to create CSV file from them with following columns (in brackets examnple for words `Hauptbahnhof` and `aufhören`):
- `base` - word itself (e.g. `Hauptbahnhof`, `aufhören`)
- `full` - full form of German word: for nouns with article and plural ending; for vebs - tenses (`der Hauptbahnhof, -e`, `aufhören, hört auf, hörte auf, hat aufgehört`)
- `plural_postfix` - only for nouns: postfixin plural form (` -e`, ``)
- `article` - only for nouns: definitive article (`der`, ``)
- `translation` - translation to english (`main train station`, `to stop`)
- `-` - empty column
- `-` - empty column
- `-` - empty column
- `example` - example in german (`Treffen wir uns am Hauptbahnhof?`, `Es hört nicht auf zu schneien.`)
- `example_translation` - translation to english of example in German (`Do we meet at the main station?`, `It does not stop snowing.`)
- `-` - empty column
- `-` - empty column
- `-` - empty column
- `-` - empty column
- `tags` - fixed value for each row: `%tags%`

Make output pipe(`|`) separated. Do NOT use python scripting, calculate it yourself. Provide data in code block.

Example:
```
base|full|plural_postfix|article|translation|example|example_translation|-|-|-|-|tags
Hauptbahnhof|der Hauptbahnhof, -e|-e|der|main train station|Treffen wir uns am Hauptbahnhof?|Do we meet at the main station?|||||%tags%
aufhören|aufhören, hört auf, hörte auf, hat aufgehört|||to stop|Es hört nicht auf zu schneien.|It does not stop snowing.|||||%tags%
```
"""

# Function to check if Anki is accessible
def check_anki_accessible():
    try:
        response = requests.get("http://localhost:8765")
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False

# Function to read text from PDF file using PyMuPDF
def read_pdf(file_path):
    text = ""
    document = fitz.open(file_path)
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    return text

# Function to read text from TXT file
def read_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Function to process words into base forms
def process_words(nlp, text): #TODO: check why not processing word `wichtigen`
    doc = nlp(text)
    words = set()
    for token in doc:
        if token.pos_ in ALLOWED_POS: # Only allowed pos
            if re.match("^[a-zA-ZäöüÄÖÜß-]+$", token.lemma_):  # Consider only alphabetic tokens
                words.add(token.lemma_)
    return list(words)

# Function to check if words are present in Anki
def check_words_in_anki(words, deck):
    words_present = set()
    words_absent = set(words)

    for word in words:
        query = {
            "action": "findNotes",
            "version": 6,
            "params": {"query": f"deck:{deck} base:{word}"}
        }
        response = requests.post("http://localhost:8765", json=query)
        if response.status_code == 200:
            note = response.json()
            if note['result']:
                words_present.add(word)
                words_absent.discard(word)
        else:
            print(f"Failed to check word: {word}")

    return list(words_present), list(words_absent)

# Function to add tags to existing Anki notes
def add_tags_to_anki(words_present, tags):
    tag_str = " ".join(tags)
    for word in words_present:
        query = {
            "action": "findNotes",
            "version": 6,
            "params": {
                "query": f"base:{word}"
            }
        }
        response = requests.post("http://localhost:8765", json=query)
        if response.status_code == 200:
            note_ids = response.json()['result']
            if note_ids:
                note_id = note_ids[0]
                query = {
                    "action": "addTags",
                    "version": 6,
                    "params": {
                        "notes": [note_id],
                        "tags": tag_str
                    }
                }
                requests.post("http://localhost:8765", json=query)

# Function to create ChatGPT prompt
def create_chatgpt_prompts(words_absent, tags, batch_size):
    prompts = []
    for i in range(0, len(words_absent), batch_size):
        batch = words_absent[i:i+batch_size]
        prompt = BASE_PROMPT.replace("%tags%", " ".join(tags)).replace("%words%","\n".join(batch))
        prompts.append(prompt)
    return prompts

@click.command()
@click.option('-f', '--file', required=True, type=click.Path(exists=True), help='Path to PDF or TXT file')
@click.option('-d', '--deck', required=True, help='Name of the resulting deck')
@click.option('-t', '--tags', multiple=True, required=True, help='Tags to add')
@click.option('-b', '--batch', default=100, help='Prompt batch size')
def main(file, deck, tags, batch):
    # Check if Anki is accessible
    if not check_anki_accessible():
        print("Anki is not accessible. Make sure Anki is running and AnkiConnect is installed.")
        exit(1)

    # Read text from file
    if file.lower().endswith('.pdf'):
        text = read_pdf(file)
    elif file.lower().endswith('.txt'):
        text = read_txt(file)
    else:
        print("Unsupported file format. Only PDF and TXT are supported.")
        exit(1)

    # Load Spacy model for German language
    nlp = spacy.load('de_core_news_lg')

    # Process words into base forms
    words = process_words(nlp, text)
    print(f"Total unique words: {len(words)}")

    # Check if words are present in Anki
    words_present, words_absent = check_words_in_anki(words, deck)
    print(f"{len(words_present)} words present in Anki, {len(words_absent)} words missing")

    # Add tags to existing Anki notes
    add_tags_to_anki(words_present, tags)
    print(f"Tagged {len(words_present)} words in Anki with tags: {tags}")

    # Create ChatGPT prompts for words absent in Anki
    prompts = create_chatgpt_prompts(words_absent, tags, batch)
    print(f"Use following {len(prompts)} prompt(s) to create Anki cards for {len(words_absent)} words missing in Anki.\n")

    for i, prompt in enumerate(prompts, 1):
        print(f"==============Prompt #{i} of {len(prompts)}==============")
        print(prompt)
        print("==========================================================\n")

if __name__ == "__main__":
    main()
