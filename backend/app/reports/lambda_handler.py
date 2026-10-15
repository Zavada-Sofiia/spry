import json
import logging
import os

from app.reports.weekly import build_weekly_report, previous_iso_week, report_key

log = logging.getLogger()
log.setLevel(logging.INFO)

BUCKET = os.environ.get("REPORTS_BUCKET", "")
_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        import boto3

        _s3_client = boto3.client("s3")
    return _s3_client


def _payload(event: dict) -> dict:
    """Accept both a direct invocation and an SQS event."""
    if isinstance(event, dict) and "Records" in event and len(event["Records"]) > 0:
        first_rec = event["Records"][0]
        if first_rec.get("eventSource") == "aws:sqs":
            return json.loads(first_rec["body"])
    return event if isinstance(event, dict) else {}


def detect_trigger(event: dict) -> str:
    p = _payload(event)
    if p.get("source") == "schedule":
        return "schedule"  # fired by EventBridge Scheduler (direct or via SQS)
    if isinstance(event, dict) and "Records" in event and len(event["Records"]) > 0:
        if event["Records"][0].get("eventSource") == "aws:sqs":
            return "sqs"  # manual / API message
    return "direct"


def handler(event, context):
    payload = _payload(event)
    week = payload.get("week") or previous_iso_week()
    transport = "sqs" if isinstance(event, dict) and "Records" in event else "direct"
    trigger = detect_trigger(event)

    log.info(
        "report-builder triggered",
        extra={"trigger": trigger, "transport": transport, "week": week},
    )
    # Also print in plain key=value so it is greppable in CloudWatch:
    print(f"report-builder triggered trigger={trigger} transport={transport} week={week}")

    bucket_name = os.environ.get("REPORTS_BUCKET", BUCKET)
    body = build_weekly_report(week)
    key = report_key(week)
    get_s3_client().put_object(Bucket=bucket_name, Key=key, Body=body, ContentType="text/csv")
    print(f"report-builder wrote s3://{bucket_name}/{key} bytes={len(body)}")
    return {"week": week, "key": key}
