from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from chromadb.utils import embedding_functions
from model.state import AgentState
from service.db_service import get_database
from datetime import datetime
import os
from langgraph.checkpoint.memory import MemorySaver
import uuid
from schema.schemas import ChatResponse
from fastapi import Depends, HTTPException

CHROMA_PERSIST_DIR = "./chroma_db"
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_KEY=""
vectorstore = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embedding_functions.DefaultEmbeddingFunction())


class TravelAgent:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.llm = ChatGroq(model="llama3-70b-8192", groq_api_key=GROQ_API_KEY)
        self.prompt = ChatPromptTemplate.from_template(
            f"""You are a {agent_type} booking assistant. Use the provided context and user history to assist with {agent_type} bookings.
            Context: {{context}}
            User History: {{history}}
            Current Message: {{message}}
            
            Provide accurate information about {agent_type} availability, prices, and booking details.
            If a booking action is requested, prepare the booking details and request confirmation.
            For flights, include flight number, airline, departure/arrival times, and price.
            For hotels, include hotel name, room type, price per night, and available amenities."""
        )

    async def process(self, state: AgentState, db):
        history = vectorstore.similarity_search(state["messages"][-1]["content"], k=5)

        history_text = "\n".join([doc.page_content for doc in history])
        
        # Fetch context from MongoDB
        if self.agent_type == "flight":
            items = await db.flights.find().to_list(100)
            context = {
                "items": [{
                    "id": str(item["_id"]),
                    "flight_number": item["flight_number"],
                    "airline": item["airline"],
                    "departure_airport": item["departure_airport"],
                    "arrival_airport": item["arrival_airport"],
                    "departure_time": item["departure_time"].isoformat(),
                    "arrival_time": item["arrival_time"].isoformat(),
                    "price": item["price"],
                    "seats_available": item["seats_available"],
                    "cabin_class": item["cabin_class"]
                } for item in items]
            }
        else:  # hotel
            items = await db.hotels.find().to_list(100)
            context = {
                "items": [{
                    "id": str(item["_id"]),
                    "name": item["name"],
                    "address": item["address"],
                    "star_rating": item["star_rating"],
                    "room_type": item["room_type"],
                    "price_per_night": item["price_per_night"],
                    "available_rooms": item["available_rooms"],
                    "amenities": item["amenities"]
                } for item in items]
            }
        
        # Process user message with LLM
        response = await self.llm.ainvoke(
            self.prompt.format(
                context=context,
                history=history_text,
                message=state["messages"][-1]["content"]
            )
        )
        
        # Handle booking requests
        if "book" in state["messages"][-1]["content"].lower() and context["items"]:
            state["requires_confirmation"] = True
            state["confirmation_data"] = {
                "item_id": context["items"][0]["id"],
                "price": context["items"][0].get("price", context["items"][0].get("price_per_night")),
                "details": context["items"][0]
            }
            response.content += "\nPlease confirm your booking with the following details:\n" + str(context["items"][0])
        
        # Store conversation in ChromaDB
        vectorstore.add_texts(
            texts=[f"User: {state['messages'][-1]['content']}\nAssistant: {response.content}"],
            metadatas=[{"user_id": state["user_id"], "timestamp": datetime.utcnow().isoformat()}]
        )
        
        state["messages"].append({"role": "assistant", "content": response.content})
        return state

# Initialize agents
flight_agent = TravelAgent("flight")
hotel_agent = TravelAgent("hotel")

# LangGraph workflow
workflow = StateGraph(AgentState)
async def flight_agent_node(state, db=Depends(get_database)):
    return await flight_agent.process(state, db)

async def hotel_agent_node(state, db=Depends(get_database)):
    return await hotel_agent.process(state, db)

workflow.add_node("flight_agent", flight_agent_node)
workflow.add_node("hotel_agent", hotel_agent_node)


workflow.add_node("human_confirmation", lambda state: state)

def router(state: AgentState) -> str:
    if state["requires_confirmation"]:
        return "human_confirmation"
    return state["agent_type"]

workflow.add_conditional_edges(
    "flight_agent",
    router,
    {"flight_agent": "flight_agent", "hotel_agent": "hotel_agent", "human_confirmation": "human_confirmation"}
)
workflow.add_conditional_edges(
    "hotel_agent",
    router,
    {"flight_agent": "flight_agent", "hotel_agent": "hotel_agent", "human_confirmation": "human_confirmation"}
)
workflow.add_edge("human_confirmation", END)
workflow.set_entry_point("flight_agent")
graph = workflow.compile(checkpointer=MemorySaver())

async def process_chat(request, user_id):
    session_id = request.session_id or str(uuid.uuid4())
    state = {
        "user_id": user_id,
        "messages": [{"role": "user", "content": request.message}],
        "context": {},
        "requires_confirmation": False,
        "confirmation_data": None,
        "agent_type": "flight" if "flight" in request.message.lower() else "hotel"
    }
    
    result = await graph.ainvoke(state, config={"configurable": {"thread_id": session_id}})
    
    return ChatResponse(
        response=result["messages"][-1]["content"],
        session_id=session_id,
        requires_confirmation=result["requires_confirmation"],
        confirmation_data=result["confirmation_data"]
    )

async def confirm_booking(request, user_id):
    from bson import ObjectId
    from datetime import datetime
    
    db = await get_database()
    state_obj = graph.get_state({"configurable": {"thread_id": request.session_id}})
    state = state_obj.get_state()
    
    if not state.get("requires_confirmation"):
        raise HTTPException(status_code=400, detail="No confirmation required")
    
    if request.confirmed:
        if state["agent_type"] == "flight":
            booking_data = {
                "user_id": user_id,
                "flight_id": state["confirmation_data"]["item_id"],
                "total_price": state["confirmation_data"]["price"],
                "booking_date": datetime.utcnow(),
                "passenger_name": "TBD",
                "passenger_email": "TBD@example.com"
            }
            result = await db.flight_bookings.insert_one(booking_data)
            await db.flights.update_one(
                {"_id": ObjectId(state["confirmation_data"]["item_id"])},
                {"$inc": {"seats_available": -1}}
            )
            response = f"Flight booking confirmed with ID: {str(result.inserted_id)}"
        else:
            booking_data = {
                "user_id": user_id,
                "hotel_id": state["confirmation_data"]["item_id"],
                "total_price": state["confirmation_data"]["price"],
                "booking_date": datetime.utcnow(),
                "guest_name": "TBD",
                "guest_email": "TBD@example.com"
            }
            result = await db.hotel_bookings.insert_one(booking_data)
            await db.hotels.update_one(
                {"_id": ObjectId(state["confirmation_data"]["item_id"])},
                {"$inc": {"available_rooms": -1}}
            )
            response = f"Hotel booking confirmed with ID: {str(result.inserted_id)}"
    else:
        response = "Booking cancelled by user"
    
    state["messages"].append({"role": "system", "content": response})
    state["requires_confirmation"] = False
    state["confirmation_data"] = None
    
    await graph.ainvoke(state, config={"configurable": {"thread_id": request.session_id}})
    
    return ChatResponse(
        response=response,
        session_id=request.session_id
    )