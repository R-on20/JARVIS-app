from enum import Enum


class Intent(str, Enum):

    CHECK_EMAIL = "check_email"

    READ_EMAIL = "read_email"

    SEARCH_EMAIL = "search_email"

    DRAFT_EMAIL = "draft_email"

    SEND_EMAIL = "send_email"

    UNKNOWN = "unknown"