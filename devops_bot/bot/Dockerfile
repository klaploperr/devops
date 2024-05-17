FROM python:3.10-alpine
WORKDIR /bot

COPY main.py .
COPY definitions.py .
COPY .env .
COPY requirements.txt .

RUN apk update \
	&& apk add libpq postgresql-dev \
	&& apk add build-base
RUN pip install -r requirements.txt

EXPOSE 1313

CMD ["python", "main.py"]
