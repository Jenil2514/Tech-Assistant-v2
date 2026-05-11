import re
import shlex

from app.provisioning.models import Employee


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ProvisioningInputError(ValueError):
    pass


def parse_onboard_command(text: str) -> Employee:
    try:
        parts = shlex.split(text)
    except ValueError as exc:
        raise ProvisioningInputError("Use `/onboard \"Full Name\" email@example.com role-key`.") from exc

    if len(parts) != 3:
        raise ProvisioningInputError("Use `/onboard \"Full Name\" email@example.com role-key`.")

    name, email, role = parts
    normalized_name = name.strip()
    normalized_email = email.strip().lower()
    normalized_role = role.strip().lower()

    if not normalized_name:
        raise ProvisioningInputError("Please provide the new joiner's full name.")

    if not EMAIL_RE.match(normalized_email):
        raise ProvisioningInputError("Please provide a valid email address.")

    if not normalized_role:
        raise ProvisioningInputError("Please provide a role key such as `backend-engineer`.")

    return Employee(
        name=normalized_name,
        email=normalized_email,
        role=normalized_role,
    )
