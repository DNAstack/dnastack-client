# Publisher Questions CLI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `dnastack publisher questions` CLI commands to list, describe, and execute questions on publisher collections

**Architecture:** Extend CollectionServiceClient with three question methods, create new CLI command group under publisher that mirrors explorer questions structure, reuse explorer utilities for parameter validation and output formatting

**Tech Stack:** Python 3.11+, Click (CLI), Pydantic (models), pytest (testing), existing DNAstack client infrastructure

**Spec Document:** `docs/superpowers/specs/2026-03-13-publisher-questions-ask-design.md`

---

## Prerequisites: Setup Feature Branch

### Task 0: Create Feature Branch

**Files:**
- None (git operations)

- [ ] **Step 1: Check current branch**

Run: `git branch --show-current`

Expected: Shows current branch name (add-local-federated-flag-to-explorer-questions-CU-86b7p1xgv)

- [ ] **Step 2: Create feature branch from current branch**

Run: `git checkout -b add_publisher_questions_ask-CU-86b8vuywp`

Expected: Creates and switches to new branch

- [ ] **Step 3: Verify new branch**

Run: `git branch --show-current`

Expected: Shows "add_publisher_questions_ask-CU-86b8vuywp"

---

## Chunk 1: Data Models and Result Loader

### Task 1: Add Question Data Models

**Files:**
- Modify: `dnastack/client/collections/model.py` (add to end of file)
- Test: `tests/client/collections/test_question_models.py` (new file)

- [ ] **Step 1: Write failing test for QuestionParameter model**

Create `tests/client/collections/test_question_models.py`:

```python
from dnastack.client.collections.model import QuestionParameter, Question


def test_question_parameter_required_fields():
    """Test QuestionParameter with only required fields"""
    param = QuestionParameter(
        name="chromosome",
        input_type="STRING",
        required=True
    )

    assert param.name == "chromosome"
    assert param.input_type == "STRING"
    assert param.required is True
    assert param.description is None
    assert param.default_value is None
    assert param.test_value is None


def test_question_parameter_all_fields():
    """Test QuestionParameter with all fields"""
    param = QuestionParameter(
        name="position",
        input_type="INTEGER",
        required=False,
        description="Genomic position",
        default_value="1000",
        test_value="12345"
    )

    assert param.name == "position"
    assert param.input_type == "INTEGER"
    assert param.required is False
    assert param.description == "Genomic position"
    assert param.default_value == "1000"
    assert param.test_value == "12345"


def test_question_parameter_model_dump():
    """Test QuestionParameter serialization"""
    param = QuestionParameter(
        name="ref",
        input_type="STRING",
        required=True,
        description="Reference allele"
    )

    dumped = param.model_dump()

    assert dumped["name"] == "ref"
    assert dumped["input_type"] == "STRING"
    assert dumped["required"] is True
    assert dumped["description"] == "Reference allele"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/client/collections/test_question_models.py::test_question_parameter_required_fields -v`

Expected: FAIL with "ImportError: cannot import name 'QuestionParameter'"

- [ ] **Step 3: Implement QuestionParameter model**

Add to `dnastack/client/collections/model.py`:

```python
from typing import Optional, List
from pydantic import BaseModel


class QuestionParameter(BaseModel):
    """
    Represents a parameter for a publisher question.
    """
    name: str
    input_type: str
    required: bool
    description: Optional[str] = None
    default_value: Optional[str] = None
    test_value: Optional[str] = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/client/collections/test_question_models.py::test_question_parameter_required_fields -v`

Expected: PASS

- [ ] **Step 5: Run all QuestionParameter tests**

Run: `pytest tests/client/collections/test_question_models.py -k "test_question_parameter" -v`

Expected: All 3 tests PASS

- [ ] **Step 6: Commit QuestionParameter**

```bash
git add dnastack/client/collections/model.py tests/client/collections/test_question_models.py
git commit -m "[CU-86b8vuywp] Add QuestionParameter model

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Write failing test for Question model**

Add to `tests/client/collections/test_question_models.py`:

```python
def test_question_minimal():
    """Test Question with minimal required fields"""
    question = Question(
        id="variant_lookup",
        name="Variant Lookup",
        collection_id="coll123"
    )

    assert question.id == "variant_lookup"
    assert question.name == "Variant Lookup"
    assert question.collection_id == "coll123"
    assert question.description is None
    assert question.parameters == []


def test_question_with_parameters():
    """Test Question with parameters"""
    param1 = QuestionParameter(name="chr", input_type="STRING", required=True)
    param2 = QuestionParameter(name="pos", input_type="INTEGER", required=True)

    question = Question(
        id="q1",
        name="Test Question",
        description="A test question",
        collection_id="coll1",
        parameters=[param1, param2]
    )

    assert question.id == "q1"
    assert question.name == "Test Question"
    assert question.description == "A test question"
    assert question.collection_id == "coll1"
    assert len(question.parameters) == 2
    assert question.parameters[0].name == "chr"
    assert question.parameters[1].name == "pos"


