#!/usr/bin/env python
import sys
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
from ankiman.commands.process_text import run_process_text
from ankiman.commands.print_dict import run_print_dict
from ankiman.commands.tag_freq import run_tag_freq

def read_pdf(file_path):
    """Read text from a PDF file using PyMuPDF."""
    import fitz
    text = ""
    document = fitz.open(file_path)
    for page in document:
        text += page.get_text()
    return text

def read_txt(file_path):
    """Read text from a TXT file using UTF-8 encoding."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def read_stdin():
    """Read text from standard input."""
    return sys.stdin.read()

@click.group()
@click.pass_context
def cli(ctx):
    """Ankiman - A tool for managing German vocabulary in Anki.
    
    This CLI tool provides various commands to process text files, manage word frequencies,
    and handle German vocabulary in Anki decks.
    """
    pass

@cli.command("process-text")
@click.argument('text', required=False)
@click.option('-f', '--file', type=click.Path(exists=True), 
              help='Path to a PDF or TXT file containing German text to process')
@click.option('-d', '--deck', required=True, 
              help='Name of the Anki deck where cards will be checked/tagged')
@click.option('-t', '--tags', multiple=True, required=True, 
              help='Tags to add to the processed words. Can be specified multiple times')
@click.pass_context
def process_text_cmd(ctx, text, file, deck, tags):
    """Process German text to extract vocabulary for Anki.

    This command extracts German words from text, checks if they exist in your Anki deck,
    adds tags to existing cards, and lists missing words that are not in your deck.
    
    Text can be provided in three ways:

    1. As a direct argument:
        \b
        ankiman process-text -d "German::Vocabulary" -t source::example "Der Hund ist braun"

    2. From a file (PDF or TXT):
        \b
        ankiman process-text -f text.pdf -d "German::Vocabulary" -t source::book
        ankiman process-text -f text.txt -d "German::Vocabulary" -t source::article

    3. From stdin (pipe):
        \b
        cat text.txt | ankiman process-text -d "German::Vocabulary" -t source::text
        echo "Das ist ein Beispiel" | ankiman process-text -d "German::Vocabulary" -t source::example

    Tags (-t) can be specified multiple times to categorize the vocabulary:
        \b
        ankiman process-text -d "German::Vocabulary" -t source::book -t level::b1 "Dieser Text ist wichtig"

    Examples:

        \b
        # Process a short text directly
        ankiman process-text -d "German::Vocabulary" -t source::example "Der schnelle braune Fuchs springt über den faulen Hund"

        \b
        # Process a PDF file with multiple tags 
        ankiman process-text -f article.pdf -d "German::Vocabulary" -t source::news -t level::b2

        \b
        # Process piped text from another command
        grep "wichtig" text.txt | ankiman process-text -d "German::Vocabulary" -t source::filtered
    """
    ensure_anki_or_fail(ctx)
    
    # Determine text source - priority: direct text > file > stdin
    content = None
    source = None
    
    if text:
        content = text
        source = "direct input"
    elif file:
        if file.lower().endswith('.pdf'):
            content = read_pdf(file)
            source = f"PDF file: {file}"
        elif file.lower().endswith('.txt'):
            content = read_txt(file)
            source = f"TXT file: {file}"
        else:
            print("Unsupported file format. Only PDF and TXT are supported.")
            exit(1)
    elif not sys.stdin.isatty():  # Check if data is being piped in
        content = read_stdin()
        source = "stdin"
    else:
        print("No input provided. Please provide text via argument, --file option, or pipe in content.")
        exit(1)
        
    print(f"Processing text from {source}")
    run_process_text(content, deck, tags)

@cli.command("print-dict")
@click.option('-d', '--deck', required=True, 
              help='Name of the Anki deck to extract words from')
@click.pass_context
def print_dict_cmd(ctx, deck):
    """Print all base German words from an Anki deck.

    This command extracts and prints the base form (base_d field) of all words
    from the specified Anki deck. Useful for creating word lists or checking
    deck contents.

    Example usage:
    ankiman print-dict -d "German::Vocabulary" > wordlist.txt
    """
    ensure_anki_or_fail(ctx)
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
@click.pass_context
def tag_freq_cmd(ctx, deck, prefix, word, word_list):
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
    ensure_anki_or_fail(ctx)
    run_tag_freq(deck, prefix, word, word_list)

if __name__ == "__main__":
    cli()
