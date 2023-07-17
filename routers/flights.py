import logging
from datetime import datetime

from fastapi import APIRouter, Request, status, Query, HTTPException
from pydantic import BaseModel
from typing import Annotated, List, Union

from models.flights import Flight
from utils import validate_date_format


logger = logging.getLogger(__name__)


class Message(BaseModel):
    message: str


router = APIRouter(tags=["flights"], responses={404: {"description": "Not found"}})


@router.get(
    "/flight",
    response_model=List[Union[Flight, None]],
    responses={
        200: {
            "description": "Query successful.",
            "content": {
                "application/json": {
                    "example": {
                        "City": "Frankfurt",
                        "Departure Date": "2023-12-10",
                        "Departure Airline": "US Airways",
                        "Departure Price": 1766,
                        "Return Date": "2023-12-16",
                        "Return Airline": "US Airways",
                        "Return Price": 716,
                    }
                }
            },
        },
        400: {
            "model": Message,
            "description": "Bad Input.",
        },
    },
    status_code=status.HTTP_200_OK,
)
async def retrieve_flight(
    req: Request,
    departureDate: Annotated[
        str,
        Query(
            description="Departure date from Singapore. ISO date format (`YYYY-MM-DD`)",
            regex="^\d{4}-\d{2}-\d{2}$",
        ),
        # Depends(check_departure_isoformat),
    ],
    returnDate: Annotated[
        str,
        Query(
            description="Return date from destination city. ISO date format (`YYYY-MM-DD`)",
            regex="^\d{4}-\d{2}-\d{2}$",
        ),
    ],
    destination: Annotated[
        str,
        Query(description="Destination city. Case-insensitive.", min_length=1),
    ],
):
    """
    Get a list of return flights at the cheapest price, given the destination city,
    departure date, and arrival date.
    """
    # validate departure date format
    correct, departureDate = validate_date_format(departureDate)
    if not correct:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bad input. departureDate ({departureDate}) not in ISO format (YYYY-MM-DD).",
        )

    # validate return date format
    correct, returnDate = validate_date_format(returnDate)
    if not correct:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bad input. returnDate ({returnDate}) not in ISO format (YYYY-MM-DD).",
        )

    # validate the departure and return date (tgt)
    if departureDate > returnDate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bad input. departureDate ({departureDate}) is later than returnDate ({returnDate}).",
        )

    mongo_query_handler = req.app.state.mongo_query_handler
    db = mongo_query_handler["minichallenge"]
    collection = db["flights"]

    # searching for outbound and inbound flights
    departure_date_iso = datetime.fromisoformat(departureDate)
    return_date_iso = datetime.fromisoformat(returnDate)

    # NOTE: need to handle case-insentivity for `destination`
    o_query = {
        "srccity": "Singapore",
        "date": {"$eq": departure_date_iso},
        "destcity": destination.title(),
    }
    i_query = {
        "srccity": destination.title(),
        "date": {"$eq": return_date_iso},
        "destcity": "Singapore",
    }

    logger.info("Retrieving flight information...")
    o_result = collection.find(o_query).sort("price")
    i_result = collection.find(i_query).sort("price")

    outbound = list(o_result)
    inbound = list(i_result)

    # no valid flights (e.g. destination is invalid)
    if not (outbound or inbound):
        return []

    logger.info("Generating suitable flights...")
    min_outbound = outbound[0]["price"]
    min_inbound = inbound[0]["price"]

    outbound = [o for o in outbound if o["price"] == min_outbound]
    inbound = [i for i in inbound if i["price"] == min_inbound]

    payload = []
    for o in outbound:
        for i in inbound:
            payload.append(
                Flight(
                    city=destination.title(),
                    departure_date=departureDate,
                    departure_airline=o["airlinename"],
                    departure_price=o["price"],
                    return_date=returnDate,
                    return_airline=i["airlinename"],
                    return_price=i["price"],
                )
            )

    return payload
