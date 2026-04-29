from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

from app.agents.router import RAG_AGENT, REPORT_AGENT, route_app_mention, route_slash_command
from app.config.settings import settings
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


@app_slack.event("message")
def handle_message_events():
    return
