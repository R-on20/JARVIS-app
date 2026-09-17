import base64
import os
from email.mime.text import MIMEText
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.settings import (
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_TOKEN_FILE,
    GMAIL_SCOPES,
)
from models.email_models import (
    EmailDraft,
    EmailMessage,
    EmailSearchResult,
)


class GmailService:

    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        credentials: Optional[Credentials] = None

        if os.path.exists(GOOGLE_TOKEN_FILE):
            credentials = Credentials.from_authorized_user_file(
                GOOGLE_TOKEN_FILE,
                GMAIL_SCOPES,
            )

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        if not credentials or not credentials.valid:
            if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Google credentials not found at "
                    f"{GOOGLE_CREDENTIALS_FILE}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_FILE,
                GMAIL_SCOPES,
            )

            credentials = flow.run_local_server(
                port=0
            )

            os.makedirs(
                os.path.dirname(GOOGLE_TOKEN_FILE),
                exist_ok=True,
            )

            with open(GOOGLE_TOKEN_FILE, "w") as token:
                token.write(credentials.to_json())

        return build(
            "gmail",
            "v1",
            credentials=credentials,
        )

    # ---------------------------------------------------------
    # LIST EMAILS
    # ---------------------------------------------------------

    def list_emails(
        self,
        max_results: int = 10,
        query: Optional[str] = None,
    ) -> EmailSearchResult:

        response = (
            self.service.users()
            .messages()
            .list(
                userId="me",
                maxResults=max_results,
                q=query,
            )
            .execute()
        )

        messages = response.get("messages", [])

        emails = []

        for message in messages:
            email = self.get_email(message["id"])

            if email:
                emails.append(email)

        return EmailSearchResult(
            emails=emails,
            total=len(emails),
        )

    # ---------------------------------------------------------
    # GET EMAIL
    # ---------------------------------------------------------

    def get_email(self, message_id: str) -> Optional[EmailMessage]:

        response = (
            self.service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",
            )
            .execute()
        )

        payload = response.get("payload", {})
        headers = payload.get("headers", [])

        header_map = {
            header["name"].lower(): header["value"]
            for header in headers
        }

        body = self._extract_body(payload)

        labels = response.get("labelIds", [])

        return EmailMessage(
            id=response["id"],
            thread_id=response.get("threadId"),
            sender=header_map.get("from", ""),
            recipient=header_map.get("to"),
            subject=header_map.get(
                "subject",
                "(No subject)",
            ),
            date=header_map.get("date"),
            snippet=response.get("snippet"),
            body=body,
            unread="UNREAD" in labels,
        )

    # ---------------------------------------------------------
    # EXTRACT EMAIL BODY
    # ---------------------------------------------------------

    def _extract_body(self, payload) -> str:

        body_data = payload.get("body", {}).get("data")

        if body_data:
            return self._decode_body(body_data)

        parts = payload.get("parts", [])

        for part in parts:

            mime_type = part.get("mimeType", "")

            if mime_type == "text/plain":

                data = part.get("body", {}).get("data")

                if data:
                    return self._decode_body(data)

            if mime_type.startswith("multipart/"):

                nested_body = self._extract_body(part)

                if nested_body:
                    return nested_body

        return ""

    # ---------------------------------------------------------
    # DECODE EMAIL
    # ---------------------------------------------------------

    @staticmethod
    def _decode_body(data: str) -> str:

        decoded = base64.urlsafe_b64decode(
            data.encode("UTF-8")
        )

        return decoded.decode(
            "UTF-8",
            errors="replace",
        )

    # ---------------------------------------------------------
    # SEARCH EMAIL
    # ---------------------------------------------------------

    def search_emails(
        self,
        query: str,
        max_results: int = 10,
    ) -> EmailSearchResult:

        return self.list_emails(
            max_results=max_results,
            query=query,
        )

    # ---------------------------------------------------------
    # MARK AS READ
    # ---------------------------------------------------------

    def mark_as_read(self, message_id: str):

        body = {
            "removeLabelIds": ["UNREAD"]
        }

        return (
            self.service.users()
            .messages()
            .modify(
                userId="me",
                id=message_id,
                body=body,
            )
            .execute()
        )

    # ---------------------------------------------------------
    # SEND EMAIL
    # ---------------------------------------------------------

    def send_email(
        self,
        draft: EmailDraft,
    ):

        message = MIMEText(
            draft.body,
            "plain",
            "utf-8",
        )

        message["to"] = draft.recipient
        message["subject"] = draft.subject

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        send_body = {
            "raw": encoded_message
        }

        return (
            self.service.users()
            .messages()
            .send(
                userId="me",
                body=send_body,
            )
            .execute()
        )