import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.flight import FlightStatus, OverbookingPolicy
from app.models.seat import SeatClass


class FlightCreate(BaseModel):
    flight_number: str = Field(..., min_length=2, max_length=20, examples=["EK-201"])
    origin: str = Field(..., min_length=2, max_length=50, examples=["UK"])
    destination: str = Field(..., min_length=2, max_length=50, examples=["Dubai"])
    departure_datetime: datetime = Field(..., examples=["2026-10-15T10:00:00Z"])
    arrival_datetime: datetime = Field(..., examples=["2026-10-15T18:00:00Z"])
    capacity: int = Field(..., gt=0, examples=[100])
    first_seats: int = Field(..., ge=0, examples=[20])
    business_seats: int = Field(..., ge=0, examples=[30])
    economy_seats: int = Field(..., ge=0, examples=[50])
    base_price: Decimal = Field(..., gt=0, examples=[250.00])
    currency: str = Field(default="USD", min_length=3, max_length=3, examples=["USD"])
    aircraft_id: Optional[uuid.UUID] = None
    overbooking_policy: OverbookingPolicy = OverbookingPolicy.HARD_LIMIT
    overbooking_buffer_percent: int = Field(default=0, ge=0, le=20)
    first_cutoff_hours: int = Field(default=2, ge=0)
    business_cutoff_hours: int = Field(default=4, ge=0)
    economy_cutoff_hours: int = Field(default=6, ge=0)

    @model_validator(mode="after")
    def validate_flight_fields(self) -> "FlightCreate":
        if self.arrival_datetime <= self.departure_datetime:
            raise ValueError("arrival_datetime must be strictly after departure_datetime")
        
        seat_sum = self.first_seats + self.business_seats + self.economy_seats
        if seat_sum != self.capacity:
            raise ValueError(
                f"Sum of class seats ({self.first_seats} First + {self.business_seats} Business + {self.economy_seats} Economy = "
                f"{seat_sum}) MUST equal aircraft capacity ({self.capacity})"
            )
        return self


class FlightUpdate(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_datetime: Optional[datetime] = None
    arrival_datetime: Optional[datetime] = None
    base_price: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[FlightStatus] = None
    first_cutoff_hours: Optional[int] = None
    business_cutoff_hours: Optional[int] = None
    economy_cutoff_hours: Optional[int] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "FlightUpdate":
        if self.departure_datetime and self.arrival_datetime:
            if self.arrival_datetime <= self.departure_datetime:
                raise ValueError("arrival_datetime must be strictly after departure_datetime")
        return self


class FlightResponse(BaseModel):
    id: uuid.UUID
    flight_number: str
    origin: str
    destination: str
    departure_datetime: datetime
    arrival_datetime: datetime
    aircraft_id: Optional[uuid.UUID]
    status: FlightStatus
    capacity: int
    first_seats: int
    business_seats: int
    economy_seats: int
    booked_first: int
    booked_business: int
    booked_economy: int
    available_first: int
    available_business: int
    available_economy: int
    base_price: Decimal
    currency: str
    overbooking_policy: OverbookingPolicy
    first_cutoff_hours: int
    business_cutoff_hours: int
    economy_cutoff_hours: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FlightFareOption(BaseModel):
    fare_rule_id: uuid.UUID
    fare_name: str
    fare_type: str
    seat_class: SeatClass
    price: Decimal
    currency: str
    is_refundable: bool
    seat_selection_allowed: bool
    change_allowed: bool
    baggage_allowance_kg: int


class FlightSearchResult(BaseModel):
    flight_id: uuid.UUID
    flight_number: str
    origin: str
    destination: str
    departure_datetime: datetime
    arrival_datetime: datetime
    duration_minutes: int
    status: FlightStatus
    available_first: int
    available_business: int
    available_economy: int
    fare_options: List[FlightFareOption]

class FlightItineraryResult(BaseModel):
    flights: List[FlightSearchResult]
    total_duration_minutes: int
    total_price_base: Decimal


class FlightCancelRequest(BaseModel):
    reason: str = Field(default="Operational cancellation", min_length=3, max_length=255)
    default_resolution: str = Field(default="REFUND", examples=["REFUND", "TRAVEL_CREDIT", "REBOOK"])
