PY_VERSION_BASELINE=3.11
PY_VERSION_STABLE=3.11
PY_VERSION_LATEST=3.12
TESTING_IMAGE_NAME=dnastack/client-library-testing

# Check if uv is available
UV_AVAILABLE := $(shell command -v uv 2> /dev/null)

.PHONY: check-uv
check-uv:
ifndef UV_AVAILABLE
	@echo "Error: 'uv' is not installed. Please install it first:"
	@echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
	@echo "  or"
	@echo "  pip install uv"
	@echo "For more installation options, visit: https://docs.astral.sh/uv/getting-started/installation/"
	@exit 1
endif

.PHONY: run-notebooks
run-notebooks:
	docker run -it --rm \
		-v $$(pwd)/samples:/workspace \
		--workdir /workspace \
		-p 8888:8888 \
		jupyter/scipy-notebook

.PHONY: run-notebooks-dev
run-notebooks-dev:
	docker run -it --rm \
		-v $$(pwd)/samples:/workspace \
		-v $$(pwd)/:/opt/src \
		--workdir /workspace \
		-p 8888:8888 \
		jupyter/scipy-notebook

.PHONY: setup
setup:
	uv venv
	uv sync --group dev
	uv run pre-commit install
	@echo "Development environment setup complete. Activate with: source .venv/bin/activate"

.PHONY: setup-docker
setup-docker: check-uv
	uv venv
	uv sync --group dev
	@echo "Docker environment setup complete."

.PHONY: reset
reset:
	rm -rf ~/.dnastack/config.yaml
	rm -rf ~/.dnastack/sessions/* 2> /dev/null || true

.PHONY: test-setup
test-setup: check-uv
	uv pip install --group test

.PHONY: test-unit
test-unit:
	uv run pytest tests/unit -v

.PHONY: test-unit-cov
test-unit-cov:
	uv run pytest tests/unit -v --cov=dnastack --cov-report=html --cov-report=term-missing

.PHONY: test-unit-watch
test-unit-watch:
	uv run pytest-watch tests/unit -v

.PHONY: lint
lint:
	uv run ruff check .

.PHONY: lint-fix
lint-fix:
	uv run ruff check --fix .

.PHONY: test-e2e
test-e2e:
	E2E_ENV_FILE=.env ./scripts/run-e2e-tests.sh

.PHONY: test-all
test-all: test-unit test-e2e

.PHONY: package-test
package-test: check-uv
	mkdir -p dist; rm -f dist/*
	uv build
	docker run -it --rm \
		-v $$(pwd)/dist:/dist-test \
		--workdir /dist-test \
		python:$(PY_VERSION_BASELINE)-slim \
		bash -c "pip install uv && uv pip install --system *.whl && dnastack use --no-auth viral.ai"

.PHONY: publish
publish: check-uv
	uv build
	@echo "Package built successfully. To publish to PyPI, run:"
	@echo "  uv publish"
	@echo "Or for test PyPI:"
	@echo "  uv publish --index-url https://test.pypi.org/legacy/"

.PHONY: docker-test-all
docker-test-all: docker-test-all-python-oldest-stable docker-test-all-python-latest-stable docker-test-all-python-rc

# Testing the oldest stable version.
.PHONY: docker-test-all-baseline
docker-test-all-baseline:
	make TESTING_PYTHON=python:$(PY_VERSION_BASELINE)-slim WEBDRIVER_DISABLED=false docker-test-all-solo

# Testing the latest stable version.
.PHONY: docker-test-all-stable
docker-test-all-stable:
	make TESTING_PYTHON=python:$(PY_VERSION_STABLE)-slim WEBDRIVER_DISABLED=false docker-test-all-solo

# Testing the release candidate version.
.PHONY: docker-test-all-latest
docker-test-all-latest:
	make TESTING_PYTHON=python:$(PY_VERSION_LATEST)-slim WEBDRIVER_DISABLED=false docker-test-all-solo

# Testing the anaconda release.
.PHONY: docker-test-all-anaconda
docker-test-all-anaconda:
	make TESTING_PYTHON=continuumio/miniconda3 WEBDRIVER_DISABLED=false docker-test-all-solo

.PHONY: docker-test-all-pypy
docker-test-all-pypy:
	make TESTING_PYTHON=pypy WEBDRIVER_DISABLED=false docker-test-all-solo

.PHONY: docker-test-all-solo
docker-test-all-solo:
	./scripts/build-e2e-test-image.sh $(TESTING_PYTHON)
	./scripts/run-e2e-tests-locally-in-docker.sh $(TESTING_PYTHON)
