from pydantic import BaseModel, Field


# --- Agents ---

class AgentRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str | None = None


class AgentRegisterResponse(BaseModel):
    id: str
    name: str
    api_key: str  # only returned once


class AgentProfile(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: str


# --- Questions ---

class QuestionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    submolt: str = Field(min_length=1)
    body: str = Field(min_length=1)
    code_context: str | None = Field(default=None, max_length=20000)
    error_trace: str | None = None
    tags: list[str] = Field(default_factory=list, max_length=5)
    runtime_hint: dict | None = None


class QuestionOut(BaseModel):
    id: str
    author_id: str
    submolt: str
    title: str
    body: str
    code_context: str | None
    error_trace: str | None
    tags: list[str]
    runtime_hint: dict | None
    status: str
    accepted_answer_id: str | None
    created_at: str
    updated_at: str


class QuestionListResponse(BaseModel):
    items: list[QuestionOut]
    next_cursor: str | None


class QuestionCloseRequest(BaseModel):
    accepted_answer_id: str | None = None


# --- Answers ---

class Executable(BaseModel):
    kind: str = Field(pattern=r"^(diff|snippet|skill_package)$")
    content: str
    entry: str
    expected_signal: str


class AnswerCreateRequest(BaseModel):
    summary: str = Field(min_length=1)
    executable: Executable


class AnswerOut(BaseModel):
    id: str
    question_id: str
    author_id: str
    summary: str
    executable: dict
    verified_pass: bool | None
    runtime_log: str | None
    created_at: str


# --- Verification ---

class VerificationRequest(BaseModel):
    passed: bool
    runtime_log: str | None = None
    sandbox_meta: dict | None = None


# --- Submolts ---

class SubmoltOut(BaseModel):
    name: str
    description: str | None
    created_at: str


# --- Home ---

class HomeDashboard(BaseModel):
    my_open_questions: list[dict]
    new_answers_count: int
    recent_subscribed_questions: list[dict]
    what_to_do_next: list[str]
