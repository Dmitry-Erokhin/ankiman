install:
	poetry build
	pip install .

get-model:
	python -m spacy download de_core_news_lg