venv:
	python3 -m venv .venv
	@echo 'run `source .venv/bin/activate` to use virtualenv'

setup:
	python3 -m pip install -Ur requirements.txt
	python3 -m pip install -Ur requirements-dev.txt

dev: venv
	source .venv/bin/activate && make setup
	source .venv/bin/activate && python3 setup.py develop
	@echo 'run `source .venv/bin/activate` to develop click_best_practices'

release:
	python3 setup.py bdist_wheel
	python3 -m twine upload dist/*

test:
	pytest

clean:
	rm -rf build dist README MANIFEST *.egg-info

distclean: clean
	rm -rf .venv