# ROS installs pytest plugins system-wide (/opt/ros/.../launch_testing) that get
# auto-loaded and fail on an unrelated missing dependency. This project has
# nothing to do with ROS, so plugin autoloading stays off.
# Override with e.g. `make paper PYTHON=/path/to/venv/bin/python`.
PYTHON ?= python
PYTEST := PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PYTHON) -m pytest

.PHONY: test test-fast lint fmt eval paper paper-anon

test:
	$(PYTEST) tests/ -q

test-fast:
	$(PYTEST) tests/ -q -m "not slow"

lint:
	ruff check src tests scripts

fmt:
	ruff format src tests scripts

eval:
	$(PYTHON) scripts/sim/evaluate.py --episodes 40

# Rebuild every table, figure and number in the manuscript from results/ and check them.
paper:
	$(PYTHON) scripts/paper/build_paper_evidence.py
	$(PYTHON) scripts/paper/supplementary_analysis.py
	latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
	$(PYTHON) scripts/paper/check_paper_numbers.py

# Double-blind submission copy: same source, CoRL submission mode (anonymous
# author block, line numbers, no PDF author metadata), written to paper/main_anon.pdf.
paper-anon: paper
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error -jobname=main_anon \
	  -pdflatex='pdflatex %O "\\def\\ANON{1}\\input{%S}"' main.tex
	@$(PYTHON) scripts/paper/check_anonymized.py paper/main_anon.pdf
