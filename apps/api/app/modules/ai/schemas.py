"""Schemas for AI conversations and messages."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(default=None, max_length=160)


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    content: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    conversation_id: uuid.UUID
    proposal_id: uuid.UUID | None
    role: Literal["user", "assistant", "system_metadata"]
    content: str
    validation_status: str
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    event_id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = Field(default_factory=list)

