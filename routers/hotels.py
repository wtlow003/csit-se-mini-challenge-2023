import logging
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Request, status, Query, HTTPException
from pydantic import BaseModel
from typing import Annotated, List, Union

from models.hotels import Hotel
from utils import validate_date_format


logger = logging.getLogger(__name__)


class Message(BaseModel):
    message: str


router = APIRouter(tags=["hotels"], responses={404: {"description": "Not found"}})


@router.get(
    "/hotel",
    response_model=List[Union[Hotel, None]],
    responses={
        200: {
            "description": "Query successful.",
            "content": {
                "application/json": {
                    "example": {
                        "City": "Frankfurt",
                        "Check In Date": "2023-12-10",
                        "Check Out Date": "2023-12-16",
                        "Hotel": "Hotel J",
                        "Price": 2959,
                    }
                }
            },
        },
        400: {"model": Message, "description": "Bad Input."},
    },
    status_code=status.HTTP_200_OK,
)
async def retrieve_hotels(
    req: Request,
    checkInDate: Annotated[
        str,
        Query(
            description="Date of check-in at the hotel. ISO date format (`YYYY-MM-DD`)",
            regex="^\d{4}-\d{2}-\d{2}$",
        ),
    ],
    checkOutDate: Annotated[
        str,
        Query(
            description="Date of check-out at the hotel. ISO date format (`YYYY-MM-DD`)",
            regex="^\d{4}-\d{2}-\d{2}$",
        ),
    ],
    destination: Annotated[
        str,
        Query(description="Destination city. Case-insensitive.", min_length=1),
    ],
):
    """
    Get a list of hotels providing the cheapest price,
    given the destination city, check-in date, and check-out date.
    """
    # validate departure date format
    correct, checkInDate = validate_date_format(checkInDate)
    if not correct:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bad input. checkInDate ({checkInDate}) not in ISO format (YYYY-MM-DD).",
        )

    # validate return date format
    correct, checkOutDate = validate_date_format(checkOutDate)
    if not correct:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bad input. checkOutDate ({checkOutDate}) not in ISO format (YYYY-MM-DD).",
        )

    # validate the departure and return date
    if checkInDate > checkOutDate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bad input. checkInDate ({checkInDate}) is later than checkOutDate ({checkOutDate}).",
        )

    mongo_query_handler = req.app.state.mongo_query_handler
    db = mongo_query_handler["minichallenge"]
    collection = db["hotels"]

    # searching for hotels given check in dates
    check_in_date_iso = datetime.fromisoformat(checkInDate)
    check_out_date_iso = datetime.fromisoformat(checkOutDate)

    # NOTE: need to handle case-insentivity for `destination`
    query = {
        "city": destination.title(),
        "date": {"$gte": check_in_date_iso, "$lte": check_out_date_iso},
    }

    logger.info("Retrieving hotel information...")
    results = list(collection.find(query))

    if not results:
        return []

    logger.info("Generating suitable hotels...")
    hotel_prices = defaultdict(int)
    # aggregating hotel prices during the timespan
    for hotel in results:
        hotel_prices[hotel["hotelName"]] += hotel["price"]

    # get the lowest price hotel
    hotel_prices = sorted(hotel_prices.items(), key=lambda x: x[1])
    min_hotel_price = hotel_prices[0][1]  # (hotelName, hotelPrice)
    hotels = [h for h in hotel_prices if h[1] == min_hotel_price]

    payload = []
    for hotel in hotels:
        payload.append(
            Hotel(
                city=destination.title(),
                check_in_date=checkInDate,
                check_out_date=checkOutDate,
                hotel=hotel[0],
                price=hotel[1],
            )
        )

    return payload
