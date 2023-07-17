from datetime import date
from pydantic import BaseModel, Field
from pydantic import field_validator


class Hotel(BaseModel):
    city: str = Field(alias="City")
    check_in_date: str = Field(alias="Check In Date")
    check_out_date: str = Field(alias="Check Out Date")
    hotel: str = Field(alias="Hotel")
    price: int = Field(alias="Price")

    class Config:
        populate_by_name = True

    @field_validator("check_in_date", "check_out_date")
    def date_in_iso_format(cls, v):
        try:
            date.fromisoformat(v)
            return v
        except ValueError as e:
            raise ValueError("Date must be in ISO date format (YYYY-MM-DD)") from e

    # @field_validator("check_out_date")
    # def valid_check_out_date(cls, check_out_date, values, **kwargs):
    #     if (
    #         "check_in_date" in values.data
    #         and check_out_date < values.data["check_in_date"]
    #     ):
    #         raise ValueError("Check out date needs to be on/after the check in date.")
    #     return check_out_date
