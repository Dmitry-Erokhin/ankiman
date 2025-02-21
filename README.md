# Ankiman

A CLI tool for managing German vocabulary in Anki.

## Features

- **Process Text Files**: Extract German words from PDF or TXT files and prepare them for Anki import
- **Word Frequency Tagging**: Automatically tag words with their frequency level in German
- **Dictionary Management**: Export word lists from your Anki decks


## Prerequisites

- Python 3.9 or higher up to 3.13 (exclusive)
- Anki with [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on installed
- Anki must be running when using Ankiman


## Installation

The recommended way to install Ankiman is using `pipx`:

```bash
# Install pipx if you haven't already
python -m pip install --user pipx
python -m pipx ensurepath

# Install Ankiman
pipx install git+https://github.com/Dmitry-Erokhin/ankiman.git
```

## Note Format

As a foundation [shared deck "B1 Wortliste DTZ Goethe"](https://ankiweb.net/shared/info/1586166030) is used therefore Ankiman is expecting fields provided by this deck:

- `full_d`: Full form of the word (for nouns with article and plural ending; for verbs - tenses)
- `base_e`: English translation
- `base_d`: Base form of the word
- `artikel_d`: Definitive article for nouns
- `plural_d`: Plural form postfix (if applicable)
- `s1`: Example sentence in German
- `s1e`: Translation of the example sentence

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.