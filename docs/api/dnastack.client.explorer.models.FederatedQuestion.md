#### Class `dnastack.client.explorer.models.FederatedQuestion(id: str, name: str, description: str, params: List[dnastack.client.explorer.models.QuestionParam], collections: List[dnastack.client.explorer.models.QuestionCollection])`
A federated question that can be asked across multiple collections.

Based on the Java FederatedQuestion record from the Explorer service.
##### Properties
###### `id: str`

###### `name: str`

###### `description: str`

###### `params: List[dnastack.client.explorer.models.QuestionParam]`

###### `collections: List[dnastack.client.explorer.models.QuestionCollection]`

##### Methods
###### `@staticmethod def construct(_fields_set: Optional['SetStr'], **values) -> 'Model'`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], update: Optional['DictStrAny'], deep: bool) -> 'Model'`
Duplicate a model, optionally choose which fields to include, exclude and change.

    the new model: you should trust this data

| Parameter | Description |
| --- | --- |
| `include` | fields to include in new model |
| `exclude` | fields to exclude from new model, as with values this takes precedence over include |
| `update` | values to change/add in the new model. Note: the data is not validated before creating |
| `deep` | set to `True` to make a deep copy of the model |

| Return |
| --- |
| new model instance |
###### `def dict(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> 'DictStrAny'`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Optional[Callable[[Any], Any]], models_as_dict: bool= True, **dumps_kwargs) -> str`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.