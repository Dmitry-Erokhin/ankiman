#!/usr/bin/env python
import click
import requests
from ankiman import ANKI_CONNECT_URL

def ensure_anki_accessible():
    try:
        response = requests.get(ANKI_CONNECT_URL)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# Delegate processing to commands modules
from ankiman.commands.process_file import run_process_file
from ankiman.commands.print_dict import run_print_dict
from ankiman.commands.tag_freq import run_tag_freq


@click.group()
@click.pass_context
def cli(ctx):
    """Main CLI entry point delegating commands to processing functions."""
    if not ensure_anki_accessible():
        click.echo("Anki is not accessible. Ensure Anki is running and AnkiConnect is installed.")
        ctx.abort()


@cli.command("process-file")
@click.option('-f', '--file', required=True, type=click.Path(exists=True), help='Path to PDF or TXT file')
@click.option('-d', '--deck', required=True, help='Resulting deck name')
@click.option('-t', '--tags', multiple=True, required=True, help='Tags to add')
@click.option('-b', '--batch', default=100, help='Prompt batch size')
def process_file_cmd(file, deck, tags, batch):
    run_process_file(file, deck, tags, batch)


@cli.command("print-dict")
@click.argument("deck")
def print_dict_cmd(deck):
    run_print_dict(deck)


@cli.command("tag-freq")
@click.option('-d', '--deck', required=True, help='Deck name')
@click.option('-p', '--prefix', default='freq', help='Tag prefix')
@click.option('-w', '--word', help='Process a specific word')
@click.option('--word-list', help='Process words as a comma-separated string')
def tag_freq_cmd(deck, prefix, word, word_list):
    run_tag_freq(deck, prefix, word, word_list)


if __name__ == "__main__":
    cli()
