from dnastack.client.collections.model import Question, QuestionParameter


def test_question_parameter_model():
    param = QuestionParameter(
        name="sample_id",
        input_type="text",
        required=True,
        description="Sample identifier",
        default_value="SAM123",
        test_value="TEST456"
    )
    assert param.name == "sample_id"
    assert param.input_type == "text"
    assert param.required is True
    assert param.description == "Sample identifier"
    assert param.default_value == "SAM123"
    assert param.test_value == "TEST456"


def test_question_parameter_minimal():
    param = QuestionParameter(
        name="gene",
        input_type="text",
        required=False
    )
    assert param.name == "gene"
    assert param.input_type == "text"
    assert param.required is False
    assert param.description is None
    assert param.default_value is None
    assert param.test_value is None


def test_question_model():
    params = [
        QuestionParameter(name="param1", input_type="text", required=True),
        QuestionParameter(name="param2", input_type="number", required=False)
    ]
    question = Question(
        id="q1",
        name="Test Question",
        description="A test question",
        collection_id="col1",
        parameters=params
    )
    assert question.id == "q1"
    assert question.name == "Test Question"
    assert question.description == "A test question"
    assert question.collection_id == "col1"
    assert len(question.parameters) == 2


def test_question_minimal():
    question = Question(
        id="q2",
        name="Minimal Question",
        collection_id="col2"
    )
    assert question.id == "q2"
    assert question.name == "Minimal Question"
    assert question.collection_id == "col2"
    assert question.description is None
    assert question.parameters == []
