# Publisher Questions CLI Design

**Date:** 2026-03-13
**ClickUp Ticket:** [CU-86b8vuywp](https://app.clickup.com/t/86b8vuywp)
**Status:** Approved

## Overview

Add `dnastack publisher questions` subcommands to enable users to list, describe, and execute questions directly on a publisher via the CLI. This feature mirrors the existing `dnastack explorer questions` commands but operates on individual collections within a publisher rather than federated questions across multiple collections.

## Background

Currently, the CLI supports executing federated questions through the explorer:

```bash
dnastack explorer questions ask \
    --question-name variant_lookup \
    --param chromosome=chr1 \
    --param position=12345 \
    --param reference=A
```

This ticket adds the ability to call questions directly on a publisher's collection service, where questions are scoped to individual collections.

## Requirements

### Functional Requirements

1. Add three new commands under `dnastack publisher questions`:
   - `list` - List all questions for a collection
   - `describe` - Get detailed information about a specific question
   - `ask` - Execute a question with parameters

2. All commands require a `--collection` flag to specify which collection to query

3. The `ask` command should support:
   - `--question-name` (required) - Question ID to execute
   - `--collection` (required) - Collection to query
   - `--param` (optional, multiple) - Question parameters as key=value
   - `--output-file` (optional) - Save results to file
   - `--output` (optional) - Output format (json/csv/yaml/table)

4. Mimic the explorer questions command structure where applicable

### Non-Functional Requirements

- Reuse existing patterns from explorer questions implementation
- Follow DNAstack CLI conventions and coding standards
- Maintain consistency with other publisher commands
- Support authentication via existing Wallet integration
- Handle errors gracefully with helpful messages

## Architecture

### High-Level Structure

```
CLI Layer:
  dnastack/cli/commands/publisher/questions/
    ├── __init__.py          (questions command group)
    ├── commands.py          (list, describe, ask commands)
    └── utils.py             (parameter parsing, output helpers)

Client Layer:
  dnastack/client/collections/client.py
    └── CollectionServiceClient (add 3 new methods)

Data Models:
  dnastack/client/collections/model.py
    └── Question, QuestionParameter models
```

### Key Design Decisions

**Why extend CollectionServiceClient instead of creating a new client?**
- Questions are inherently tied to collections (per-collection scope)
- CollectionServiceClient already manages collection resources
- Avoids unnecessary abstraction for relatively simple CRUD operations
- Keeps related functionality together

**Why create a dedicated command group?**
- Clear separation of concerns at the CLI level
- Mirrors the explorer questions structure (familiar to users)
- Allows reuse of utilities from explorer where applicable

### Differences from Explorer Questions

| Aspect | Explorer | Publisher |
|--------|----------|-----------|
| Scope | Federated across multiple collections | Single collection |
| Collection Filter | `--collections` to select which to query | `--collection` (required) to specify target |
| Local Federation | `--local-federated` flag | Not applicable |
| Client | Dedicated `ExplorerClient` | `CollectionServiceClient` |
| Questions API | `/questions/{id}/query` | `/collections/{collection}/questions/{id}/query` |

## Client Layer Design

### New Methods in CollectionServiceClient

Add three methods to `dnastack/client/collections/client.py`:

```python
def list_questions(
    self,
    collection_id_or_slug_name: str,
    no_auth: bool = False,
    trace: Optional[Span] = None
) -> List[Question]:
    """
    List all questions for a collection.

    Args:
        collection_id_or_slug_name: Collection ID or slug name
        no_auth: Skip authentication (for public collections)
        trace: Optional tracing span

    Returns:
        List[Question]: List of questions available for the collection

    Raises:
        UnknownCollectionError: If collection not found
        ClientError: For other API errors
    """
    trace = trace or Span(origin=self)
    with self.create_http_session(no_auth=no_auth) as session:
        url = urljoin(self.url, f'collections/{collection_id_or_slug_name}/questions')
        response = session.get(url, trace_context=trace)

        # API returns MultipleItemsResponse with items array
        response_data = response.json()
        return [Question(**item) for item in response_data.get('items', [])]


def get_question(
    self,
    collection_id_or_slug_name: str,
    question_id: str,
    no_auth: bool = False,
    trace: Optional[Span] = None
) -> Question:
    """
    Get details of a specific question.

    Args:
        collection_id_or_slug_name: Collection ID or slug name
        question_id: Question ID
        no_auth: Skip authentication (for public collections)
        trace: Optional tracing span

    Returns:
        Question: Question details including parameters

    Raises:
        UnknownCollectionError: If collection not found
        ClientError: If question not found (404) or other API errors
    """
    trace = trace or Span(origin=self)
    with self.create_http_session(no_auth=no_auth) as session:
        url = urljoin(self.url, f'collections/{collection_id_or_slug_name}/questions/{question_id}')
        response = session.get(url, trace_context=trace)
        return Question(**response.json())


def ask_question(
    self,
    collection_id_or_slug_name: str,
    question_id: str,
    params: Dict[str, str],
    no_auth: bool = False,
    trace: Optional[Span] = None
) -> ResultIterator[Dict[str, Any]]:
    """
    Execute a question with parameters.

    Args:
        collection_id_or_slug_name: Collection ID or slug name
        question_id: Question ID to execute
        params: Question parameters as key-value pairs
        no_auth: Skip authentication (for public collections)
        trace: Optional tracing span

    Returns:
        ResultIterator[Dict[str, Any]]: Iterator over query results in Data Connect format

    Raises:
        UnknownCollectionError: If collection not found
        ClientError: If question not found or invalid parameters
    """
    trace = trace or Span(origin=self)
    return ResultIterator(
        QuestionQueryResultLoader(
            service_url=urljoin(self.url, f'collections/{collection_id_or_slug_name}/questions/{question_id}/query'),
            http_session=self.create_http_session(no_auth=no_auth),
            request_payload={'params': params},
            trace=trace
        )
    )
```

### Result Loader for Question Queries

Create `QuestionQueryResultLoader` (similar to explorer's pattern) to handle Data Connect pagination:

```python
class QuestionQueryResultLoader(ResultLoader):
    """
    Result loader for publisher question query results.
    Handles Data Connect TableData format with pagination support.
    """

    def __init__(
        self,
        service_url: str,
        http_session: HttpSession,
        request_payload: Dict[str, Any],
        trace: Optional[Span] = None
    ):
        self.__http_session = http_session
        self.__service_url = service_url
        self.__request_payload = request_payload
        self.__trace = trace
        self.__next_page_url = None
        self.__first_request = True

    def has_more(self) -> bool:
        return self.__first_request or self.__next_page_url is not None

    def load(self) -> List[Dict[str, Any]]:
        if not self.has_more():
            raise InactiveLoaderError(self.__service_url)

        with self.__http_session as session:
            if self.__first_request:
                # Initial POST request with parameters
                response = session.post(
                    self.__service_url,
                    json=self.__request_payload,
                    trace_context=self.__trace
                )
                self.__first_request = False
            else:
                # Follow pagination with GET
                response = session.get(
                    self.__next_page_url,
                    trace_context=self.__trace
                )

            response_data = response.json()

            # Extract next page URL from pagination
            pagination = response_data.get('pagination')
            self.__next_page_url = pagination.get('next_page_url') if pagination else None

            # Return data array from TableData format
            return response_data.get('data', [])
```

### Data Models

Add to `dnastack/client/collections/model.py`:

```python
class QuestionParameter(BaseModel):
    """
    Represents a parameter for a publisher question.
    """
    name: str
    input_type: str  # e.g., "STRING", "INTEGER", "FLOAT"
    required: bool
    description: Optional[str] = None
    default_value: Optional[str] = None
    test_value: Optional[str] = None


class Question(BaseModel):
    """
    Represents a publisher question within a collection.
    """
    id: str
    name: str
    description: Optional[str] = None
    collection_id: str
    parameters: List[QuestionParameter] = []
    # Note: SQL template may not be exposed by API
```

## CLI Command Design

### Command Group Structure

Create `dnastack/cli/commands/publisher/questions/__init__.py`:

```python
from dnastack.cli.commands.publisher.questions.commands import init_questions_commands
from dnastack.cli.core.group import formatted_group


@formatted_group("questions")
def questions_command_group():
    """Commands for working with publisher questions"""
    pass


# Initialize questions subcommands
init_questions_commands(questions_command_group)
```

Register in `dnastack/cli/commands/publisher/__init__.py`:

```python
from dnastack.cli.commands.publisher.questions import questions_command_group

# ... existing imports ...

publisher_command_group.add_command(collections_command_group)
publisher_command_group.add_command(datasources_command_group)
publisher_command_group.add_command(questions_command_group)  # NEW
```

### Command Implementations

Create `dnastack/cli/commands/publisher/questions/commands.py`:

#### List Command

```python
@formatted_command(
    group=group,
    name='list',
    specs=[
        ArgumentSpec(
            name='collection',
            arg_names=['--collection', '-c'],
            help='Collection ID or slug name',
            required=True
        ),
        RESOURCE_OUTPUT_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def list_questions(collection: str, output: str, context: Optional[str], endpoint_id: Optional[str]):
    """List all questions for a collection"""
    trace = Span()
    client = get_collection_service_client(context=context, endpoint_id=endpoint_id)

    questions = client.list_questions(collection, trace=trace)

    show_iterator(
        output_format=output,
        iterator=questions,
        transform=lambda q: q.model_dump()
    )
```

#### Describe Command

```python
@formatted_command(
    group=group,
    name='describe',
    specs=[
        ArgumentSpec(
            name='question_id',
            arg_type=ArgumentType.POSITIONAL,
            help='Question ID to describe',
            required=True
        ),
        ArgumentSpec(
            name='collection',
            arg_names=['--collection', '-c'],
            help='Collection ID or slug name',
            required=True
        ),
        RESOURCE_OUTPUT_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def describe_question(
    question_id: str,
    collection: str,
    output: str,
    context: Optional[str],
    endpoint_id: Optional[str]
):
    """Get detailed information about a question"""
    trace = Span()
    client = get_collection_service_client(context=context, endpoint_id=endpoint_id)

    question = client.get_question(collection, question_id, trace=trace)

    show_iterator(
        output_format=output,
        iterator=[question],
        transform=lambda q: q.model_dump()
    )
```

#### Ask Command

```python
@formatted_command(
    group=group,
    name='ask',
    specs=[
        ArgumentSpec(
            name='question_name',
            arg_names=['--question-name'],
            help='Question ID to execute',
            required=True
        ),
        ArgumentSpec(
            name='collection',
            arg_names=['--collection', '-c'],
            help='Collection ID or slug name',
            required=True
        ),
        ArgumentSpec(
            name='args',
            arg_names=['--param'],
            help='Question parameters in key=value format (can be used multiple times)',
            type=JsonLike,
            multiple=True
        ),
        ArgumentSpec(
            name='output_file',
            arg_names=['--output-file'],
            help='Output file path for results'
        ),
        DATA_OUTPUT_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def ask_question(
    question_name: str,
    collection: str,
    args: tuple,
    output_file: Optional[str],
    output: str,
    context: Optional[str],
    endpoint_id: Optional[str]
):
    """Execute a question with parameters"""
    trace = Span()
    client = get_collection_service_client(context=context, endpoint_id=endpoint_id)

    # Parse parameters
    inputs = {}
    if args:
        for arg in args:
            parsed_args = arg.parsed_value() if hasattr(arg, 'parsed_value') else parse_and_merge_arguments(arg)
            inputs.update(parsed_args)

    # Get question details for validation
    question = client.get_question(collection, question_name, trace=trace)

    # Validate parameters
    try:
        inputs = validate_question_parameters(inputs, question)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    # Execute the question
    results_iter = client.ask_question(collection, question_name, inputs, trace=trace)

    # Collect results
    results = list(results_iter)

    # Output results
    handle_question_results_output(results, output_file, output)
```

### Utility Functions

Create `dnastack/cli/commands/publisher/questions/utils.py`:

```python
from typing import Optional, Dict, Any, List
from imagination import container
from dnastack.client.collections.client import CollectionServiceClient
from dnastack.cli.helpers.client_factory import ConfigurationBasedClientFactory
from dnastack.common.json_argument_parser import parse_and_merge_arguments


def get_collection_service_client(
    context: Optional[str] = None,
    endpoint_id: Optional[str] = None
) -> CollectionServiceClient:
    """
    Get a CollectionServiceClient instance.

    Args:
        context: Optional context name
        endpoint_id: Optional endpoint ID

    Returns:
        CollectionServiceClient: Configured client
    """
    factory: ConfigurationBasedClientFactory = container.get(ConfigurationBasedClientFactory)
    return factory.get(CollectionServiceClient, context_name=context, endpoint_id=endpoint_id)


def validate_question_parameters(inputs: Dict[str, str], question) -> Dict[str, str]:
    """
    Validate question parameters against question schema.

    Args:
        inputs: User-provided parameters
        question: Question object with parameter definitions

    Returns:
        Dict[str, str]: Validated parameters

    Raises:
        ValueError: If required parameters are missing
    """
    required_params = [p.name for p in question.parameters if p.required]
    missing_params = [p for p in required_params if p not in inputs]

    if missing_params:
        raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

    return inputs


def handle_question_results_output(
    results: List[Dict[str, Any]],
    output_file: Optional[str],
    output_format: str
):
    """
    Handle output of question results to file or stdout.
    Reuses logic from explorer questions utils.

    Args:
        results: List of result dictionaries
        output_file: Optional file path to write to
        output_format: Output format (json, csv, yaml, table)
    """
    # Import from explorer utils to reuse existing implementation
    from dnastack.cli.commands.explorer.questions.utils import (
        handle_question_results_output as explorer_output_handler
    )

    explorer_output_handler(results, output_file, output_format)
```

## Error Handling

### Error Scenarios and Responses

| Scenario | HTTP Status | Exception | CLI Output |
|----------|-------------|-----------|------------|
| Collection not found | 404 | `UnknownCollectionError` | "Error: Collection 'xyz' not found" + suggestion to list collections |
| Question not found | 404 | `ClientError` | "Error: Question 'abc' not found in collection 'xyz'" + suggestion to list questions |
| Missing required params | - | `ValueError` | "Error: Missing required parameters: x, y, z" + show available params |
| Invalid parameter values | 400 | `ClientError` | "Error: Invalid parameters - {API message}" |
| Unauthorized | 401 | `UnauthenticatedApiAccessError` | "Error: Authentication required" |
| Forbidden | 403 | `UnauthorizedApiAccessError` | "Error: Not authorized to access questions in collection 'xyz'" |

### Validation Strategy

1. **Pre-flight Validation:**
   - Fetch question metadata with `get_question()`
   - Validate required parameters are provided
   - Show helpful error if validation fails

2. **API Error Handling:**
   - Catch HTTP errors from collection service
   - Map to appropriate exceptions
   - Provide actionable error messages

3. **Pagination Handling:**
   - `ResultIterator` automatically follows `next_page_url`
   - Collect all pages before outputting results
   - Handle pagination errors gracefully

## Testing Strategy

### Unit Tests

**Client Tests** (`tests/client/collections/test_questions.py`):

```python
def test_list_questions():
    """Test listing questions for a collection"""
    # Mock API response with MultipleItemsResponse format
    # Verify Question objects are created correctly
    # Test with empty list

def test_get_question():
    """Test getting a specific question"""
    # Mock API response with Question data
    # Verify Question object parsing
    # Test 404 handling

def test_ask_question():
    """Test executing a question"""
    # Mock Data Connect TableData response
    # Verify ResultIterator behavior
    # Test pagination (multiple pages)
    # Test with no results
```

**CLI Command Tests** (`tests/cli/commands/publisher/test_questions_commands.py`):

```python
def test_list_questions_command():
    """Test list command"""
    # Mock CollectionServiceClient.list_questions
    # Verify output formatting (json, yaml, table)
    # Test with --collection flag

def test_describe_question_command():
    """Test describe command"""
    # Mock CollectionServiceClient.get_question
    # Verify parameter display
    # Test output formatting

def test_ask_question_command():
    """Test ask command"""
    # Mock parameter parsing
    # Mock parameter validation
    # Mock CollectionServiceClient.ask_question
    # Test --output-file
    # Test various output formats
    # Test error scenarios (missing params, etc.)
```

**Utility Tests** (`tests/cli/commands/publisher/test_questions_utils.py`):

```python
def test_validate_question_parameters():
    """Test parameter validation"""
    # Test with all required params
    # Test with missing required params
    # Test with optional params
    # Test with extra params (should be allowed)
```

### Integration/E2E Tests

If applicable, add E2E tests that:
- Run against a real collection-service instance
- Test authentication flow
- Verify actual question execution
- Test against known test collections

### Test Coverage Goals

- Unit test coverage: >80% for new code
- All error paths tested
- Happy paths for all three commands verified
- Edge cases (empty results, pagination, etc.) covered

## Implementation Steps

### Phase 1: Data Models and Client

1. **Add Data Models** (`dnastack/client/collections/model.py`)
   - Define `QuestionParameter` class
   - Define `Question` class
   - Add imports and type hints

2. **Create Result Loader** (`dnastack/client/collections/client.py`)
   - Implement `QuestionQueryResultLoader`
   - Handle POST for initial request
   - Handle GET for pagination
   - Parse Data Connect TableData format

3. **Extend CollectionServiceClient** (`dnastack/client/collections/client.py`)
   - Add `list_questions()` method
   - Add `get_question()` method
   - Add `ask_question()` method
   - Add error handling

### Phase 2: CLI Commands

4. **Create CLI Utilities** (`dnastack/cli/commands/publisher/questions/utils.py`)
   - Implement `get_collection_service_client()`
   - Implement `validate_question_parameters()`
   - Implement `handle_question_results_output()` (reuse explorer)

5. **Implement CLI Commands** (`dnastack/cli/commands/publisher/questions/commands.py`)
   - Implement `list_questions` command
   - Implement `describe_question` command
   - Implement `ask_question` command
   - Use `@formatted_command` decorator
   - Add proper error handling

6. **Create Command Group** (`dnastack/cli/commands/publisher/questions/__init__.py`)
   - Create `questions_command_group`
   - Initialize commands

7. **Register Command Group** (`dnastack/cli/commands/publisher/__init__.py`)
   - Import questions_command_group
   - Register under publisher_command_group

### Phase 3: Testing

8. **Write Unit Tests**
   - Client method tests
   - CLI command tests
   - Utility function tests
   - Mock all external dependencies

9. **Run Tests Locally**
   - Execute `make test-unit`
   - Verify coverage meets goals
   - Fix any failing tests

### Phase 4: Git and Documentation

10. **Create Branch**
    - Branch name: `add_publisher_questions_ask-CU-86b8vuywp`
    - Base branch: current branch (as specified by user)

11. **Commit Changes**
    - Commit message: `[CU-86b8vuywp] Add publisher questions subcommands`
    - Include co-author line per CLAUDE.md

12. **Update Documentation** (if needed)
    - Update CLI README if exists
    - Add examples to docs

## File Manifest

### New Files

```
dnastack-client/
├── dnastack/cli/commands/publisher/questions/
│   ├── __init__.py                  (questions command group)
│   ├── commands.py                  (list, describe, ask commands)
│   └── utils.py                     (helper functions)
└── tests/
    ├── cli/commands/publisher/
    │   └── test_questions_commands.py
    └── client/collections/
        └── test_questions.py
```

### Modified Files

```
dnastack-client/
├── dnastack/client/collections/
│   ├── client.py                    (add 3 methods + QuestionQueryResultLoader)
│   └── model.py                     (add Question, QuestionParameter models)
└── dnastack/cli/commands/publisher/
    └── __init__.py                  (register questions group)
```

## Dependencies

No new external dependencies required. Uses existing libraries:
- `click` - CLI framework
- `pydantic` - Data models
- `requests` - HTTP client (via HttpSession)
- Existing DNAstack client infrastructure

## Security Considerations

- **Authentication:** Uses existing Wallet OAuth2 integration
- **Authorization:** Respects publisher's access control for collections and questions
- **No-Auth Mode:** Supports `--no-auth` for public resources (not exposed as CLI flag initially)
- **Input Validation:** Validates parameters before sending to API
- **Error Messages:** Don't leak sensitive information (follow existing patterns)

## Open Questions / Future Enhancements

1. **Question Creation/Editing:** Not in scope for this ticket, but could be added later
2. **Question Preferences:** Publisher has question preferences API, could add support
3. **Test Execution:** Publisher has `/questions/test` endpoint, could add `test` command
4. **Caching:** Could cache question metadata to avoid repeated API calls
5. **Auto-completion:** Could add shell completion for question names

## Examples

### List Questions

```bash
dnastack publisher questions list --collection my-variants
```

Output:
```json
[
  {
    "id": "variant_lookup",
    "name": "Variant Lookup",
    "description": "Look up variants by position",
    "collection_id": "...",
    "parameters": [
      {"name": "chromosome", "input_type": "STRING", "required": true},
      {"name": "position", "input_type": "INTEGER", "required": true}
    ]
  }
]
```

### Describe Question

```bash
dnastack publisher questions describe variant_lookup --collection my-variants
```

Output shows detailed question metadata including all parameters.

### Ask Question

```bash
dnastack publisher questions ask \
    --collection my-variants \
    --question-name variant_lookup \
    --param chromosome=chr1 \
    --param position=12345 \
    --output json
```

Output:
```json
[
  {
    "chromosome": "chr1",
    "position": 12345,
    "reference": "A",
    "alternate": "G",
    ...
  }
]
```

### Save to File

```bash
dnastack publisher questions ask \
    --collection my-variants \
    --question-name variant_lookup \
    --param chromosome=chr1 \
    --param position=12345 \
    --output-file results.json \
    --output json
```

Output: `Results written to results.json`

## Success Criteria

- [ ] `dnastack publisher questions list --collection <id>` lists questions
- [ ] `dnastack publisher questions describe <id> --collection <id>` shows question details
- [ ] `dnastack publisher questions ask` executes questions with parameters
- [ ] Parameter validation works correctly (required params enforced)
- [ ] Output formats (json, csv, yaml, table) work correctly
- [ ] Output file writing works
- [ ] Error messages are helpful and actionable
- [ ] Unit tests pass with >80% coverage
- [ ] Code follows DNAstack coding standards
- [ ] Pre-commit hooks pass (lint, tests)
- [ ] Commands work with authentication
- [ ] Commands work with different contexts/endpoints

## References

- **ClickUp Ticket:** https://app.clickup.com/t/86b8vuywp
- **Explorer Questions Implementation:** `dnastack/cli/commands/explorer/questions/`
- **Collection Service API:** QuestionController.java, QueryController.java in collection-service
- **CLAUDE.md Guidelines:** `/Users/agenovese/Documents/development/dnastack-client/CLAUDE.md`
