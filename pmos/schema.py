"""Pydantic models for every PM OS source type. Python 3.9: use typing, not X | Y."""
import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from typing_extensions import Literal

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _check_iso_date(v: str) -> str:
    if not _ISO_DATE.match(v):
        raise ValueError("date must be YYYY-MM-DD")
    return v


class Turn(BaseModel):
    speaker: Literal["agent", "customer"]
    text: str


class Interview(BaseModel):
    """Voice-agent customer interview (voice of customer)."""
    id: str
    customer_name: str
    company: str
    date: str
    turns: List[Turn]

    _date = field_validator("date")(_check_iso_date)


class NPSRecord(BaseModel):
    """NPS survey comment or support-ticket snippet."""
    id: str
    account: str
    date: str
    channel: Literal["nps", "support", "community"]
    score: Optional[int] = Field(default=None, ge=0, le=10)
    text: str

    _date = field_validator("date")(_check_iso_date)


class CRMRecord(BaseModel):
    """Sales-team feedback captured on a CRM opportunity."""
    id: str
    account: str
    segment: Literal["enterprise", "mid-market", "smb"]
    arr_usd: int = Field(gt=0)
    stage: str
    rep: str
    date: str
    request: str
    notes: str
    competitor: Optional[str] = None

    _date = field_validator("date")(_check_iso_date)


class Sentence(BaseModel):
    speaker: str
    start_s: float = Field(ge=0)
    text: str


class FirefliesMeeting(BaseModel):
    """Fireflies.ai notetaker export: timestamped sentences + AI summary."""
    id: str
    title: str
    date: str
    account: str
    attendees: List[str]
    sentences: List[Sentence]
    summary: str
    action_items: List[str]

    _date = field_validator("date")(_check_iso_date)

    @field_validator("sentences")
    @classmethod
    def _in_order(cls, v: List[Sentence]) -> List[Sentence]:
        starts = [s.start_s for s in v]
        if starts != sorted(starts):
            raise ValueError("sentences must be in chronological order")
        return v


class Commitment(BaseModel):
    """Contract-backed deal-breaker promised to a client."""
    id: str
    account: str
    commitment: str
    due_date: str
    arr_at_risk_usd: int = Field(gt=0)
    contract_ref: str
    linked_theme: str

    _date = field_validator("due_date")(_check_iso_date)


class Squad(BaseModel):
    id: str
    name: str
    engineers: int
    capacity_pw_per_month: int = Field(gt=0)


class Quarter(BaseModel):
    label: str
    months: List[str]


class ReachConfig(BaseModel):
    arr_weight_min: float
    arr_weight_max: float


class CompanyConfig(BaseModel):
    name: str
    product: str
    quarter: Quarter
    squads: List[Squad]
    reach: ReachConfig


_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Evidence(BaseModel):
    source: Literal["voc", "support", "crm", "fireflies", "commitment"]
    record_id: str
    account: str
    quote: str = Field(min_length=1)


class Suggested(BaseModel):
    impact: float
    confidence: float
    effort_pw: float = Field(gt=0)
    rationale: str

    @field_validator("impact")
    @classmethod
    def _impact(cls, v: float) -> float:
        if v not in (0.25, 0.5, 1, 2, 3):
            raise ValueError("impact must be one of 0.25, 0.5, 1, 2, 3")
        return v

    @field_validator("confidence")
    @classmethod
    def _confidence(cls, v: float) -> float:
        if v not in (0.5, 0.8, 1.0):
            raise ValueError("confidence must be one of 0.5, 0.8, 1.0")
        return v


class BacklogItem(BaseModel):
    """One derived roadmap candidate. `id` must stay stable across re-derives so
    user overrides in the event log keep applying."""
    id: str
    title: str
    problem: str
    squad: str
    theme: str
    evidence: List[Evidence] = Field(min_length=1)
    suggested: Suggested
    depends_on: List[str] = []
    commitment_id: Optional[str] = None

    @field_validator("id")
    @classmethod
    def _slug(cls, v: str) -> str:
        if not _SLUG.match(v):
            raise ValueError("id must be a lowercase-hyphen slug")
        return v


class Backlog(BaseModel):
    company: str
    derived_at: str
    items: List[BacklogItem]