def test_question_model_dump():
    """Test Question serialization"""
    param = QuestionParameter(name="x", input_type="STRING", required=True)
    question = Question(
        id="q2",
        name="Q2",
        collection_id="coll2",
        parameters=[param]
    )

    dumped = question.model_dump()

    assert dumped["id"] == "q2"
    assert dumped["name"] == "Q2"
    assert dumped["collection_id"] == "coll2"
    assert len(dumped["parameters"]) == 1
    assert dumped["parameters"][0]["name"] == "x"
```

- [ ] **Step 8: Run test to verify it fails**

Run: `pytest tests/client/collections/test_question_models.py::test_question_minimal -v`

Expected: FAIL with "ImportError: cannot import name 'Question'"

- [ ] **Step 9: Implement Question model**

Add to `dnastack/client/collections/model.py`:

```python
class Question(BaseModel):
    """
    Represents a publisher question within a collection.
    """
    id: str
    name: str
    description: Optional[str] = None
    collection_id: str
    parameters: List[QuestionParameter] = []
```

- [ ] **Step 10: Run tests to verify they pass**

Run: `pytest tests/client/collections/test_question_models.py -k "test_question" -v`

Expected: All 3 Question tests PASS

- [ ] **Step 11: Run all model tests**

Run: `pytest tests/client/collections/test_question_models.py -v`

Expected: All 6 tests PASS

- [ ] **Step 12: Commit Question model**

```bash
git add dnastack/client/collections/model.py tests/client/collections/test_question_models.py
git commit -m "[CU-86b8vuywp] Add Question model

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 2: Add QuestionQueryResultLoader

**Files:**
- Modify: `dnastack/client/collections/client.py` (add before CollectionServiceClient class)
- Test: `tests/client/collections/test_question_result_loader.py` (new file)

- [ ] **Step 1: Write failing test for QuestionQueryResultLoader initialization**

Create `tests/client/collections/test_question_result_loader.py`:

```python
from unittest.mock import Mock, MagicMock
from dnastack.client.collections.client import QuestionQueryResultLoader
from dnastack.common.tracing import Span


def test_loader_initialization():
    """Test QuestionQueryResultLoader initialization"""
    mock_session = Mock()
    trace = Span()

    loader = QuestionQueryResultLoader(
        service_url="http://test.com/query",
        http_session=mock_session,
        request_payload={"params": {"x": "1"}},
        trace=trace
    )

    assert loader.has_more() is True


def test_loader_has_more_after_load():
    """Test has_more after loading results"""
    mock_session = MagicMock()
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [{"id": "1"}],
        "pagination": None
    }
    mock_session.__enter__.return_value.post.return_value = mock_response

    loader = QuestionQueryResultLoader(
        service_url="http://test.com/query",
        http_session=mock_session,
        request_payload={"params": {}},
        trace=None
    )

    results = loader.load()

    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert loader.has_more() is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/client/collections/test_question_result_loader.py::test_loader_initialization -v`

Expected: FAIL with "ImportError: cannot import name 'QuestionQueryResultLoader'"

- [ ] **Step 3: Implement QuestionQueryResultLoader**

Add to `dnastack/client/collections/client.py` (before CollectionServiceClient class):

```python
from typing import Dict, Any
from dnastack.client.result_iterator import ResultLoader, InactiveLoaderError


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

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/client/collections/test_question_result_loader.py -v`

Expected: Both tests PASS

- [ ] **Step 5: Write test for pagination**

Add to `tests/client/collections/test_question_result_loader.py`:

```python
def test_loader_pagination():
    """Test QuestionQueryResultLoader follows pagination"""
    mock_session = MagicMock()

    # First response with next_page_url
    first_response = Mock()
    first_response.json.return_value = {
        "data": [{"id": "1"}, {"id": "2"}],
        "pagination": {"next_page_url": "http://test.com/page2"}
    }

    # Second response without next_page_url
    second_response = Mock()
    second_response.json.return_value = {
        "data": [{"id": "3"}],
        "pagination": None
    }

    mock_session.__enter__.return_value.post.return_value = first_response
    mock_session.__enter__.return_value.get.return_value = second_response

    loader = QuestionQueryResultLoader(
        service_url="http://test.com/query",
        http_session=mock_session,
        request_payload={"params": {"x": "1"}},
        trace=None
    )

    # Load first page
    page1 = loader.load()
    assert len(page1) == 2
    assert loader.has_more() is True

    # Load second page
    page2 = loader.load()
    assert len(page2) == 1
    assert loader.has_more() is False
```

