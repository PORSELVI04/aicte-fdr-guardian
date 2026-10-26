from pydantic import BaseModel, ConfigDict, Field


class InstitutionCreate(BaseModel):
    institution_code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=255)
    address: str = Field(min_length=3, max_length=500)
    contact_email: str = Field(min_length=5, max_length=255)


class InstitutionResponse(InstitutionCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)