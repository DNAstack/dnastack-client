PY_VERSION_BASELINE=3.11
PY_VERSION_STABLE=3.11
PY_VERSION_LATEST=3.12
TESTING_IMAGE_NAME=dnastack/client-library-testing

# Check if uv is available
UV_AVAILABLE := $(shell command -v uv 2> /dev/null)

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "DNAstack Client Library - Available Make Targets"
	@echo ""
	@echo "Development Setup:"
	@echo "  setup                    Set up development environment with uv"
	@echo "  reset                    Clean configuration and session files"
	@echo ""
	@echo "Testing:"
	@echo "  test-unit                Run unit tests"
	@echo "  test-unit-cov            Run unit tests with coverage report"
	@echo "  test-unit-watch          Run unit tests in watch mode"
	@echo "  test-e2e                 Run E2E tests"
	@echo "  test-all                 Run both unit and E2E tests"
	@echo ""
	@echo "Linting:"
	@echo "  lint                     Run ruff linter to check code"
	@echo "  lint-fix                 Auto-fix linting issues"
	@echo ""
	@echo "Package Management:"
	@echo "  package-test             Build and test package installation"
	@echo "  publish                  Build package for distribution"
	@echo ""
	@echo "Docker Testing:"
	@echo "  docker-test-all          Run tests across all Python versions"
	@echo "  docker-test-all-baseline Test with Python $(PY_VERSION_BASELINE) (baseline)"
	@echo "  docker-test-all-stable   Test with Python $(PY_VERSION_STABLE) (stable)"
	@echo "  docker-test-all-latest   Test with Python $(PY_VERSION_LATEST) (latest)"
	@echo "  docker-test-all-anaconda Test with Anaconda"
	@echo "  docker-test-all-pypy     Test with PyPy"
	@echo ""
	@echo "Notebooks:"
	@echo "  run-notebooks            Start Jupyter notebook server"
	@echo "  run-notebooks-dev        Start Jupyter with development mounts"
	@echo ""

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

.PHONY: install-buildx
install-buildx:
	@echo "Checking for Docker buildx..."
	@if ! docker buildx version &> /dev/null; then \
		echo "Installing Docker buildx for $(shell uname -s)/$(shell uname -m)..."; \
		mkdir -p ~/.docker/cli-plugins; \
		if [ "$(shell uname -s)" = "Darwin" ] && [ "$(shell uname -m)" = "arm64" ]; then \
			curl -LsSf https://github.com/docker/buildx/releases/download/v0.12.1/buildx-v0.12.1.darwin-arm64 -o ~/.docker/cli-plugins/docker-buildx; \
		elif [ "$(shell uname -s)" = "Darwin" ] && [ "$(shell uname -m)" = "x86_64" ]; then \
			curl -LsSf https://github.com/docker/buildx/releases/download/v0.12.1/buildx-v0.12.1.darwin-amd64 -o ~/.docker/cli-plugins/docker-buildx; \
		elif [ "$(shell uname -s)" = "Linux" ] && [ "$(shell uname -m)" = "x86_64" ]; then \
			curl -LsSf https://github.com/docker/buildx/releases/download/v0.12.1/buildx-v0.12.1.linux-amd64 -o ~/.docker/cli-plugins/docker-buildx; \
		elif [ "$(shell uname -s)" = "Linux" ] && [ "$(shell uname -m)" = "aarch64" ]; then \
			curl -LsSf https://github.com/docker/buildx/releases/download/v0.12.1/buildx-v0.12.1.linux-arm64 -o ~/.docker/cli-plugins/docker-buildx; \
		else \
			echo "Unsupported platform: $(shell uname -s)/$(shell uname -m)"; \
			exit 1; \
		fi; \
		chmod +x ~/.docker/cli-plugins/docker-buildx; \
		echo "Docker buildx installed successfully."; \
	else \
		echo "Docker buildx is already installed."; \
	fi
	@docker buildx version

.PHONY: setup
setup: check-uv
	uv venv
	uv sync --group dev
	uv run pre-commit install
	make install-buildx

.PHONY: reset
reset:
	rm -rf ~/.dnastack/config.yaml
	rm -rf ~/.dnastack/sessions/* 2> /dev/null || true

.PHONY: test-setup
test-setup: check-uv
	uv pip install --group test

.PHONY: test-unit
test-unit:
	uv run pytest tests -m unit -v -n auto

.PHONY: test-unit-cov
test-unit-cov:
	uv run pytest tests -m unit -v --cov=dnastack --cov-report=html --cov-report=term-missing -n auto

.PHONY: test-unit-watch
test-unit-watch:
	uv run pytest-watch tests -m unit -v

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
docker-test-all: docker-test-all-baseline docker-test-all-stable docker-test-all-latest docker-test-all-anaconda docker-test-all-pypy

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
	@if ! docker buildx version &> /dev/null; then \
		echo "Error: Docker buildx is required for building test images."; \
		echo "Please run 'make install-buildx' to install it."; \
		exit 1; \
	fi
	./scripts/build-e2e-test-image.sh $(TESTING_PYTHON)
	./scripts/run-e2e-tests-locally-in-docker.sh $(TESTING_PYTHON)
