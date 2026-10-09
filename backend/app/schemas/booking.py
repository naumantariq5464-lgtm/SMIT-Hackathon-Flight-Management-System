import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.booking import BookingStatus
from app.models.booking_passenger import PassengerStatus
from app.models.seat import SeatClass


class PassengerCreate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100, examples=["Alice"])
    last_name: str = Field(..., min_length=2, max_length=100, examples=["Smith"])
    passport_number: Optional[str] = Field(None, max_length=50, examples=["A12345678"])
    seat_class: SeatClass = SeatClass.ECONOMY
    seat_id: Optional[uuid.UUID] = None  # Optional specific seat selection


class BookingFlightRequest(BaseModel):
    flight_id: uuid.UUID
    fare_rule_id: uuid.UUID


class BookingCreate(BaseModel):
    flights: List[BookingFlightRequest] = Field(..., min_length=1, description="List of flights for the itinerary (multi-leg or single)")
    passengers: List[PassengerCreate] = Field(..., min_length=1, max_length=9)
    price_hold_id: Optional[uuid.UUID] = None
    group_failure_policy: str = Field(
        default="FULL_FAILURE",
        description="Behavior if not all requested seats are available: FULL_FAILURE or PARTIAL_ALLOWED",
    )


class BookingPassengerResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    seat_id: Optional[uuid.UUID]
    seat_number: Optional[str]
    seat_class: SeatClass
    first_name: str
    last_name: str
    passport_number: Optional[str]
    ticket_price: Decimal
    status: PassengerStatus

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    id: uuid.UUID
    booking_reference: str
    user_id: uuid.UUID
    flight_id: uuid.UUID
    fare_rule_id: uuid.UUID
    total_price: Decimal
    currency: str
    status: BookingStatus
    passengers: List[BookingPassengerResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
