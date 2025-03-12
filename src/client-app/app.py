from flask import Flask, request, render_template
import os
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# Local upload folder (optional)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Azure Storage Configuration (Replace with your details)
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# Ensure the container exists
try:
    container_client.get_container_properties()
except Exception:
    container_client.create_container()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part", 400
    
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    # Save file locally (optional, for debugging)
    local_file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(local_file_path)

    # Upload file to Azure Blob Storage
    try:
        blob_client = container_client.get_blob_client(file.filename)
        with open(local_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        return f"File '{file.filename}' uploaded to Azure Blob Storage successfully!", 200
    except Exception as e:
        return f"Error uploading to Azure: {str(e)}", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
