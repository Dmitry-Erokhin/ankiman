import click
import fitz  # PyMuPDF
import spacy
import random
import string
import requests
import json

# Load Spacy German model
nlp = spacy.load("de_core_news_lg")

def generate_execution_id(length=5):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def read_file(file_path):
    text = ""
    if file_path.endswith('.pdf'):
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
    elif file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    return text

def process_text(text):
    doc = nlp(text)
    words = {}
    for token in doc:
        if token.is_alpha:
            words[token.lemma_] = {
                "word": token.lemma_,
                "pos": token.pos_
            }
    return words

def check_in_anki(word, deck_name):
    query = {
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f"deck:{deck_name} base_d:{word}"
        }
    }
    response = requests.post("http://localhost:8765", json=query)
    result = response.json()
    return len(result['result']) > 0

def enrich_word_with_gpt(word, pos, chatgpt_token):
    prompt = f"Provide the following information for the German word '{word}' (part of speech: {pos}):\n"\
             "1. Article for noun (empty for other parts of speech).\n"\
             "2. Plural ending of the noun (empty for other parts of speech).\n"\
             "3. Full German form, including article and plural endings for nouns and tense forms for verbs.\n"\
             "4. Translation to English.\n"\
             "5. Used roots.\n"\
             "6. Example in German.\n"\
             "7. Translation to English of the example."
    
    headers = {
        "Authorization": f"Bearer {chatgpt_token}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "text-davinci-004",
        "prompt": prompt,
        "max_tokens": 200
    }
    
    response = requests.post("https://api.openai.com/v1/completions", headers=headers, json=data)
    result = response.json()
    text = result['choices'][0]['text'].strip().split('\n')
    
    return {
        "article": text[0].strip(),
        "plural_ending": text[1].strip(),
        "full_form": text[2].strip(),
        "translation": text[3].strip(),
        "roots": text[4].strip().split(', '),
        "example_de": text[5].strip(),
        "example_en": text[6].strip()
    }

def create_or_update_anki_card(deck_name, word_data, tags, execution_id):
    tags.append(f"A::Executions::{execution_id}")
    tags.append(f"S::POS::{word_data['pos']}")
    for root in word_data['roots']:
        tags.append(f"S::root:{root}")
    
    note = {
        "deckName": deck_name,
        "modelName": "Basic",
        "fields": {
            "full_d": word_data['full_form'],
            "base_e": word_data['translation'],
            "base_d": word_data['word'],
            "article_d": word_data['article'],
            "s1": word_data['example_de'],
            "s1e": word_data['example_en']
        },
        "tags": tags
    }
    
    query = {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": note
        }
    }
    response = requests.post("http://localhost:8765", json=query)
    return response.json()

@click.command()
@click.option('-o', '--file', required=True, type=click.Path(exists=True), help='Path to PDF or TXT file.')
@click.option('-d', '--deck', required=True, type=str, help='Name of the resulting deck.')
@click.option('-t', '--tags', multiple=True, type=str, help='Tags to add.')
@click.option('-g', '--gpt-token', required=True, type=str, help='ChatGPT token.')
@click.option('-u', '--update', is_flag=True, help='Update flag.')
def main(file, deck, tags, gpt_token, update):
    execution_id = generate_execution_id()
    print(f"Execution ID: {execution_id}")

    # Step 1: Read and process text
    text = read_file(file)
    words = process_text(text)
    print(f"Words extracted: {words}")

    # Step 3: Make words unique
    unique_words = {word: data for word, data in words.items()}
    print(f"Unique words: {unique_words}")

    if not update:
        # Step 4: Check if word is in Anki
        unique_words = {word: data for word, data in unique_words.items() if not check_in_anki(word, deck)}
        print(f"Words after Anki check: {unique_words}")

    for word, data in unique_words.items():
        # Step 5 and 6: Enrich word with additional information
        enriched_data = enrich_word_with_gpt(word, data['pos'], gpt_token)
        data.update(enriched_data)
        print(f"Enriched data for word '{word}': {data}")

        # Step 7: Create or update Anki card
        result = create_or_update_anki_card(deck, data, list(tags), execution_id)
        print(f"Anki update result for '{word}': {result}")

    # Step 8: Print results on processing
    print("Processing complete.")

if __name__ == "__main__":
    main()
