from typing import List, Dict, Any
from dnastack.client.explorer.models import FederatedQuestion


def format_question_list_table(questions: List[FederatedQuestion]) -> List[Dict[str, Any]]:
    """
    Format a list of federated questions for table display.
    
    Args:
        questions: List of FederatedQuestion objects
        
    Returns:
        List[Dict[str, Any]]: Formatted table data
    """
    table_data = []
    
    for question in questions:
        row = {
            'ID': question.id,
            'Name': question.name,
            'Description': question.description,
            'Parameters': len(question.params),
            'Collections': len(question.collections),
            'Required Params': len([p for p in question.params if p.required])
        }
        table_data.append(row)
    
    return table_data


def format_question_detail_table(question: FederatedQuestion) -> Dict[str, Any]:
    """
    Format a single federated question for detailed display.
    
    Args:
        question: FederatedQuestion object
        
    Returns:
        Dict[str, Any]: Formatted question details
    """
    # Format parameters
    params_info = []
    for param in question.params:
        param_info = {
            'Name': param.name,
            'Type': param.input_type,
            'Required': 'Yes' if param.required else 'No',
            'Description': param.description or '',
            'Default': param.default_value or ''
        }
        
        # Add dropdown values if available
        if param.values and param.input_subtype == "DROPDOWN":
            values_list = param.values.split('\n')
            param_info['Choices'] = ', '.join(values_list[:3]) + ('...' if len(values_list) > 3 else '')
        
        params_info.append(param_info)
    
    # Format collections
    collections_info = []
    for col in question.collections:
        col_info = {
            'ID': col.id,
            'Name': col.name,
            'Slug': col.slug,
            'Question ID': col.question_id
        }
        collections_info.append(col_info)
    
    return {
        'question': {
            'ID': question.id,
            'Name': question.name,
            'Description': question.description
        },
        'parameters': params_info,
        'collections': collections_info
    }


def format_question_results_table(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format question query results for table display.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        List[Dict[str, Any]]: Formatted table data
    """
    if not results:
        return []
    
    # For complex nested results, we'll flatten them
    formatted_results = []
    
    for result in results:
        # If result is already flat, use as-is
        if all(not isinstance(v, (dict, list)) for v in result.values()):
            formatted_results.append(result)
        else:
            # Flatten complex nested structures
            flattened = _flatten_dict(result)
            formatted_results.append(flattened)
    
    return formatted_results


def _flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys
        
    Returns:
        Dict[str, Any]: Flattened dictionary
    """
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            if v and isinstance(v[0], dict):
                # For lists of dicts, create separate entries
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(_flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                # For simple lists, join with commas
                items.append((new_key, ', '.join(str(x) for x in v)))
        else:
            items.append((new_key, v))
    
    return dict(items)