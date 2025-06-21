# dnastack-client
The command line interface and client library for DNAstack services and GA4GH-compatible service, implemented in Python

* This is a fork from [the old repository](https://github.com/DNAstack/dnastack-client-library).
* Copyright 2024 DNAstack Corp.
* All usages are permitted under [Apache 2 License](LICENSE).

## Development Setup

### Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) for Python dependency management. Install uv using one of these methods:

```bash
# Using the official installer (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Using Homebrew (macOS)
brew install uv

# Using pipx
pipx install uv
```

For more installation options, see the [uv documentation](https://docs.astral.sh/uv/getting-started/installation/).

### Setup

1. Clone the repository and set up the development environment:
```bash
git clone omairvalence:DNAstack/dnastack-client.git
cd dnastack-client
make setup  # Creates virtual environment and installs all dependencies
```

2. Run commands using uv (no activation needed):
```bash
make test-unit      # Run unit tests
make test-e2e       # Run E2E tests (requires .env file)
make test-all       # Run both unit and E2E tests
make lint           # Run linting checks
uv run dnastack --help  # Run CLI commands
```


### Tips

Run the client in development mode using uv:
```bash
uv run dnastack --help
uv run dnastack auth login
uv run dnastack collections list
uv run dnastack explorer questions list
uv run omics --help
```

IntelliJ/PyCharm run configuration:
   - Run the "Omics CLI" configuration in IntelliJ/PyCharm.
   - This configuration runs the CLI using `python -m dnastack` to avoid module shadowing issues

### FAQ

**Q: Why do I get a `ModuleNotFoundError: No module named 'http.client'` error when I run the `omics_cli.__main__` function 
through IntelliJ/PyCharm?**

**A:**  The default run configuration in IntelliJ/PyCharm tries to run the CLI script as a standalone file. 
This causes Python to add `dnastack/` to `sys.path`. Since there is an `http/` directory inside `dnastack/`, it shadows 
Python's built-in `http` module. As a result, imports like `import http.client` will fail with a `ModuleNotFoundError`.  

To avoid this, use the `python -m dnastack` command or the provided "Omics CLI" run configuration in IntelliJ/PyCharm.