- [ ] **Step 6: Run pagination test**

Run: `pytest tests/client/collections/test_question_result_loader.py::test_loader_pagination -v`

Expected: PASS

- [ ] **Step 7: Run all loader tests**

Run: `pytest tests/client/collections/test_question_result_loader.py -v`

Expected: All 3 tests PASS

- [ ] **Step 8: Commit QuestionQueryResultLoader**

```bash
git add dnastack/client/collections/client.py tests/client/collections/test_question_result_loader.py
git commit -m "[CU-86b8vuywp] Add QuestionQueryResultLoader for pagination

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Chunk 2: CollectionServiceClient Question Methods

### Task 3: Add list_questions Method

**Files:**
- Modify: `dnastack/client/collections/client.py:336` (add to CollectionServiceClient class)
- Test: `tests/client/collections/test_collection_service_questions.py` (new file)

- [ ] **Step 1: Write failing test for list_questions**

Create `tests/client/collections/test_collection_service_questions.py`:

```python
from unittest.mock import Mock, MagicMock, patch
from dnastack.client.collections.client import CollectionServiceClient
from dnastack.client.collections.model import Question, QuestionParameter
from dnastack.client.models import ServiceEndpoint


def test_list_questions_success():
    """Test list_questions returns list of Question objects"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.json.return_value = {
        "items": [
            {
                "id": "q1",
                "name": "Question 1",
                "collection_id": "coll1",
                "parameters": []
            },
            {
                "id": "q2",
                "name": "Question 2",
                "collection_id": "coll1",
                "description": "Test question",
                "parameters": [
                    {"name": "x", "input_type": "STRING", "required": True}
                ]
            }
        ]
    }

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.get.return_value = mock_response
        mock_session_creator.return_value = mock_session

        questions = client.list_questions("coll1")

    assert len(questions) == 2
    assert isinstance(questions[0], Question)
    assert questions[0].id == "q1"
    assert questions[0].name == "Question 1"
    assert questions[1].id == "q2"
    assert len(questions[1].parameters) == 1


def test_list_questions_empty():
    """Test list_questions with no questions"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.json.return_value = {"items": []}

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.get.return_value = mock_response
        mock_session_creator.return_value = mock_session

        questions = client.list_questions("coll1")

    assert questions == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/client/collections/test_collection_service_questions.py::test_list_questions_success -v`

Expected: FAIL with "AttributeError: 'CollectionServiceClient' object has no attribute 'list_questions'"

- [ ] **Step 3: Implement list_questions method**

Add to `dnastack/client/collections/client.py` in CollectionServiceClient class (after delete_collection method):

```python
    def list_questions(
        self,
        collection_id_or_slug_name: str,
        no_auth: bool = False,
        trace: Optional[Span] = None
    ) -> List['Question']:
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
        from dnastack.client.collections.model import Question

        trace = trace or Span(origin=self)
        with self.create_http_session(no_auth=no_auth) as session:
            url = urljoin(self.url, f'collections/{collection_id_or_slug_name}/questions')
            response = session.get(url, trace_context=trace)

            # API returns MultipleItemsResponse with items array
            response_data = response.json()
            return [Question(**item) for item in response_data.get('items', [])]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/client/collections/test_collection_service_questions.py -k "test_list_questions" -v`

Expected: Both tests PASS

- [ ] **Step 5: Commit list_questions**

```bash
git add dnastack/client/collections/client.py tests/client/collections/test_collection_service_questions.py
git commit -m "[CU-86b8vuywp] Add list_questions method to CollectionServiceClient

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 4: Add get_question Method

**Files:**
- Modify: `dnastack/client/collections/client.py` (add after list_questions)
- Test: `tests/client/collections/test_collection_service_questions.py`

- [ ] **Step 1: Write failing test for get_question**

Add to `tests/client/collections/test_collection_service_questions.py`:

```python
def test_get_question_success():
    """Test get_question returns Question object"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "variant_lookup",
        "name": "Variant Lookup",
        "description": "Look up variants",
        "collection_id": "my-variants",
        "parameters": [
            {"name": "chromosome", "input_type": "STRING", "required": True},
            {"name": "position", "input_type": "INTEGER", "required": True}
        ]
    }

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.get.return_value = mock_response
        mock_session_creator.return_value = mock_session

        question = client.get_question("my-variants", "variant_lookup")

    assert isinstance(question, Question)
    assert question.id == "variant_lookup"
    assert question.name == "Variant Lookup"
    assert question.description == "Look up variants"
    assert len(question.parameters) == 2
    assert question.parameters[0].name == "chromosome"
    assert question.parameters[0].required is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/client/collections/test_collection_service_questions.py::test_get_question_success -v`

Expected: FAIL with "AttributeError: 'CollectionServiceClient' object has no attribute 'get_question'"

