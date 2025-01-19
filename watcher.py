import datetime
import os
import shutil
import time
import psycopg2 # type: ignore
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv # type: ignore
import requests # type: ignore

load_dotenv()

# Database connection string (update with your database details)
DB_CONNECTION_STRING = os.getenv("DATABASE_URL")

class FileUploadHandler(FileSystemEventHandler):
    def __init__(self, destination_folder, db_connection_string):
        self.destination_folder = destination_folder
        self.db_connection_string = db_connection_string

    def on_created(self, event):
        if event.is_directory:
            return

        file_name = os.path.basename(event.src_path)
        print(f"New file detected: {file_name}")

        # Handle database operation
        self.handle_database(file_name)

        # Simulate file processing and update status
        if self.process_file(file_name):
            self.update_status(file_name)

        # Move the file to the destination folder
        self.move_file(event.src_path)

    def handle_database(self, file_name):
        try:
            conn = psycopg2.connect(self.db_connection_string)
            cursor = conn.cursor()

            # Check if the file already exists in the database
            cursor.execute("SELECT id, isupdated FROM filetable WHERE file_name = %s;", (file_name,))
            record = cursor.fetchone()

            if record:
                # Update the existing record
                updated_value = f"{file_name}_{datetime.datetime.now()}"
                cursor.execute("UPDATE filetable SET isupdated = %s WHERE id = %s;", (updated_value, record[0]))
                print(f"File {file_name} already exists. Updated record with 'isupdated' = {updated_value}.")
            else:
                # Insert a new record
                cursor.execute("INSERT INTO filetable (file_name, status) VALUES (%s, %s);", (file_name, 'added'))
                print(f"File {file_name} added to the database with status 'Added'.")

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error handling database operation: {e}")
    
    def process_file(self, file_name):
        """
        Simulates processing of the file.
        Replace this function with actual processing logic.
        """
        print(f"Processing file: {file_name}")
        # Simulate a successful processing
        time.sleep(2)  # Simulate processing delay
        print(f"Processing completed for file: {file_name}")
        return True
    
    def update_status(self, file_name):
        try:
            conn = psycopg2.connect(self.db_connection_string)
            cursor = conn.cursor()

            # Update the status column to 'processed'
            cursor.execute("UPDATE filetable SET status = %s WHERE file_name = %s;", ('processed', file_name))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Status updated to 'processed' for file: {file_name}")
        except Exception as e:
            print(f"Error updating status for file {file_name}: {e}")

    def move_file(self, source_path):
        try:
            # Create the destination folder if it doesn't exist
            if not os.path.exists(self.destination_folder):
                os.makedirs(self.destination_folder)

            # Move the file to the destination folder
            shutil.move(source_path, self.destination_folder)
            print(f"Moved {os.path.basename(source_path)} to {self.destination_folder}")
        except Exception as e:
            print(f"Error moving file: {e}")

def watch_folder(source_folder, destination_folder, db_connection_string):
    event_handler = FileUploadHandler(destination_folder, db_connection_string)
    observer = Observer()
    observer.schedule(event_handler, source_folder, recursive=False)
    observer.start()
    print(f"Watching for file uploads in: {source_folder}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    source_folder = r"C:\Users\shadil\Desktop\python\uploads"
    destination_folder = r"C:\Users\shadil\Desktop\python\visited"
    watch_folder(source_folder, destination_folder, DB_CONNECTION_STRING)
