import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from pymongo import MongoClient
from routers import flights, hotels

from exceptions import request_validation_exception_handler

MONGO_URL = os.getenv(
    "MONGO_HOST",
    "mongodb+srv://userReadOnly:7ZT817O8ejDfhnBM@minichallenge.q4nve1r.mongodb.net/",
)


def init_mongo_query_handler():
    """
    Initialise MongoDB connection.

    Returns:
        _type_: _description_
    """
    logger.info("Initialising connection to MongoDB.")
    return MongoClient(MONGO_URL)


logger = logging.getLogger(__name__)


# =============================================================================
# Define Application
# =============================================================================

app = FastAPI()
app.include_router(flights.router)
app.include_router(hotels.router)

# =============================================================================
# Define Generic Attributes and Exception Handlers
# =============================================================================

# NOTE: check for usage of global mongo_query_handler instead
app.state.mongo_query_handler = init_mongo_query_handler()

app.add_exception_handler(RequestValidationError, request_validation_exception_handler)


################################################################################
# Do not modify
################################################################################
@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """
    Redirect to swagger documentation when accessing the root path
    """
    return RedirectResponse("/docs")


@app.get("/healthcheck", tags=["system"])
async def healthcheck():
    """
    Endpoint allowing us to know if the server is running

    Returns:

        bool: True if server if running

    """
    return True


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