- [ ] **Step 3: Implement get_question method**

Add to `dnastack/client/collections/client.py` after list_questions:

```python
    def get_question(
        self,
        collection_id_or_slug_name: str,
        question_id: str,
        no_auth: bool = False,
        trace: Optional[Span] = None
    ) -> 'Question':
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
        from dnastack.client.collections.model import Question

        trace = trace or Span(origin=self)
        with self.create_http_session(no_auth=no_auth) as session:
            url = urljoin(self.url, f'collections/{collection_id_or_slug_name}/questions/{question_id}')
            response = session.get(url, trace_context=trace)
            return Question(**response.json())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/client/collections/test_collection_service_questions.py::test_get_question_success -v`

Expected: PASS

- [ ] **Step 5: Commit get_question**

```bash
git add dnastack/client/collections/client.py tests/client/collections/test_collection_service_questions.py
git commit -m "[CU-86b8vuywp] Add get_question method to CollectionServiceClient

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 5: Add ask_question Method

**Files:**
- Modify: `dnastack/client/collections/client.py` (add after get_question)
- Test: `tests/client/collections/test_collection_service_questions.py`

- [ ] **Step 1: Write failing test for ask_question**

Add to `tests/client/collections/test_collection_service_questions.py`:

```python
from dnastack.client.result_iterator import ResultIterator


def test_ask_question_returns_iterator():
    """Test ask_question returns ResultIterator"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session_creator.return_value = mock_session

        result = client.ask_question(
            "my-collection",
            "my-question",
            {"param1": "value1"}
        )

    assert isinstance(result, ResultIterator)


def test_ask_question_executes_query():
    """Test ask_question makes correct API call"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [{"id": "1", "value": "result"}],
        "pagination": None
    }

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.post.return_value = mock_response
        mock_session_creator.return_value = mock_session

        result_iter = client.ask_question(
            "test-coll",
            "test-q",
            {"x": "1", "y": "2"}
        )

        # Consume iterator
        results = list(result_iter)

    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert results[0]["value"] == "result"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/client/collections/test_collection_service_questions.py::test_ask_question_returns_iterator -v`

Expected: FAIL with "AttributeError: 'CollectionServiceClient' object has no attribute 'ask_question'"

- [ ] **Step 3: Implement ask_question method**

Add to `dnastack/client/collections/client.py` after get_question:

```python
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/client/collections/test_collection_service_questions.py -k "test_ask_question" -v`

Expected: Both tests PASS

- [ ] **Step 5: Run all client question tests**

Run: `pytest tests/client/collections/test_collection_service_questions.py -v`

Expected: All tests PASS

- [ ] **Step 6: Commit ask_question**

```bash
git add dnastack/client/collections/client.py tests/client/collections/test_collection_service_questions.py
git commit -m "[CU-86b8vuywp] Add ask_question method to CollectionServiceClient

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Chunk 3: CLI Utilities

### Task 6: Create Publisher Questions Utils

**Files:**
- Create: `dnastack/cli/commands/publisher/questions/__init__.py`
- Create: `dnastack/cli/commands/publisher/questions/utils.py`
- Test: `tests/cli/commands/publisher/test_questions_utils.py` (new file)

- [ ] **Step 1: Create questions directory and __init__.py**

```bash
mkdir -p dnastack/cli/commands/publisher/questions
touch dnastack/cli/commands/publisher/questions/__init__.py
```

- [ ] **Step 2: Write failing test for get_collection_service_client**

Create `tests/cli/commands/publisher/test_questions_utils.py`:

```python
from unittest.mock import Mock, patch
from dnastack.cli.commands.publisher.questions.utils import get_collection_service_client
from dnastack.client.collections.client import CollectionServiceClient


def test_get_collection_service_client_no_args():
    """Test get_collection_service_client with no arguments"""
    with patch('dnastack.cli.commands.publisher.questions.utils.container') as mock_container:
        mock_factory = Mock()
        mock_client = Mock(spec=CollectionServiceClient)
        mock_factory.get.return_value = mock_client
        mock_container.get.return_value = mock_factory

        client = get_collection_service_client()

        assert client == mock_client
        mock_factory.get.assert_called_once_with(
            CollectionServiceClient,
            context_name=None,
            endpoint_id=None
        )


def test_get_collection_service_client_with_context():
    """Test get_collection_service_client with context"""
    with patch('dnastack.cli.commands.publisher.questions.utils.container') as mock_container:
        mock_factory = Mock()
        mock_client = Mock(spec=CollectionServiceClient)
        mock_factory.get.return_value = mock_client
        mock_container.get.return_value = mock_factory

        client = get_collection_service_client(context="test-ctx", endpoint_id="ep1")

        assert client == mock_client
        mock_factory.get.assert_called_once_with(
            CollectionServiceClient,
            context_name="test-ctx",
            endpoint_id="ep1"
        )
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/cli/commands/publisher/test_questions_utils.py::test_get_collection_service_client_no_args -v`

