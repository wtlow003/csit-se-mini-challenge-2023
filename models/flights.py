from datetime import date
from pydantic import BaseModel, Field
from pydantic import field_validator


class Flight(BaseModel):
    city: str = Field(alias="City")
    departure_date: str = Field(alias="Departure Date")
    departure_airline: str = Field(alias="Departure Airline")
    departure_price: int = Field(alias="Departure Price")
    return_date: str = Field(alias="Return Date")
    return_airline: str = Field(alias="Return Airline")
    return_price: int = Field(alias="Return Price")

    class Config:
        populate_by_name = True

    @field_validator("departure_date", "return_date")
    def date_in_iso_format(cls, v):
        try:
            date.fromisoformat(v)
            return v
        except ValueError as e:
            raise ValueError("Date must be in ISO date format (YYYY-MM-DD)") from e

    # # https://stackoverflow.com/questions/72338650/pydantic-multi-field-comparison
    # @field_validator("return_date")
    # def valid_return_date(cls, return_date, values, **kwargs):
    #     if (
    #         "departure_date" in values.data
    #         and return_date < values.data["departure_date"]
    #     ):
    #         raise ValueError("Return date needs to be on/after the departure date.")
    #     return return_date
