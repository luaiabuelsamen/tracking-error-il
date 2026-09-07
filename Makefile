# ROS installs pytest plugins system-wide (/opt/ros/.../launch_testing) that get
# auto-loaded and fail on an unrelated missing dependency. This project has
# nothing to do with ROS, so plugin autoloading stays off.
PYTEST := PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest

.PHONY: test test-fast lint fmt eval paper

test:
	$(PYTEST) tests/ -q

test-fast:
	$(PYTEST) tests/ -q -m "not slow"

lint:
	ruff check src tests scripts

fmt:
	ruff format src tests scripts

eval:
	python scripts/sim/evaluate.py --episodes 40

# Rebuild every table, figure and number in the manuscript from results/ and check them.
paper:
	python scripts/paper/build_paper_evidence.py
	python scripts/paper/supplementary_analysis.py
	latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
	python scripts/paper/check_paper_numbers.py
