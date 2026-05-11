from app.config.settings import settings
from app.integrations.task_management.base import TaskManagementAdapter, TaskAdapterConfigurationError
from app.integrations.task_management.linear import LinearTaskAdapter


def get_task_management_adapter() -> TaskManagementAdapter:
    adapter_name = (settings.TASK_ADAPTER or "").strip().lower()

    if adapter_name == "linear":
        return LinearTaskAdapter()

    raise TaskAdapterConfigurationError(
        f"Unsupported TASK_ADAPTER `{settings.TASK_ADAPTER}`. Currently supported: linear."
    )
