import requests
from wordfreq import word_frequency
from ankiman import ANKI_CONNECT_URL

# Frequency thresholds for German words
FREQ_THRESHOLDS = {
    'very-high': 0.0001,  # Very common words
    'high': 0.00001,      # Common words
    'moderate': 0.000001, # Moderately common words
    # Below moderate is considered 'low'
}


def fetch_cards(deck_name, word=None):
    """Fetch cards from the specified deck, optionally filtered by word."""
    query = f'deck:"{deck_name}"'
    if word:
        query += f' base_d:"{word}"'

    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": query}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()['result']


def get_note_info(note_ids):
    """Get detailed information about notes."""
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {"notes": note_ids}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()['result']


def get_frequency_tag(freq, prefix):
    """Determine frequency tag based on word frequency."""
    for level, threshold in FREQ_THRESHOLDS.items():
        if freq >= threshold:
            return f"{prefix}::{level}"
    return f"{prefix}::low"


def update_note_tags(note_id, tags_to_add, prefix):
    """Update note tags, removing old frequency tags and adding new ones."""
    # First, get current tags
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {"notes": [note_id]}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    current_tags = response.json()['result'][0]['tags']
    
    # Remove old frequency tags
    updated_tags = [tag for tag in current_tags if not tag.startswith(f"{prefix}::")]
    
    # Add new frequency tags
    updated_tags.extend(tags_to_add)
    
    # Update the note
    payload = {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                "tags": updated_tags
            }
        }
    }
    requests.post(ANKI_CONNECT_URL, json=payload)


def process_word(word, prefix):
    """Calculate frequency and determine appropriate tag for a word."""
    freq = word_frequency(word, 'de')
    return get_frequency_tag(freq, prefix)


def run_tag_freq(deck, prefix, word=None, word_list=None):
    """Main function to process words and update frequency tags."""
    # Process specific words if provided
    if word_list:
        words_to_process = [w.strip() for w in word_list.split(',')]
    elif word:
        words_to_process = [word]
    else:
        # Process all cards in deck
        note_ids = fetch_cards(deck)
        notes = get_note_info(note_ids)
        words_to_process = [note['fields']['base_d']['value'] for note in notes if 'base_d' in note['fields']]

    print(f"Processing {len(words_to_process)} words...")
    
    for current_word in words_to_process:
        # Fetch notes for this word
        note_ids = fetch_cards(deck, current_word)
        if not note_ids:
            print(f"No cards found for word: {current_word}")
            continue

        # Calculate frequency and determine tag
        freq_tag = process_word(current_word, prefix)
        
        # Update tags for each note
        for note_id in note_ids:
            update_note_tags(note_id, [freq_tag], prefix)
            print(f"Updated '{current_word}' with tag: {freq_tag}")

# For testing purposes
if __name__ == "__main__":
    deck = "DE::Classes::B1-prep"
    prefix = "freq"
    word = "Ampel"
    run_tag_freq(deck, prefix, word)