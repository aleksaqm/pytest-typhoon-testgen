# pytest-typhoon-testgen

## Automated test generation and coverage tracking from ReqIF requirements with seamless Allure integration

**pytest-typhoon-testgen** is a powerful Python library and `pytest` plugin for automated test generation, updating, and coverage analysis based on requirements specified in ReqIF files. It also integrates seamlessly with Allure reporting, enabling automated report packaging and upload to a remote server.

---

## Features

### Automated Test Generation

- Generate `pytest`-compatible test folders, files, and test functions directly from ReqIF requirement files.
- Ensures your test suite structure mirrors your requirements hierarchy.

### Test Update & Synchronization

- Update existing test files and functions to stay in sync with evolving requirements.
- Automatically adds new tests, updates existing ones, and marks obsolete tests.

### Coverage Analysis

- Compare your current test suite against the requirements in a ReqIF file.
- Identify missing, extra, or outdated tests and folders.
- Ensure full traceability and coverage.

### Allure Reporting Integration

- Automatically collects Allure test results after test execution.
- Packages them into a ZIP archive and uploads to a configurable server endpoint.
- Server URL and Allure results directory are configurable via environment variables or a `.env` file.

###  Customizable Ignore Rules

- Supports `.typhoonignore` files to exclude specific files or directories from generation, updating, or coverage checks.

---

## Installation
```sh
pip install pytest-typhoon-testgen
```
or install it from source:
```
git clone https://github.com/aleksaqm/pytest-typhoon-testgen.git
cd pytest-typhoon-testgen
pip install .
```
---

## Usage

### 1. Test Generation

Generate a test suite from a ReqIF file.
```
  typhoon_testgen path/to/requirements.reqif path/to/output/tests
```
- Creates folders and test files mirroring the requirement structure.
- Each requirement in the ReqIF file becomes the folder where tests will be.
- Each test in the ReqIF file becomes a python test file where functions will be written.
- Each test case in the ReqIF file becomes a pytest function with metadata.

### 2. Test Update

Update an existing test suite to match the latest requirements.
```
typhoon_test_update path/to/requirements.reqif path/to/existing/tests
```
- Adds new tests and folders as needed.
- Updates existing test functions and marks unimplemented tests with `@pytest.mark.skip`.
- Preserves custom test code where possible.

### 3. Coverage Check

Analyze differences between your test suite and requirements.
```
coverage_check path/to/requirements.reqif path/to/tests
```
- Outputs a JSON summary of missing, extra, and modified tests and folders.
- Helps maintain full requirements coverage.

### 4. Allure Report Upload

Enable the reporting plugin when running pytest.
```
pytest --report
```
- After test execution, Allure results are updated to have data from test function decorators.
```
pytest --upload
```
- After test execution desired folder will be zipped and uploaded to the configured server.
```
pytest --report --upload
```
- Combination -> For doing everything at once
- Server URL and Allure results directory are configurable via environment variables or ``.env`` file.

---

## Configuration

Configure the plugin using a `.env` file in your project root.
```
ALLURE_RESULTS_DIR=allure-results
SERVER_URL=http://your-server.com
```
- Or override configuration using environment variables.

---

## Integration with Pytest

- The plugin registers itself automatically via the `pytest11` entry point.
- To enable Allure report upload, use the `--report` flag with pytest.

---

## Example Workflow

- Generate tests from your requirements.
- Run your tests with Allure and reporting enabled.
- Check coverage.
- Update tests as requirements evolve.

---

## Requirements

- Python 3.6+
- pytest
- Jinja2
- allure-pytest
- requests
- pydantic
- pydantic-settings
- gitignore-parser

See `requirements.txt` for full details.

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

---

## Contributing

Contributions are welcome!  
Please open issues or submit pull requests on GitHub.

---

## Author

**Aleksa Perović**  
aleksa.perovic@typhoon-hil.com
