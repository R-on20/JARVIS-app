import re

from core.intents import Intent


class IntentRouter:

    def classify(self, text: str) -> Intent:

        text = text.lower().strip()

        # -------------------------------------------------
        # CHECK EMAIL
        # -------------------------------------------------

        if any(
            phrase in text
            for phrase in [
                "check my email",
                "check my emails",
                "check my inbox",
                "show my emails",
                "show my inbox",
                "any new emails",
                "any new mail",
                "do i have any emails",
                "do i have new emails",
            ]
        ):
            return Intent.CHECK_EMAIL

        # -------------------------------------------------
        # READ EMAIL
        # -------------------------------------------------

        if any(
            phrase in text
            for phrase in [
                "read the email",
                "read my email",
                "read the latest email",
                "read that email",
                "open the email",
            ]
        ):
            return Intent.READ_EMAIL

        # -------------------------------------------------
        # SEARCH EMAIL
        # -------------------------------------------------

        if any(
            phrase in text
            for phrase in [
                "find an email",
                "find the email",
                "search my email",
                "search my emails",
                "look for an email",
                "look through my emails",
            ]
        ):
            return Intent.SEARCH_EMAIL

        # -------------------------------------------------
        # DRAFT EMAIL
        # -------------------------------------------------

        if any(
            phrase in text
            for phrase in [
                "draft an email",
                "draft a mail",
                "write an email",
                "write a mail",
                "compose an email",
                "compose a mail",
            ]
        ):
            return Intent.DRAFT_EMAIL

        # -------------------------------------------------
        # SEND EMAIL
        # -------------------------------------------------

        if any(
            phrase in text
            for phrase in [
                "send the email",
                "send that email",
                "send it",
                "send the mail",
            ]
        ):
            return Intent.SEND_EMAIL

        return Intent.UNKNOWN