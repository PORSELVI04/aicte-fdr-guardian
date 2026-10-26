from datetime import date
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class FDRCreate(BaseModel):
    fdr_number: str = Field(min_length=2, max_length=100)
    institution_id: int = Field(gt=0)
    bank_name: str = Field(min_length=2, max_length=255)
    branch_name: str = Field(min_length=2, max_length=255)
    deposit_amount: Decimal = Field(
        gt=0,
        max_digits=15,
        decimal_places=2,
    )
    issue_date: date
    maturity_date: date

    @field_validator("fdr_number")
    @classmethod
    def validate_fdr_number(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("FDR number cannot be empty or whitespace")

        if len(value) < 2:
            raise ValueError("FDR number must contain at least 2 characters")

        return value

    @model_validator(mode="after")
    def validate_dates(self):
        if self.maturity_date <= self.issue_date:
            raise ValueError("Maturity date must be after issue date")
        return self


class FDRResponse(FDRCreate):
    id: int
    validity_status: str
    administrative_status: str

    model_config = ConfigDict(from_attributes=True)