import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator


class AircraftCreate(BaseModel):
    model: str = Field(..., min_length=2, max_length=100, examples=["Boeing 777-300ER"])
    registration_number: str = Field(..., min_length=2, max_length=50, examples=["PK-777"])
    total_capacity: int = Field(..., gt=0, examples=[100])
    first_seats: int = Field(..., ge=0, examples=[20])
    business_seats: int = Field(..., ge=0, examples=[30])
    economy_seats: int = Field(..., ge=0, examples=[50])

    @model_validator(mode="after")
    def validate_capacity_sum(self) -> "AircraftCreate":
        if self.first_seats + self.business_seats + self.economy_seats != self.total_capacity:
            raise ValueError(
                f"Sum of seats ({self.first_seats} First + {self.business_seats} Business + {self.economy_seats} Economy = "
                f"{self.first_seats + self.business_seats + self.economy_seats}) must equal total capacity ({self.total_capacity})"
            )
        return self


class AircraftResponse(BaseModel):
    id: uuid.UUID
    model: str
    registration_number: str
    total_capacity: int
    first_seats: int
    business_seats: int
    economy_seats: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
