from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

from app.agents.router import (
    PROVISIONING_AGENT,
    RAG_AGENT,
    REPORT_AGENT,
    route_app_mention,
    route_slash_command,
)
from app.config.settings import settings
from app.provisioning.models import OnboardingActionResult, ProvisioningRequest
from app.provisioning.parser import ProvisioningInputError
from app.provisioning.role_mappings import UnknownRoleError
from app.provisioning.service import (
    approve_onboarding_request,
    create_onboarding_request,
    reject_onboarding_request,
)
from app.rag.service import answer_rag_question


app_slack = App(
    token=settings.SLACK_BOT_TOKEN,
    signing_secret=settings.SLACK_SIGNING_SECRET,
    token_verification_enabled=False,
)

handler = SlackRequestHandler(app_slack)


def _query_progress_response(question: str):
    return {
        "response_type": "ephemeral",
        "text": "Working on your question...",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Working on your question*\n>{question}",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Searching docs - ranking matches - drafting answer",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "_This usually takes a few seconds._",
                    },
                ],
            },
        ],
    }


def _query_final_response(answer: str):
    answer_block_text = answer

    return {
        "response_type": "ephemeral",
        "replace_original": True,
        "text": answer,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": answer_block_text,
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Answered from retrieved company knowledge.",
                    },
                ],
            },
        ],
    }


def _ephemeral_message(text: str, replace_original: bool = True):
    return {
        "response_type": "ephemeral",
        "replace_original": replace_original,
        "text": text,
    }


def _slack_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _onboarding_preview_response(request: ProvisioningRequest):
    employee = request.employee
    access_lines = "\n".join(
        f"- {_slack_escape(item)}"
        for item in request.role_mapping.access_summary
    )
    task_count = len(request.role_mapping.linear_issue_templates)

    return {
        "response_type": "ephemeral",
        "text": f"Onboarding approval needed for {employee.name}.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Onboarding approval needed*\n"
                        f"*Name:* {_slack_escape(employee.name)}\n"
                        f"*Email:* `{_slack_escape(employee.email)}`\n"
                        f"*Role:* `{_slack_escape(employee.role)}` "
                        f"({_slack_escape(request.role_mapping.display_name)})\n"
                        f"*Status:* Pending approval"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Role mapping / planned access*\n{access_lines}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Planned actions after approval*\n"
                        "- Append employee row to local CSV register\n"
                        "- Send Linear workspace invite\n"
                        f"- Create 1 Linear parent issue with {task_count} onboarding sub-issues"
                    ),
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "action_id": "provisioning_approve",
                        "value": request.request_id,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "style": "danger",
                        "action_id": "provisioning_reject",
                        "value": request.request_id,
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Request `{request.request_id}`. Only configured approvers can approve.",
                    },
                ],
            },
        ],
    }


def _onboarding_result_response(result: OnboardingActionResult):
    if result.request is None:
        return _ephemeral_message(result.message)

    request = result.request
    employee = request.employee
    parent_issue_count = sum(
        1
        for task_result in result.linear_task_results
        if task_result.metadata.get("issue_type") == "parent"
    )
    sub_issue_count = sum(
        1
        for task_result in result.linear_task_results
        if task_result.metadata.get("issue_type") == "sub_issue"
    )

    if result.status == "completed":
        status_text = (
            f"*Onboarding completed for {_slack_escape(employee.name)}*\n"
            f"*Email:* `{_slack_escape(employee.email)}`\n"
            f"*Role:* `{_slack_escape(employee.role)}`\n\n"
            f"OK Employee register row {'created' if result.csv_appended else 'already existed'}\n"
            "OK Linear invite sent\n"
            f"OK Linear onboarding issue created ({parent_issue_count} parent, {sub_issue_count} sub-issues)\n"
            "OK Audit log stored"
        )
    elif result.status == "rejected":
        status_text = (
            f"*Onboarding rejected for {_slack_escape(employee.name)}*\n"
            "No CSV row or Linear changes were made.\n"
            "OK Audit log stored"
        )
    elif result.status == "failed":
        status_text = (
            f"*Onboarding failed for {_slack_escape(employee.name)}*\n"
            f"*Email:* `{_slack_escape(employee.email)}`\n\n"
            f"CSV row: {'created' if result.csv_appended else 'not created or already existed'}\n"
            f"Linear invite: `{_slack_escape(request.linear_invite_status)}`\n"
            f"Linear tasks: `{_slack_escape(request.linear_tasks_status)}`\n"
            f"Audit request: `{request.request_id}`"
        )
    else:
        status_text = (
            f"*Onboarding status: `{_slack_escape(result.status)}`*\n"
            f"{_slack_escape(result.message)}\n"
            f"Request `{request.request_id}`"
        )

    return {
        "response_type": "ephemeral",
        "replace_original": True,
        "text": result.message,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": status_text,
                },
            }
        ],
    }


