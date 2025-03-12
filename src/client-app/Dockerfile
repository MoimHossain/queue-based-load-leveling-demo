# Use an official lightweight Python image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy necessary files
COPY requirements.txt ./
COPY app.py ./
COPY templates ./templates

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
