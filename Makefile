.DEFAULT_GOAL := test
NODE_BIN=./node_modules/.bin

.PHONY: clean compile_translations dummy_translations extract_translations fake_translations help html_coverage \
	migrate pull_translations push_translations quality requirements test update_translations validate

help:
	@echo "Please use \`make <target>\` where <target> is one of"
	@echo "  clean                      delete generated byte code and coverage reports"
	@echo "  compile_translations       compile translation files, outputting .po files for each supported language"
	@echo "  dummy_translations         generate dummy translation (.po) files"
	@echo "  extract_translations       extract strings to be translated, outputting .mo files"
	@echo "  fake_translations          generate and compile dummy translation files"
	@echo "  help                       display this help message"
	@echo "  html_coverage              generate and view HTML coverage report"
	@echo "  migrate                    apply database migrations"
	@echo "  pull_translations          pull translations from Transifex"
	@echo "  push_translations          push source translation files (.po) from Transifex"
	@echo "  quality                    run PEP8 and Pylint"
	@echo "  accept                     run acceptance tests"
	@echo "  requirements               install requirements for local development"
	@echo "  serve                      serve Programs at 0.0.0.0:8004"
	@echo "  test                       run tests and generate coverage report"
	@echo "  validate                   run tests and quality checks"
	@echo "  html_docs                  build html documents from rst docs and open in (default) browser"
	@echo ""

clean:
	find . -name '*.pyc' -delete
	coverage erase

requirements:
	pip install -r requirements/local.txt

test: clean
	REUSE_DB=1 coverage run ./manage.py test programs --settings=programs.settings.test
	coverage report

quality:
	pep8 --config=.pep8 programs *.py acceptance_tests
	pylint --rcfile=pylintrc programs *.py acceptance_tests

serve:
	python manage.py runserver 0.0.0.0:8004

accept:
	nosetests --with-ignore-docstrings -v acceptance_tests --with-xunit --xunit-file=acceptance_tests/xunit.xml

validate: test quality

migrate:
	python manage.py migrate

html_coverage:
	coverage html && open htmlcov/index.html

extract_translations:
	python manage.py makemessages -l en -v1 -d django
	python manage.py makemessages -l en -v1 -d djangojs

dummy_translations:
	cd programs && i18n_tool dummy

compile_translations:
	python manage.py compilemessages

fake_translations: extract_translations dummy_translations compile_translations

pull_translations:
	tx pull -a

push_translations:
	tx push -s

html_docs:
	cd docs && make html && open _build/html/index.html
