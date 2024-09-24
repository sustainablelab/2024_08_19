.PHONY: tags
tags:
	ctags -R .

.PHONY: tests
tests:
	python -m unittest discover -s libs
