from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class UnprocessedEmail:
    id: int
    message_id: str
    sender: str
    subject: str
    body: str
    timestamp: datetime

@dataclass
class LLMResponse:
    original_email_id: int
    response_subject: str
    response_body: str
    generated_at: datetime
    model_used: str
    sent_at: datetime