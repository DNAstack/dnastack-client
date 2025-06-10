from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QuestionParam(BaseModel):
    """
    A parameter definition for a question.
    
    Based on the Java QuestionParam class from the Explorer service.
    """
    id: str
    name: str
    label: str
    input_type: str = Field(alias="inputType")
    description: Optional[str] = None
    required: bool = False
    default_value: Optional[str] = Field(default=None, alias="defaultValue")
    test_value: Optional[str] = Field(default=None, alias="testValue")
    input_subtype: Optional[str] = Field(default=None, alias="inputSubtype")
    allowed_values: Optional[str] = Field(default=None, alias="allowedValues")
    table: Optional[str] = None
    column: Optional[str] = None
    values: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class QuestionCollection(BaseModel):
    """
    A collection reference within a federated question.
    """
    id: str
    slug: str
    name: str
    question_id: str = Field(alias="questionId")

    class Config:
        allow_population_by_field_name = True


class FederatedQuestion(BaseModel):
    """
    A federated question that can be asked across multiple collections.
    
    Based on the Java FederatedQuestion record from the Explorer service.
    """
    id: str
    name: str
    description: str
    params: List[QuestionParam]
    collections: List[QuestionCollection]


class FederatedQuestionListResponse(BaseModel):
    """
    Response containing a list of federated questions.
    """
    questions: List[FederatedQuestion]


class FederatedQuestionQueryRequest(BaseModel):
    """
    Request payload for asking a federated question.
    
    Based on the Java FederatedQuestionQueryRequest record.
    """
    inputs: Dict[str, str]
    collections: List[str]


class FederatedQuestionQueryResponse(BaseModel):
    """
    Response from asking a federated question.
    
    This is a flexible model to handle various response formats.
    The actual structure depends on the question being asked.
    """
    # This will contain the actual query results
    # Structure varies based on the question type
    data: Any = None
    
    def __init__(self, **data):
        # Handle raw response data
        super().__init__(data=data)


class QuestionQueryResult(BaseModel):
    """
    A single result item from a question query.
    
    This is a flexible model to handle different result structures
    depending on the question type.
    """
    # Dynamic content - structure varies by question
    content: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data):
        super().__init__(content=data)

    def __getitem__(self, key):
        return self.content[key]

    def __setitem__(self, key, value):
        self.content[key] = value

    def get(self, key, default=None):
        return self.content.get(key, default)

    def keys(self):
        return self.content.keys()

    def values(self):
        return self.content.values()

    def items(self):
        return self.content.items()