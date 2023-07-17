# Pull base image
FROM python:3.11

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code/

# Install dependencies
COPY poetry.lock .
COPY pyproject.toml .
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install

COPY ./models /code/models
COPY ./routers /code/routers
COPY ./exceptions.py /code/exceptions.py
COPY ./utils.py /code/utils.py
COPY ./main.py /code/main.py

EXPOSE 8080

ENTRYPOINT ["python3", "main.py"]