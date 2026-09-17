from models.email_models import EmailMessage


def format_email_list(emails: list[EmailMessage]) -> str:

    if not emails:
        return "You don't have any emails matching that request."

    lines = []

    for index, email in enumerate(emails, start=1):

        unread = "Unread" if email.unread else "Read"

        lines.append(
            f"{index}. {email.sender}. "
            f"{email.subject}. "
            f"{unread}."
        )

    return "\n".join(lines)


def format_email(email: EmailMessage) -> str:

    return (
        f"From: {email.sender}\n"
        f"Subject: {email.subject}\n"
        f"Date: {email.date or 'Unknown'}\n\n"
        f"{email.body or email.snippet or 'This email has no readable content.'}"
    )