Expected: FAIL with "ImportError: cannot import name 'get_collection_service_client'"

- [ ] **Step 4: Implement get_collection_service_client**

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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/cli/commands/publisher/test_questions_utils.py -k "test_get_collection_service_client" -v`

Expected: Both tests PASS

- [ ] **Step 6: Commit get_collection_service_client**

```bash
git add dnastack/cli/commands/publisher/questions/utils.py tests/cli/commands/publisher/test_questions_utils.py
git commit -m "[CU-86b8vuywp] Add get_collection_service_client utility

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Write failing test for validate_question_parameters**

Add to `tests/cli/commands/publisher/test_questions_utils.py`:

```python
import pytest
from dnastack.cli.commands.publisher.questions.utils import validate_question_parameters
from dnastack.client.collections.model import Question, QuestionParameter


def test_validate_question_parameters_all_present():
    """Test validation passes when all required params present"""
    question = Question(
        id="q1",
        name="Test",
        collection_id="c1",
        parameters=[
            QuestionParameter(name="x", input_type="STRING", required=True),
            QuestionParameter(name="y", input_type="STRING", required=False)
        ]
    )

    inputs = {"x": "value1", "y": "value2"}

    result = validate_question_parameters(inputs, question)

    assert result == inputs


def test_validate_question_parameters_missing_required():
    """Test validation fails when required param missing"""
    question = Question(
        id="q1",
        name="Test",
        collection_id="c1",
        parameters=[
            QuestionParameter(name="req1", input_type="STRING", required=True),
            QuestionParameter(name="req2", input_type="STRING", required=True),
            QuestionParameter(name="opt", input_type="STRING", required=False)
        ]
    )

    inputs = {"req1": "value1"}  # Missing req2

    with pytest.raises(ValueError) as exc_info:
        validate_question_parameters(inputs, question)

    assert "Missing required parameters: req2" in str(exc_info.value)


def test_validate_question_parameters_only_required():
    """Test validation passes with only required params"""
    question = Question(
        id="q1",
        name="Test",
        collection_id="c1",
        parameters=[
            QuestionParameter(name="req", input_type="STRING", required=True),
            QuestionParameter(name="opt", input_type="STRING", required=False)
        ]
    )

    inputs = {"req": "value1"}

    result = validate_question_parameters(inputs, question)

    assert result == inputs
```

- [ ] **Step 8: Run test to verify it fails**

Run: `pytest tests/cli/commands/publisher/test_questions_utils.py::test_validate_question_parameters_all_present -v`

Expected: FAIL with "ImportError: cannot import name 'validate_question_parameters'"

- [ ] **Step 9: Implement validate_question_parameters**

Add to `dnastack/cli/commands/publisher/questions/utils.py`:

```python
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
```

- [ ] **Step 10: Run tests to verify they pass**

Run: `pytest tests/cli/commands/publisher/test_questions_utils.py -k "test_validate_question_parameters" -v`

Expected: All 3 tests PASS

- [ ] **Step 11: Commit validate_question_parameters**

```bash
git add dnastack/cli/commands/publisher/questions/utils.py tests/cli/commands/publisher/test_questions_utils.py
git commit -m "[CU-86b8vuywp] Add validate_question_parameters utility

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

- [ ] **Step 12: Write failing test for handle_question_results_output**

Add to `tests/cli/commands/publisher/test_questions_utils.py`:

```python
from unittest.mock import patch, call
from dnastack.cli.commands.publisher.questions.utils import handle_question_results_output


def test_handle_question_results_output_delegates_to_explorer():
    """Test handle_question_results_output delegates to explorer util"""
    results = [{"id": "1"}, {"id": "2"}]

    with patch('dnastack.cli.commands.publisher.questions.utils.explorer_output_handler') as mock_handler:
        handle_question_results_output(results, None, "json")

        mock_handler.assert_called_once_with(results, None, "json")


def test_handle_question_results_output_with_file():
    """Test handle_question_results_output with output file"""
    results = [{"id": "1"}]

    with patch('dnastack.cli.commands.publisher.questions.utils.explorer_output_handler') as mock_handler:
        handle_question_results_output(results, "output.json", "json")

        mock_handler.assert_called_once_with(results, "output.json", "json")
```

- [ ] **Step 13: Run test to verify it fails**

Run: `pytest tests/cli/commands/publisher/test_questions_utils.py::test_handle_question_results_output_delegates_to_explorer -v`

Expected: FAIL with "ImportError: cannot import name 'handle_question_results_output'"

- [ ] **Step 14: Implement handle_question_results_output**

Add to `dnastack/cli/commands/publisher/questions/utils.py`:

```python
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

