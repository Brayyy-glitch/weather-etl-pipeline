FROM python:3.12-slim

WORKDIR /app

# Copy the requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "pipeline.py"]

# # Build the image
# docker build -t weather-etl .

# # Run pipeline, saving the data to a local ./data folder
# docker run --rm -v "$(pwd)/data:/app/data" weather-etl

# # Run tests
# docker run --rm weather-etl pytest