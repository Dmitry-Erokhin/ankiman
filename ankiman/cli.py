#!/usr/bin/env python
import click
import requests
from ankiman import ANKI_CONNECT_URL

def ensure_anki_or_fail(ctx):
    try:
        response = requests.get(ANKI_CONNECT_URL)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        click.echo("Anki is not accessible. Ensure Anki is running and AnkiConnect is installed.")
        ctx.abort()

# Delegate processing to commands modules
from ankiman.commands.process_file import run_process_file
from ankiman.commands.print_dict import run_print_dict
from ankiman.commands.tag_freq import run_tag_freq


@click.group()
@click.pass_context
def cli(ctx):
    """Ankiman - A tool for managing German vocabulary in Anki.
    
    This CLI tool provides various commands to process text files, manage word frequencies,
    and handle German vocabulary in Anki decks.
    """
    pass


@cli.command("process-file")
@click.option('-f', '--file', required=True, type=click.Path(exists=True), 
              help='Path to a PDF or TXT file containing German text to process')
@click.option('-d', '--deck', required=True, 
              help='Name of the Anki deck where cards will be checked/tagged')
@click.option('-t', '--tags', multiple=True, required=True, 
              help='Tags to add to the processed words. Can be specified multiple times')
@click.option('-b', '--batch', default=100, 
              help='Number of words to include in each ChatGPT prompt (default: 100)')
def process_file_cmd(file, deck, tags, batch):
    """Process a text file to extract German vocabulary.

    This command reads a PDF or TXT file, extracts German words, checks if they exist
    in the specified Anki deck, and generates prompts for creating new cards for missing words.
    It will also add specified tags to existing cards.

    Example usage:
    ankiman process-file -f text.pdf -d "German::Vocabulary" -t source::book -t level::b1
    """
    ensure_anki_or_fail(cli)
    run_process_file(file, deck, tags, batch)


@cli.command("print-dict")
@click.option('-d', '--deck', required=True, 
              help='Name of the Anki deck to extract words from')
def print_dict_cmd(deck):
    """Print all base German words from an Anki deck.

    This command extracts and prints the base form (base_d field) of all words
    from the specified Anki deck. Useful for creating word lists or checking
    deck contents.

    Example usage:
    ankiman print-dict -d "German::Vocabulary" > wordlist.txt
    """
    ensure_anki_or_fail(cli)
    run_print_dict(deck)


@cli.command("tag-freq")
@click.option('-d', '--deck', required=True, 
              help='Name of the Anki deck to process')
@click.option('-p', '--prefix', default='freq', 
              help='Prefix for frequency tags (default: "freq")')
@click.option('-w', '--word', 
              help='Process a specific word instead of the entire deck')
@click.option('--word-list', 
              help='Process multiple words (comma-separated) instead of the entire deck')
def tag_freq_cmd(deck, prefix, word, word_list):
    """Tag words with their frequency level in German.

    This command analyzes words in the deck and adds frequency tags (very-high,
    high, moderate, or low) based on their usage frequency in the German language.
    You can process the entire deck, a single word, or a list of words.

    Tags will be in the format: prefix::frequency-level
    (e.g., freq::high, freq::moderate)

    Example usage:
    Process entire deck:
    ankiman tag-freq -d "German::Vocabulary"

    Process single word:
    ankiman tag-freq -d "German::Vocabulary" -w "Haus"

    Process multiple words:
    ankiman tag-freq -d "German::Vocabulary" --word-list "Haus,Auto,Buch"
    """
    ensure_anki_or_fail(cli)
    run_tag_freq(deck, prefix, word, word_list)


if __name__ == "__main__":
    cli()