- [ ] **Step 15: Run tests to verify they pass**

Run: `pytest tests/cli/commands/publisher/test_questions_utils.py -k "test_handle_question_results_output" -v`

Expected: Both tests PASS

- [ ] **Step 16: Run all utils tests**

Run: `pytest tests/cli/commands/publisher/test_questions_utils.py -v`

Expected: All tests PASS

- [ ] **Step 17: Commit handle_question_results_output**

```bash
git add dnastack/cli/commands/publisher/questions/utils.py tests/cli/commands/publisher/test_questions_utils.py
git commit -m "[CU-86b8vuywp] Add handle_question_results_output utility

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Chunk 4: CLI Commands

### Task 7: Implement List Command

**Files:**
- Create: `dnastack/cli/commands/publisher/questions/commands.py`
- Test: `tests/cli/commands/publisher/test_questions_commands.py` (new file)

- [ ] **Step 1: Write failing test for list command**

Create `tests/cli/commands/publisher/test_questions_commands.py`:

```python
from unittest.mock import Mock, patch
from click.testing import CliRunner
from dnastack.cli.commands.publisher.questions.commands import init_questions_commands
from dnastack.cli.core.group import formatted_group
from dnastack.client.collections.model import Question


@formatted_group("test_questions")
def test_questions_group():
    """Test questions command group"""
    pass


def test_list_questions_command():
    """Test list questions command"""
    init_questions_commands(test_questions_group)
    runner = CliRunner()

    mock_question = Question(
        id="q1",
        name="Test Question",
        collection_id="coll1",
        parameters=[]
    )

    with patch('dnastack.cli.commands.publisher.questions.commands.get_collection_service_client') as mock_get_client:
        mock_client = Mock()
        mock_client.list_questions.return_value = [mock_question]
        mock_get_client.return_value = mock_client

        result = runner.invoke(test_questions_group, ['list', '--collection', 'test-coll'])

    assert result.exit_code == 0
    assert "q1" in result.output
    assert "Test Question" in result.output


def test_list_questions_missing_collection():
    """Test list questions command without collection flag"""
    init_questions_commands(test_questions_group)
    runner = CliRunner()

    result = runner.invoke(test_questions_group, ['list'])

    assert result.exit_code != 0
    assert "collection" in result.output.lower() or "required" in result.output.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/cli/commands/publisher/test_questions_commands.py::test_list_questions_command -v`

Expected: FAIL with "ImportError: cannot import name 'init_questions_commands'"

- [ ] **Step 3: Implement list command**

Create `dnastack/cli/commands/publisher/questions/commands.py`:

```python
from typing import Optional

import click
from click import Group

from dnastack.cli.commands.publisher.questions.utils import (
    get_collection_service_client,
    validate_question_parameters,
    handle_question_results_output
)
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import (
    ArgumentSpec,
    CONTEXT_ARG,
    SINGLE_ENDPOINT_ID_ARG,
    ArgumentType,
    RESOURCE_OUTPUT_ARG,
    DATA_OUTPUT_ARG
)
from dnastack.cli.helpers.iterator_printer import show_iterator
from dnastack.common.json_argument_parser import JsonLike, parse_and_merge_arguments
from dnastack.common.logger import get_logger
from dnastack.common.tracing import Span

logger = get_logger(__name__)


def init_questions_commands(group: Group):
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/cli/commands/publisher/test_questions_commands.py -k "test_list_questions" -v`

Expected: Both tests PASS

- [ ] **Step 5: Commit list command**

```bash
git add dnastack/cli/commands/publisher/questions/commands.py tests/cli/commands/publisher/test_questions_commands.py
git commit -m "[CU-86b8vuywp] Add list questions CLI command

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 8: Implement Describe Command

**Files:**
- Modify: `dnastack/cli/commands/publisher/questions/commands.py`
- Test: `tests/cli/commands/publisher/test_questions_commands.py`

- [ ] **Step 1: Write failing test for describe command**

Add to `tests/cli/commands/publisher/test_questions_commands.py`:

```python
from dnastack.client.collections.model import QuestionParameter


def test_describe_question_command():
    """Test describe question command"""
    runner = CliRunner()

    mock_question = Question(
        id="variant_lookup",
        name="Variant Lookup",
        description="Look up variants by position",
        collection_id="coll1",
        parameters=[
            QuestionParameter(name="chromosome", input_type="STRING", required=True),
            QuestionParameter(name="position", input_type="INTEGER", required=True)
        ]
    )

    with patch('dnastack.cli.commands.publisher.questions.commands.get_collection_service_client') as mock_get_client:
        mock_client = Mock()
        mock_client.get_question.return_value = mock_question
        mock_get_client.return_value = mock_client

        result = runner.invoke(test_questions_group, [
            'describe',
            'variant_lookup',
            '--collection', 'test-coll'
        ])

    assert result.exit_code == 0
    assert "variant_lookup" in result.output
    assert "Variant Lookup" in result.output
    assert "chromosome" in result.output


def test_describe_question_missing_args():
    """Test describe command without required args"""
    runner = CliRunner()

    result = runner.invoke(test_questions_group, ['describe'])

    assert result.exit_code != 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/cli/commands/publisher/test_questions_commands.py::test_describe_question_command -v`

