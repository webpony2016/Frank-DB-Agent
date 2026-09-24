from datetime import date
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, model_validator

Short = Annotated[str, Field(min_length=1, max_length=200)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class JobBriefInput(Input):
    customer_id: Short
    title: Short
    site: Short
    service: Short
    requested_start: date
    requested_end: date

    @model_validator(mode="after")
    def dates(self):
        if self.requested_end < self.requested_start:
            raise ValueError("The end date cannot be before the start date.")
        return self


class VersionInput(Input):
    expected_version: int = Field(ge=1, strict=True)

from decimal import Decimal


class QuoteLineInput(Input):
    description: str = Field(min_length=1, max_length=300)
    quantity: Decimal = Field(ge=0, le=100000, decimal_places=3, allow_inf_nan=False)
    unit_price: Decimal = Field(ge=0, le=1000000, decimal_places=2, allow_inf_nan=False)


class QuoteInput(VersionInput):
    lines: list[QuoteLineInput] = Field(min_length=1, max_length=30)