def _onboarding_working_response():
    return {
        "response_type": "ephemeral",
        "replace_original": True,
        "text": "Running approved onboarding workflow...",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Running approved onboarding workflow*",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Writing employee register - sending Linear invite - creating onboarding issue and sub-issues",
                    },
                ],
            },
        ],
    }


def _handle_query_command(command, ack, respond):
    routed = route_slash_command(command.get("command", ""), command.get("text", ""))

    ack(_query_progress_response(routed.text or "No question provided"))

    if routed.agent != RAG_AGENT:
        respond(_ephemeral_message("I do not know how to handle that command yet."))
        return

    if not routed.text:
        respond(_ephemeral_message("Please add a question after `/query`."))
        return

    try:
        response = answer_rag_question(routed.text)

        respond(_query_final_response(response))
    except Exception:
        respond(_ephemeral_message("Something went wrong while answering that question. Please try again."))
        raise


def _handle_report_command(command, ack, respond):
    routed = route_slash_command(command.get("command", ""), command.get("text", ""))

    ack({
        "response_type": "ephemeral",
        "text": "Preparing report...",
    })

    if routed.agent != REPORT_AGENT:
        respond(_ephemeral_message("I do not know how to handle that command yet."))
        return

    respond(_ephemeral_message("Report command received. The report agent is not implemented yet."))


def _handle_onboard_command(command, ack, respond):
    routed = route_slash_command(command.get("command", ""), command.get("text", ""))

    if routed.agent != PROVISIONING_AGENT:
        ack(_ephemeral_message("I do not know how to handle that command yet."))
        return

    try:
        request = create_onboarding_request(
            text=routed.text,
            requester_id=command.get("user_id", ""),
            workspace_id=command.get("team_id", ""),
            channel_id=command.get("channel_id"),
        )
    except (ProvisioningInputError, UnknownRoleError) as exc:
        ack(_ephemeral_message(str(exc), replace_original=False))
        return
    except Exception:
        ack(_ephemeral_message("Something went wrong while preparing that onboarding request."))
        raise

    ack(_onboarding_preview_response(request))




@app_slack.command("/query")
def handle_query_command(command, ack, respond):
    _handle_query_command(command, ack, respond)


@app_slack.command("/report")
def handle_report_command(command, ack, respond):
    _handle_report_command(command, ack, respond)


@app_slack.command("/onboard")
def handle_onboard_command(command, ack, respond):
    _handle_onboard_command(command, ack, respond)


@app_slack.action("provisioning_approve")
def handle_provisioning_approve(ack, body, respond):
    ack()

    action = body.get("actions", [{}])[0]
    request_id = action.get("value", "")
    approver_id = body.get("user", {}).get("id", "")
    respond(_onboarding_working_response())
    result = approve_onboarding_request(request_id, approver_id)

    respond(_onboarding_result_response(result))


@app_slack.action("provisioning_reject")
def handle_provisioning_reject(ack, body, respond):
    ack()

    action = body.get("actions", [{}])[0]
    request_id = action.get("value", "")
    approver_id = body.get("user", {}).get("id", "")
    result = reject_onboarding_request(request_id, approver_id)

    respond(_onboarding_result_response(result))


@app_slack.event("app_mention")
def handle_message(event, client):
    query = event["text"].split(">", 1)[-1].strip()
    routed = route_app_mention(query)
    channel = event["channel"]

    msg = client.chat_postMessage(
        channel=channel,
        text="Searching documents...",
    )

    ts = msg["ts"]
    client.chat_update(
        channel=channel,
        ts=ts,
        text="Generating answer...",
    )

    response = answer_rag_question(routed.text)

    client.chat_update(
        channel=channel,
        ts=ts,
        text=response,
    )


@app_slack.event("message")
def handle_message_events():
    return