Expected: FAIL with "AssertionError: assert 2 == 0" (command not found)

- [ ] **Step 3: Implement describe command**

Add to `dnastack/cli/commands/publisher/questions/commands.py` (inside init_questions_commands function):

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

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/cli/commands/publisher/test_questions_commands.py -k "test_describe_question" -v`

Expected: Both tests PASS

- [ ] **Step 5: Commit describe command**

```bash
git add dnastack/cli/commands/publisher/questions/commands.py tests/cli/commands/publisher/test_questions_commands.py
git commit -m "[CU-86b8vuywp] Add describe question CLI command

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 9: Implement Ask Command

**Files:**
- Modify: `dnastack/cli/commands/publisher/questions/commands.py`
- Test: `tests/cli/commands/publisher/test_questions_commands.py`

- [ ] **Step 1: Write failing test for ask command**

Add to `tests/cli/commands/publisher/test_questions_commands.py`:

```python
def test_ask_question_command():
    """Test ask question command"""
    runner = CliRunner()

    mock_question = Question(
        id="test_q",
        name="Test Q",
        collection_id="coll1",
        parameters=[
            QuestionParameter(name="x", input_type="STRING", required=True)
        ]
    )

    mock_results = [
        {"id": "1", "value": "result1"},
        {"id": "2", "value": "result2"}
    ]

    with patch('dnastack.cli.commands.publisher.questions.commands.get_collection_service_client') as mock_get_client:
        mock_client = Mock()
        mock_client.get_question.return_value = mock_question
        mock_client.ask_question.return_value = iter(mock_results)
        mock_get_client.return_value = mock_client

        with patch('dnastack.cli.commands.publisher.questions.commands.handle_question_results_output') as mock_output:
            result = runner.invoke(test_questions_group, [
                'ask',
                '--question-name', 'test_q',
                '--collection', 'test-coll',
                '--param', 'x=value1'
            ])

    assert result.exit_code == 0
    mock_output.assert_called_once()


def test_ask_question_missing_required_param():
    """Test ask command fails when required param missing"""
    runner = CliRunner()

    mock_question = Question(
        id="test_q",
        name="Test Q",
        collection_id="coll1",
        parameters=[
            QuestionParameter(name="required_param", input_type="STRING", required=True)
        ]
    )

    with patch('dnastack.cli.commands.publisher.questions.commands.get_collection_service_client') as mock_get_client:
        mock_client = Mock()
        mock_client.get_question.return_value = mock_question
        mock_get_client.return_value = mock_client

        result = runner.invoke(test_questions_group, [
            'ask',
            '--question-name', 'test_q',
            '--collection', 'test-coll'
        ])

    assert result.exit_code != 0
    assert "Missing required parameters" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/cli/commands/publisher/test_questions_commands.py::test_ask_question_command -v`

Expected: FAIL (command not found)

- [ ] **Step 3: Implement ask command**

Add to `dnastack/cli/commands/publisher/questions/commands.py` (inside init_questions_commands):

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

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/cli/commands/publisher/test_questions_commands.py -k "test_ask_question" -v`

Expected: Both tests PASS

- [ ] **Step 5: Run all command tests**

Run: `pytest tests/cli/commands/publisher/test_questions_commands.py -v`

Expected: All tests PASS

- [ ] **Step 6: Commit ask command**

```bash
git add dnastack/cli/commands/publisher/questions/commands.py tests/cli/commands/publisher/test_questions_commands.py
git commit -m "[CU-86b8vuywp] Add ask question CLI command

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Chunk 5: Command Group Registration

### Task 10: Register Questions Command Group

**Files:**
- Modify: `dnastack/cli/commands/publisher/questions/__init__.py`
- Modify: `dnastack/cli/commands/publisher/__init__.py`
- Test: `tests/cli/commands/publisher/test_questions_integration.py` (new file)

- [ ] **Step 1: Write failing integration test**

Create `tests/cli/commands/publisher/test_questions_integration.py`:

