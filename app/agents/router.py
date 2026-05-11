from dataclasses import dataclass


RAG_AGENT = "rag"
REPORT_AGENT = "report"
PROVISIONING_AGENT = "provisioning"
UNKNOWN_AGENT = "unknown"


@dataclass(frozen=True)
class RoutedRequest:
    agent: str
    text: str
    source: str
    command: str | None = None


def route_slash_command(command: str, text: str) -> RoutedRequest:
    normalized_command = command.strip().lower()
    normalized_text = text.strip()

    if normalized_command == "/query":
        return RoutedRequest(
            agent=RAG_AGENT,
            text=normalized_text,
            source="slash_command",
            command=normalized_command,
        )

    if normalized_command == "/report":
        return RoutedRequest(
            agent=REPORT_AGENT,
            text=normalized_text,
            source="slash_command",
            command=normalized_command,
        )

    if normalized_command == "/onboard":
        return RoutedRequest(
            agent=PROVISIONING_AGENT,
            text=normalized_text,
            source="slash_command",
            command=normalized_command,
        )

    return RoutedRequest(
        agent=UNKNOWN_AGENT,
        text=normalized_text,
        source="slash_command",
        command=normalized_command,
    )


def route_app_mention(text: str) -> RoutedRequest:
    return RoutedRequest(
        agent=RAG_AGENT,
        text=text.strip(),
        source="app_mention",
    )
