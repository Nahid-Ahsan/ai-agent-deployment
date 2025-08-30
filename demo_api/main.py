from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime
import os
import uvicorn

app = FastAPI(title="Flight and Hotel Booking API")

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://root:example@localhost:27017/travel_booking?authSource=admin")
client = AsyncIOMotorClient(MONGODB_URL)
db = client["travel_booking"]

# Pydantic Schemas
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
    cabin_class: str  # Economy, Business, First
    status: str = "scheduled"  # scheduled, delayed, cancelled

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
    room_type: str  # Single, Double, Suite, etc.
    price_per_night: float
    available_rooms: int
    check_in_date: datetime
    check_out_date: datetime
    amenities: List[str]  # e.g., ["wifi", "pool", "gym"]

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
    booking_date: datetime
    status: str = "confirmed"  # confirmed, pending, cancelled

class FlightBookingCreate(BookingBase):
    flight_id: str
    passenger_name: str
    passenger_email: str
    seat_number: Optional[str] = None

class HotelBookingCreate(BookingBase):
    hotel_id: str
    guest_name: str
    guest_email: str
    room_number: Optional[str] = None

class FlightBooking(BookingBase):
    id: str
    flight_id: str
    passenger_name: str
    passenger_email: str
    seat_number: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class HotelBooking(BookingBase):
    id: str
    hotel_id: str
    guest_name: str
    guest_email: str
    room_number: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Dependency for getting DB
async def get_database():
    return db

# Flight CRUD APIs
@app.post("/flights/", response_model=Flight)
async def create_flight(flight: FlightCreate, db=Depends(get_database)):
    flight_dict = flight.dict()
    result = await db.flights.insert_one(flight_dict)
    return {**flight_dict, "id": str(result.inserted_id)}

@app.get("/flights/", response_model=List[Flight])
async def get_flights(db=Depends(get_database)):
    flights = await db.flights.find().to_list(100)
    return [{**flight, "id": str(flight["_id"])} for flight in flights]

@app.get("/flights/{flight_id}", response_model=Flight)
async def get_flight(flight_id: str, db=Depends(get_database)):
    flight = await db.flights.find_one({"_id": ObjectId(flight_id)})
    if flight is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    return {**flight, "id": str(flight["_id"])}

@app.put("/flights/{flight_id}", response_model=Flight)
async def update_flight(flight_id: str, flight: FlightCreate, db=Depends(get_database)):
    result = await db.flights.update_one(
        {"_id": ObjectId(flight_id)},
        {"$set": flight.dict()}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Flight not found")
    return {**flight.dict(), "id": flight_id}

@app.delete("/flights/{flight_id}")
async def delete_flight(flight_id: str, db=Depends(get_database)):
    result = await db.flights.delete_one({"_id": ObjectId(flight_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Flight not found")
    return {"message": "Flight deleted successfully"}

# Hotel CRUD APIs
@app.post("/hotels/", response_model=Hotel)
async def create_hotel(hotel: HotelCreate, db=Depends(get_database)):
    hotel_dict = hotel.dict()
    result = await db.hotels.insert_one(hotel_dict)
    return {**hotel_dict, "id": str(result.inserted_id)}

@app.get("/hotels/", response_model=List[Hotel])
async def get_hotels(db=Depends(get_database)):
    hotels = await db.hotels.find().to_list(100)
    return [{**hotel, "id": str(hotel["_id"])} for hotel in hotels]

@app.get("/hotels/{hotel_id}", response_model=Hotel)
async def get_hotel(hotel_id: str, db=Depends(get_database)):
    hotel = await db.hotels.find_one({"_id": ObjectId(hotel_id)})
    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return {**hotel, "id": str(hotel["_id"])}

@app.put("/hotels/{hotel_id}", response_model=Hotel)
async def update_hotel(hotel_id: str, hotel: HotelCreate, db=Depends(get_database)):
    result = await db.hotels.update_one(
        {"_id": ObjectId(hotel_id)},
        {"$set": hotel.dict()}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return {**hotel.dict(), "id": hotel_id}

@app.delete("/hotels/{hotel_id}")
async def delete_hotel(hotel_id: str, db=Depends(get_database)):
    result = await db.hotels.delete_one({"_id": ObjectId(hotel_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return {"message": "Hotel deleted successfully"}

# Booking APIs
@app.post("/bookings/flight/", response_model=FlightBooking)
async def create_flight_booking(booking: FlightBookingCreate, db=Depends(get_database)):
    flight = await db.flights.find_one({"_id": ObjectId(booking.flight_id)})
    if not flight or flight["seats_available"] <= 0:
        raise HTTPException(status_code=400, detail="Flight not available")
    
    booking_dict = booking.dict()
    booking_dict["booking_date"] = datetime.utcnow()
    result = await db.flight_bookings.insert_one(booking_dict)
    
    # Update flight seats
    await db.flights.update_one(
        {"_id": ObjectId(booking.flight_id)},
        {"$inc": {"seats_available": -1}}
    )
    
    return {**booking_dict, "id": str(result.inserted_id)}

@app.post("/bookings/hotel/", response_model=HotelBooking)
async def create_hotel_booking(booking: HotelBookingCreate, db=Depends(get_database)):
    hotel = await db.hotels.find_one({"_id": ObjectId(booking.hotel_id)})
    if not hotel or hotel["available_rooms"] <= 0:
        raise HTTPException(status_code=400, detail="Hotel room not available")
    
    booking_dict = booking.dict()
    booking_dict["booking_date"] = datetime.utcnow()
    result = await db.hotel_bookings.insert_one(booking_dict)
    
    # Update hotel rooms
    await db.hotels.update_one(
        {"_id": ObjectId(booking.hotel_id)},
        {"$inc": {"available_rooms": -1}}
    )
    
    return {**booking_dict, "id": str(result.inserted_id)}

@app.get("/bookings/flight/{booking_id}", response_model=FlightBooking)
async def get_flight_booking(booking_id: str, db=Depends(get_database)):
    booking = await db.flight_bookings.find_one({"_id": ObjectId(booking_id)})
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {**booking, "id": str(booking["_id"])}

@app.get("/bookings/hotel/{booking_id}", response_model=HotelBooking)
async def get_hotel_booking(booking_id: str, db=Depends(get_database)):
    booking = await db.hotel_bookings.find_one({"_id": ObjectId(booking_id)})
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {**booking, "id": str(booking["_id"])}

@app.delete("/bookings/flight/{booking_id}")
async def cancel_flight_booking(booking_id: str, db=Depends(get_database)):
    booking = await db.flight_bookings.find_one({"_id": ObjectId(booking_id)})
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    result = await db.flight_bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {"status": "cancelled"}}
    )
    
    # Return seat to flight
    await db.flights.update_one(
        {"_id": ObjectId(booking["flight_id"])},
        {"$inc": {"seats_available": 1}}
    )
    
    return {"message": "Flight booking cancelled successfully"}

@app.delete("/bookings/hotel/{booking_id}")
async def cancel_hotel_booking(booking_id: str, db=Depends(get_database)):
    booking = await db.hotel_bookings.find_one({"_id": ObjectId(booking_id)})
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    result = await db.hotel_bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {"status": "cancelled"}}
    )
    
    # Return room to hotel
    await db.hotels.update_one(
        {"_id": ObjectId(booking["hotel_id"])},
        {"$inc": {"available_rooms": 1}}
    )
    
    return {"message": "Hotel booking cancelled successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)