```python
from click.testing import CliRunner
from dnastack.cli.commands.publisher import publisher_command_group


def test_questions_group_registered():
    """Test questions command group is registered under publisher"""
    runner = CliRunner()

    result = runner.invoke(publisher_command_group, ['questions', '--help'])

    assert result.exit_code == 0
    assert "questions" in result.output.lower()
    assert "list" in result.output
    assert "describe" in result.output
    assert "ask" in result.output


def test_questions_list_available():
    """Test list command is available"""
    runner = CliRunner()

    result = runner.invoke(publisher_command_group, ['questions', 'list', '--help'])

    assert result.exit_code == 0
    assert "collection" in result.output.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/cli/commands/publisher/test_questions_integration.py::test_questions_group_registered -v`

Expected: FAIL (questions group not found)

- [ ] **Step 3: Update questions/__init__.py to create group**

Edit `dnastack/cli/commands/publisher/questions/__init__.py`:

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

- [ ] **Step 4: Register questions group in publisher**

Edit `dnastack/cli/commands/publisher/__init__.py`:

Find the section that imports and registers command groups (after datasources_command_group import):

```python
from dnastack.cli.commands.publisher.questions import questions_command_group
```

And add registration (after datasources registration):

```python
publisher_command_group.add_command(questions_command_group)
```

- [ ] **Step 5: Run integration tests**

Run: `pytest tests/cli/commands/publisher/test_questions_integration.py -v`

Expected: Both tests PASS

- [ ] **Step 6: Commit command group registration**

```bash
git add dnastack/cli/commands/publisher/questions/__init__.py dnastack/cli/commands/publisher/__init__.py tests/cli/commands/publisher/test_questions_integration.py
git commit -m "[CU-86b8vuywp] Register questions command group under publisher

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Chunk 6: Final Testing and Validation

### Task 11: Run Full Test Suite

**Files:**
- None (verification only)

- [ ] **Step 1: Run all new unit tests**

Run: `pytest tests/client/collections/test_question*.py tests/cli/commands/publisher/test_questions*.py -v`

Expected: All tests PASS

- [ ] **Step 2: Run full test suite**

Run: `make test-unit`

Expected: All tests PASS

- [ ] **Step 3: Check test coverage for new code**

Run: `make test-unit-cov`

Expected: Coverage >80% for new files

- [ ] **Step 4: Run linting**

Run: `make lint`

Expected: No linting errors

- [ ] **Step 5: Fix any linting issues if present**

Run: `make lint-fix`

Expected: Linting issues auto-fixed

- [ ] **Step 6: Re-run tests after lint fixes**

Run: `make test-unit`

Expected: All tests still PASS

- [ ] **Step 7: Commit any lint fixes**

```bash
git add -u
git commit -m "[CU-86b8vuywp] Fix linting issues

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Task 12: Manual Testing

**Files:**
- None (manual verification)

- [ ] **Step 1: Test CLI installation**

Run: `uv run dnastack publisher questions --help`

Expected: Shows questions commands (list, describe, ask)

- [ ] **Step 2: Verify list command help**

Run: `uv run dnastack publisher questions list --help`

Expected: Shows --collection flag and options

- [ ] **Step 3: Verify describe command help**

Run: `uv run dnastack publisher questions describe --help`

Expected: Shows positional question_id and --collection flag

- [ ] **Step 4: Verify ask command help**

Run: `uv run dnastack publisher questions ask --help`

Expected: Shows --question-name, --collection, --param, --output-file, --output flags

- [ ] **Step 5: Document manual testing results**

Create note of successful manual tests or any issues found

### Task 13: Final Verification and Push

**Files:**
- None (git operations)

- [ ] **Step 1: Verify all changes are committed**

Run: `git status`

Expected: "nothing to commit, working tree clean"

- [ ] **Step 2: View commit history**

Run: `git log --oneline -15`

Expected: Shows all commits for this feature

- [ ] **Step 3: Verify branch name**

Run: `git branch --show-current`

Expected: Shows "add_publisher_questions_ask-CU-86b8vuywp"

- [ ] **Step 4: Push branch to remote (if applicable)**

Run: `git push -u origin add_publisher_questions_ask-CU-86b8vuywp`

Expected: Branch pushed to remote

---

## Success Criteria Checklist

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
- [ ] All files committed with proper messages
- [ ] Feature branch created with ticket ID

## Implementation Notes

- Follow TDD strictly - write test, see it fail, implement, see it pass
- Commit frequently (after each logical unit)
- Run tests after every code change
- Use @superpowers:test-driven-development if available
- Reuse explorer utilities where applicable (output handling)
- Mirror explorer questions structure for consistency
- All commit messages include ticket ID and co-author line

## References

- **Spec:** `docs/superpowers/specs/2026-03-13-publisher-questions-ask-design.md`
- **Ticket:** https://app.clickup.com/t/86b8vuywp
- **Explorer Questions:** `dnastack/cli/commands/explorer/questions/`
- **Collection Service:** `../collection-service/src/main/java/com/dnastack/collectionservice/question/`
