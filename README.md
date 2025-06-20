# dnastack-client
The command line interface and client library for DNAstack services and GA4GH-compatible service, implemented in Python

* This is a fork from [the old repository](https://github.com/DNAstack/dnastack-client-library).
* Copyright 2024 DNAstack Corp.
* All usages are permitted under [Apache 2 License](LICENSE).

## Development Setup

### Prerequisites

This project uses [uv](https://docs.astral.sh/uv/) for Python project and dependency management. uv is an extremely fast Python package installer and resolver, written in Rust.

#### Installing uv

Choose one of the following installation methods:

1. **Using the installer script (recommended):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Using pip:**
   ```bash
   pip install uv
   ```

3. **Using Homebrew (macOS):**
   ```bash
   brew install uv
   ```

4. **Using pipx:**
   ```bash
   pipx install uv
   ```

For more installation options and detailed instructions, visit the [official uv documentation](https://docs.astral.sh/uv/getting-started/installation/).

### Setting Up the Development Environment

Once uv is installed, you can set up the development environment:

```bash
# Set up virtual environment and install all dependencies
make setup

# Or manually:
uv venv
uv pip install -e ".[all]"
uv pip install --group dev
```

### Tips
To run the client in development mode from the current sources:

1. Direct Python execution:
```
   python -m dnastack --help
   python -m dnastack auth login
   python -m dnastack collections list
```
2. Using the omics entry point:
```
   python -m dnastack.omics_cli --help
```
3. IntelliJ/PyCharm run configuration:
   - Run the "Omics CLI" configuration in IntelliJ/PyCharm.
   - This configuration runs the CLI using `python -m dnastack` to avoid module shadowing issues

### FAQ

**Q: Why do I get a `ModuleNotFoundError: No module named 'http.client'` error when I run the `omics_cli.__main__` function 
through IntelliJ/PyCharm?**

**A:**  The default run configuration in IntelliJ/PyCharm tries to run the CLI script as a standalone file. 
This causes Python to add `dnastack/` to `sys.path`. Since there is an `http/` directory inside `dnastack/`, it shadows 
Python's built-in `http` module. As a result, imports like `import http.client` will fail with a `ModuleNotFoundError`.  

To avoid this, use the `python -m dnastack` command or the provided "Omics CLI" run configuration in IntelliJ/PyCharm.