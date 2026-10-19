"""The names the engine commands give each engine type, kept apart so every engine module can import them."""
from typing import Any, Dict, Optional

from dnastack.client.workbench.ewes.engine_models import EngineAdapterType

# The `engines create` and `engines update` subcommand of each adapter type.
SUBCOMMAND_NAMES: Dict[EngineAdapterType, str] = {
    EngineAdapterType.GCP_CLOUD_RUN_CROMWELL: 'gcp',
    EngineAdapterType.WES_ON_CROMWELL: 'wes',
    EngineAdapterType.AZURE_CONTAINER_APP_CROMWELL: 'azure',
    EngineAdapterType.AWS_HEALTH_OMICS: 'aws',
}


def subcommand_for(adapter_type: Any) -> Optional[str]:
    """The create/update subcommand for an adapter type.

    A type with no subcommand is returned as it is only if it is one of the known adapter types, and is None
    otherwise, so that a value read from input is never echoed.
    """
    if not isinstance(adapter_type, str) or adapter_type not in {t.value for t in EngineAdapterType}:
        return None
    return SUBCOMMAND_NAMES.get(EngineAdapterType(adapter_type), adapter_type)


def with_article(subcommand: str) -> str:
    """'a gcp', 'an aws': the subcommand name with the article it is read with."""
    return f"{'an' if subcommand[0] in 'aeiou' else 'a'} {subcommand}"
