import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import os
from pymongo.errors import ConnectionFailure, OperationFailure

async def insert_bangladesh_data():
    # MongoDB connection with authentication
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://root:example@localhost:27017/travel_booking?authSource=admin")
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        # Test connection
        await client.admin.command('ping')
    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {str(e)}")
        print("Ensure MongoDB is running and credentials are correct.")
        return
    except OperationFailure as e:
        print(f"Authentication error: {str(e)}")
        print("Verify username and password in MONGODB_URL or Docker Compose configuration.")
        return

    db = client["travel_booking"]

    # Sample Flights Data (Bangladesh context)
    flights = [
        {
            "flight_number": "BB101",
            "airline": "Biman Bangladesh Airlines",
            "departure_airport": "DAC",
            "arrival_airport": "CGP",
            "departure_time": datetime(2025, 8, 1, 9, 0),
            "arrival_time": datetime(2025, 8, 1, 10, 0),
            "price": 6500.00,  # BDT
            "seats_available": 100,
            "cabin_class": "Economy",
            "status": "scheduled"
        },
        {
            "flight_number": "US202",
            "airline": "US-Bangla Airlines",
            "departure_airport": "DAC",
            "arrival_airport": "SPD",
            "departure_time": datetime(2025, 8, 2, 11, 30),
            "arrival_time": datetime(2025, 8, 2, 12, 30),
            "price": 5500.00,  # BDT
            "seats_available": 80,
            "cabin_class": "Economy",
            "status": "scheduled"
        },
        {
            "flight_number": "BB303",
            "airline": "Biman Bangladesh Airlines",
            "departure_airport": "CGP",
            "arrival_airport": "RJH",
            "departure_time": datetime(2025, 8, 3, 14, 0),
            "arrival_time": datetime(2025, 8, 3, 15, 30),
            "price": 7000.00,  # BDT
            "seats_available": 90,
            "cabin_class": "Economy",
            "status": "scheduled"
        }
    ]

    # Sample Hotels Data (Bangladesh context)
    hotels = [
        {
            "name": "Pan Pacific Sonargaon Dhaka",
            "address": {
                "street": "107 Kazi Nazrul Islam Avenue",
                "city": "Dhaka",
                "country": "Bangladesh",
                "postal_code": "1215"
            },
            "star_rating": 5,
            "room_type": "Deluxe Room",
            "price_per_night": 15000.00,  # BDT
            "available_rooms": 40,
            "check_in_date": datetime(2025, 8, 1),
            "check_out_date": datetime(2025, 8, 5),
            "amenities": ["wifi", "pool", "gym", "restaurant"]
        },
        {
            "name": "Hotel Agrabad Chattogram",
            "address": {
                "street": "1672 Sabder Ali Road, Agrabad C/A",
                "city": "Chattogram",
                "country": "Bangladesh",
                "postal_code": "4100"
            },
            "star_rating": 4,
            "room_type": "Executive Suite",
            "price_per_night": 12000.00,  # BDT
            "available_rooms": 30,
            "check_in_date": datetime(2025, 8, 2),
            "check_out_date": datetime(2025, 8, 6),
            "amenities": ["wifi", "restaurant", "business_center"]
        },
        {
            "name": "Grand Palace Hotel Saidpur",
            "address": {
                "street": "Airport Road",
                "city": "Saidpur",
                "country": "Bangladesh",
                "postal_code": "5310"
            },
            "star_rating": 3,
            "room_type": "Standard Room",
            "price_per_night": 8000.00,  # BDT
            "available_rooms": 20,
            "check_in_date": datetime(2025, 8, 3),
            "check_out_date": datetime(2025, 8, 7),
            "amenities": ["wifi", "parking", "restaurant"]
        },
        {
            "name": "Royal Park Rajshahi",
            "address": {
                "street": "Shiroil, Boalia",
                "city": "Rajshahi",
                "country": "Bangladesh",
                "postal_code": "6100"
            },
            "star_rating": 4,
            "room_type": "Superior Room",
            "price_per_night": 10000.00,  # BDT
            "available_rooms": 25,
            "check_in_date": datetime(2025, 8, 3),
            "check_out_date": datetime(2025, 8, 7),
            "amenities": ["wifi", "gym", "restaurant"]
        }
    ]

    # Sample Bookings Data (Bangladesh context)
    flight_bookings = [
        {
            "user_id": "user001",
            "flight_id": None,  # Will be updated after flight insertion
            "passenger_name": "Md. Rahim Khan",
            "passenger_email": "rahim.khan@example.com",
            "seat_number": "15A",
            "total_price": 6500.00,  # BDT
            "booking_date": datetime.utcnow(),
            "status": "confirmed"
        },
        {
            "user_id": "user002",
            "flight_id": None,  # Will be updated after flight insertion
            "passenger_name": "Fatima Begum",
            "passenger_email": "fatima.begum@example.com",
            "seat_number": "9B",
            "total_price": 5500.00,  # BDT
            "booking_date": datetime.utcnow(),
            "status": "confirmed"
        }
    ]

    hotel_bookings = [
        {
            "user_id": "user001",
            "hotel_id": None,  # Will be updated after hotel insertion
            "guest_name": "Md. Rahim Khan",
            "guest_email": "rahim.khan@example.com",
            "room_number": "301",
            "total_price": 60000.00,  # 4 nights * 15000.00 BDT
            "booking_date": datetime.utcnow(),
            "status": "confirmed"
        },
        {
            "user_id": "user003",
            "hotel_id": None,  # Will be updated after hotel insertion
            "guest_name": "Ayesha Siddiqua",
            "guest_email": "ayesha.siddiqua@example.com",
            "room_number": "205",
            "total_price": 32000.00,  # 4 nights * 8000.00 BDT
            "booking_date": datetime.utcnow(),
            "status": "confirmed"
        }
    ]

    try:
        # Clear existing collections
        await db.flights.delete_many({})
        await db.hotels.delete_many({})
        await db.flight_bookings.delete_many({})
        await db.hotel_bookings.delete_many({})

        # Insert flights
        flight_results = await db.flights.insert_many(flights)
        flight_ids = flight_results.inserted_ids

        # Update flight_bookings with flight IDs
        flight_bookings[0]["flight_id"] = str(flight_ids[0])
        flight_bookings[1]["flight_id"] = str(flight_ids[1])

        # Insert hotels
        hotel_results = await db.hotels.insert_many(hotels)
        hotel_ids = hotel_results.inserted_ids

        # Update hotel_bookings with hotel IDs
        hotel_bookings[0]["hotel_id"] = str(hotel_ids[0])
        hotel_bookings[1]["hotel_id"] = str(hotel_ids[2])

        # Insert bookings
        await db.flight_bookings.insert_many(flight_bookings)
        await db.hotel_bookings.insert_many(hotel_bookings)

        print("Bangladesh sample data inserted successfully!")
        print(f"Inserted {len(flight_ids)} flights")
        print(f"Inserted {len(hotel_ids)} hotels")
        print(f"Inserted {len(flight_bookings)} flight bookings")
        print(f"Inserted {len(hotel_bookings)} hotel bookings")

    except OperationFailure as e:
        print(f"Operation failed: {str(e)}")
        print("Check MongoDB credentials or database permissions.")
    except Exception as e:
        print(f"Error inserting data: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(insert_bangladesh_data())