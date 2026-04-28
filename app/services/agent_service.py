from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

from app.agents.router import RAG_AGENT, REPORT_AGENT, route_app_mention, route_slash_command
from app.config.settings import settings
from app.services.rag_service import answer_rag_question


app_slack = App(
    token=settings.SLACK_BOT_TOKEN,
    signing_secret=settings.SLACK_SIGNING_SECRET,
    token_verification_enabled=False,
)

handler = SlackRequestHandler(app_slack)


def _handle_query_command(command, ack, respond):
    routed = route_slash_command(command.get("command", ""), command.get("text", ""))

    ack({
        "response_type": "ephemeral",
        "text": "Searching documents...",
    })

    if routed.agent != RAG_AGENT:
        respond({
            "response_type": "ephemeral",
            "replace_original": True,
            "text": "I do not know how to handle that command yet.",
        })
        return

    if not routed.text:
        respond({
            "response_type": "ephemeral",
            "replace_original": True,
            "text": "Please add a question after `/query`.",
        })
        return

    try:
        respond({
            "response_type": "ephemeral",
            "replace_original": True,
            "text": "Generating answer...",
        })

        response = answer_rag_question(routed.text)

        respond({
            "response_type": "ephemeral",
            "replace_original": True,
            "text": response,
        })
    except Exception:
        respond({
            "response_type": "ephemeral",
            "replace_original": True,
            "text": "Something went wrong while answering that question. Please try again.",
        })
        raise


def _handle_report_command(command, ack, respond):
    routed = route_slash_command(command.get("command", ""), command.get("text", ""))

    ack({
        "response_type": "ephemeral",
        "text": "Preparing report...",
    })

    if routed.agent != REPORT_AGENT:
        respond({
            "response_type": "ephemeral",
            "replace_original": True,
            "text": "I do not know how to handle that command yet.",
        })
        return

    respond({
        "response_type": "ephemeral",
        "replace_original": True,
        "text": "Report command received. The report agent is not implemented yet.",
    })


@app_slack.command("/query")
def handle_query_command(command, ack, respond):
    _handle_query_command(command, ack, respond)


@app_slack.command("/report")
def handle_report_command(command, ack, respond):
    _handle_report_command(command, ack, respond)


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
