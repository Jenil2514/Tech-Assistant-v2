from abc import ABC, abstractmethod

from app.provisioning.models import ConnectorResult, Employee, RoleMapping


class TaskAdapterConfigurationError(RuntimeError):
    pass


class TaskManagementAdapter(ABC):
    @abstractmethod
    def invite_user(self, employee: Employee, role_mapping: RoleMapping) -> ConnectorResult:
        raise NotImplementedError

    @abstractmethod
    def create_onboarding_tasks(
        self,
        employee: Employee,
        role_mapping: RoleMapping,
    ) -> list[ConnectorResult]:
        raise NotImplementedError
