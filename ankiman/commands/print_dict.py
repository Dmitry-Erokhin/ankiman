import requests
from ankiman import ANKI_CONNECT_URL


def fetch_all_cards(deck_name):
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": f'deck:"{deck_name}"'}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()['result']


def get_note_info(note_ids):
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {"notes": note_ids}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    return response.json()['result']


def run_print_dict(deck):
    """Fetch and print base_d field from notes in the given deck."""
    note_ids = fetch_all_cards(deck)
    if not note_ids:
        print(f"No cards found in deck '{deck}'.")
        return
    notes = get_note_info(note_ids)
    for note in notes:
        fields = note.get("fields", {})
        if "base_d" in fields:
            print(fields["base_d"].get("value", ""))


