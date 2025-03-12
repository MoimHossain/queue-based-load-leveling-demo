from flask import Flask, request, jsonify
import os
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueServiceClient, QueueClient
import json
import threading
import time
import logging
import base64  # Add import for base64 decoding

app = Flask(__name__)

# Queue processing function
def process_queue_messages():
    try:
        # Get connection string from environment variable
        connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        queue_name = os.environ.get("AZURE_STORAGE_QUEUE_NAME", "documentcreated")
        
        if not connection_string:
            logging.error("Azure Storage connection string not found in environment variables")
            return
            
        # Create a queue client
        queue_client = QueueClient.from_connection_string(connection_string, queue_name)
        
        logging.info(f"Starting to monitor queue: {queue_name}")
        
        while True:
            try:
                # Get messages from the queue (adjust max_messages based on your requirements)
                messages = queue_client.receive_messages(max_messages=10)
                
                for message in messages:
                    try:
                        # Process the message
                        logging.info(f"Processing message: {message.id}")
                        message_content = message.content
                        
                        # Decode base64 content
                        try:
                            decoded_content = base64.b64decode(message_content).decode('utf-8')
                            logging.info("Successfully decoded base64 message content")
                        except Exception as e:
                            logging.warning(f"Failed to decode base64 content: {str(e)}")
                            decoded_content = message_content  # Fallback to original if decoding fails
                        
                        # Try to extract blob name from message
                        try:
                            message_data = json.loads(decoded_content)
                            blob_subject = message_data.get('subject', '')
                            # Extract blob name from subject (format: /blobServices/default/containers/{container}/blobs/{blobname})
                            blob_name = blob_subject.split('/blobs/')[-1] if '/blobs/' in blob_subject else 'unknown'
                            logging.info(f"Detected blob: {blob_name}")
                        except json.JSONDecodeError:
                            logging.warning("Could not parse message JSON content")
                            blob_name = 'unknown'
                        
                        # Print message to console
                        print("\n=============================================")
                        print("NEW MESSAGE RECEIVED FROM AZURE QUEUE:")
                        print(f"ID: {message.id}")
                        print(f"Blob name: {blob_name}")
                        print(f"Content: {message_content}")
                        print("=============================================\n")
                        
                        # Delete the message from the queue after processing
                        queue_client.delete_message(message.id, message.pop_receipt)
                        logging.info(f"Message {message.id} for blob '{blob_name}' processed and deleted")
                    except Exception as e:
                        logging.error(f"Error processing message {message.id}: {str(e)}")
                
                # Sleep for a short time to avoid excessive polling
                time.sleep(10)
                
            except Exception as e:
                logging.error(f"Error receiving messages: {str(e)}")
                time.sleep(5)  # Wait a bit longer on errors
                
    except Exception as e:
        logging.error(f"Queue processing error: {str(e)}")

# Initialize a variable to track if the thread has been started
queue_thread_started = False

@app.before_request
def ensure_queue_thread_running():
    global queue_thread_started
    if not queue_thread_started:
        queue_thread = threading.Thread(target=process_queue_messages, daemon=True)
        queue_thread.start()
        app.logger.info("Queue processing thread started")
        queue_thread_started = True

@app.route("/")
def index():
    return f"Background service is running!", 200

@app.route("/onDocumentCreated", methods=["POST"])
def on_document_created():
    try:
        print("Received a message from Azure Queue Triggered")
        message = request.get_json()
        print(f"Received message from Azure Queue: {json.dumps(message, indent=2)}")
        return jsonify({"status": "processed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Start the thread immediately if not running in a web server context
    queue_thread = threading.Thread(target=process_queue_messages, daemon=True)
    queue_thread.start()
    logging.info("Queue processing thread started")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
