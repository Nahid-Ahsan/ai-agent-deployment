from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from enum import Enum

class FlightStatus(str, Enum):
    scheduled = "scheduled"
    delayed = "delayed"
    cancelled = "cancelled"

class BookingStatus(str, Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"

class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class FlightBase(BaseModel):
    flight_number: str
    airline: str
    departure_airport: str
    arrival_airport: str
    departure_time: datetime
    arrival_time: datetime
    price: float
    seats_available: int
    cabin_class: str
    status: FlightStatus = FlightStatus.scheduled

class FlightCreate(FlightBase):
    pass

class Flight(FlightBase):
    id: str

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class HotelBase(BaseModel):
    name: str
    address: Address
    star_rating: int
    room_type: str
    price_per_night: float
    available_rooms: int
    check_in_date: datetime
    check_out_date: datetime
    amenities: List[str]

class HotelCreate(HotelBase):
    pass

class Hotel(HotelBase):
    id: str

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class BookingBase(BaseModel):
    user_id: str
    total_price: float
    booking_date: datetime = datetime.utcnow()
    status: BookingStatus = BookingStatus.confirmed

class FlightBookingCreate(BookingBase):
    flight_id: str
    passenger_name: str
    passenger_email: EmailStr
    seat_number: Optional[str] = None

class HotelBookingCreate(BookingBase):
    hotel_id: str
    guest_name: str
    guest_email: EmailStr
    room_number: Optional[str] = None

class FlightBooking(BookingBase):
    id: str
    flight_id: str
    passenger_name: str
    passenger_email: EmailStr
    seat_number: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class HotelBooking(BookingBase):
    id: str
    hotel_id: str
    guest_name: str
    guest_email: EmailStr
    room_number: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

