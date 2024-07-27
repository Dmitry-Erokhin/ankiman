install:
	poetry build
	pip install .
	python -m spacy download de_core_news_lg