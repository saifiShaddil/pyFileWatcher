import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv  # type: ignore
import requests  # type: ignore
import zipfile  # type: ignore

load_dotenv()

# Database connection string (update with your database details)
DB_CONNECTION_STRING = os.getenv("DATABASE_URL")
GEOSERVER_URL = os.getenv("GEOSERVER_URL")
GEOSERVER_WORKSPACE = "pvlayer"  # Change to your workspace
GEOSERVER_STORE = "pvlayer"      # Change to your datastore name
GEOSERVER_USERNAME = "admin"     # Change to your GeoServer username
GEOSERVER_PASSWORD = "geoserver" # Change to your GeoServer password


# Define layer mapping (you can expand this)
LAYER_MAPPING = {
    "Mumty_Structure": ["mumty", "structure"],
    "Turbovents": ["turbovents"],
    "parapet": ["parapet"],
    "RCC_Roof": ["rcc"],
    "Metal_Roof": ["metal"],
    "RoofRidge": ["ridge"],
    "WaterTank": ["watertank", "tank"],
    "HVAC": ["hvac"],
    "Helipads": ["helipad"],
    # Add additional layers and keywords here
}


def remove_existing_layer(layer_name):
    """
    Removes an existing layer if it exists.
    """
    layer_url = f"{GEOSERVER_URL}/workspaces/{GEOSERVER_WORKSPACE}/layers/pvlayer:{layer_name}"
    response = requests.get(
        layer_url,
        auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD)
    )

    if response.status_code == 200:
        print(f"Layer '{layer_name}' exists. Removing...")
        delete_response = requests.delete(
            layer_url,
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD)
        )

        if delete_response.status_code == 200:
            print(f"Layer '{layer_name}' removed successfully.")
        else:
            print(f"Error removing layer '{layer_name}': {delete_response.status_code}, {delete_response.text}")
    else:
        print(f"Layer '{layer_name}' does not exist. Proceeding with upload.")

def upload_and_publish_layer(zip_file_path, layer_name):
    """
        Uploads and publishes a zipped shapefile to GeoServer.
        If the layer already exists, it deletes and replaces it.
    """
    # Step 1: Remove the existing layer if it exists
    remove_existing_layer(layer_name)

    # Step 2: Create the datastore
    datastore_url = f"{GEOSERVER_URL}/workspaces/{GEOSERVER_WORKSPACE}/datastores/{GEOSERVER_STORE}"
    print(f"Checking if datastore exists at {datastore_url}")
    response = requests.get(
        datastore_url,
        auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD)
    )
    

    if response.status_code == 200:
        print(f"Datastore {GEOSERVER_WORKSPACE} already exists.")
    elif response.status_code == 404:
         # Step 2: Create the datastore if it doesn't exist
        print(f"Datastore '{GEOSERVER_STORE}' not found. Creating datastore...")

        datastore_payload = f"""
        <dataStore>
            <name>{GEOSERVER_STORE}</name>
            <connectionParameters>
                <entry key="url">file:{zip_file_path}</entry>
                <entry key="usePreparedStatements">true</entry>
                <entry key="dbtype">shapefile</entry>
            </connectionParameters>
        </dataStore>
        """
        headers = {"Content-Type": "application/xml"}

        response = requests.post(
                datastore_url,
                headers=headers,
                auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
                data=datastore_payload
            )
        if response.status_code != 201:
            print(f"Error creating datastore: {response}, {response.text}")
            return
    
        print(f"Datastore '{GEOSERVER_STORE}' created successfully.")
    else:
        print(f"Error checking datastore existence: {response.status_code}, {response.text}")
        return
    
    # Step 3: Upload the shapefile to the datastore
    upload_url = f"{GEOSERVER_URL}/workspaces/{GEOSERVER_WORKSPACE}/datastores/{GEOSERVER_STORE}/file.shp"

    with open(zip_file_path, 'rb') as file_data:
        upload_response = requests.put(
            upload_url,
            headers={"Content-Type": "application/zip"},
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
            data=file_data
        )
    
    if upload_response.status_code == 200:
        print(f"Shapefile '{zip_file_path}' uploaded successfully.")
    elif upload_response.status_code == 201:
        print(f"Shapefile '{zip_file_path}' uploaded successfully.")
    else:
        print(f"Error uploading shapefile: {upload_response.status_code}, {upload_response.text}")
        return
    
     # Step 4: Create and configure the layer
    feature_type_url = f"{GEOSERVER_URL}/workspaces/{GEOSERVER_WORKSPACE}/datastores/{GEOSERVER_STORE}/featuretypes"
    # Check if the feature type already exists
    feature_type_exists_url = f"{feature_type_url}/{layer_name}"
    exists_response = requests.get(
        feature_type_exists_url,
        auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD)
    )
    
    if exists_response.status_code == 200:
        print(f"Feature type '{layer_name}' already exists in datastore '{GEOSERVER_STORE}'. Skipping creation.")
    else:
         # Proceed to create the feature type if it doesn't exist
        feature_type_payload = f"""
            <featureType>
                <name>{layer_name}</name>
                <nativeName>{layer_name}</nativeName>
                <srs>EPSG:4326</srs>
            </featureType>
        """
        layer_response = requests.post(
            feature_type_url,
            headers={"Content-Type": "application/xml"},
            auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD),
            data=feature_type_payload
        )
        print(f"layer_response '{layer_response}.")
        if layer_response.status_code in [200, 201]:
            print(f"Layer '{layer_name}' created successfully.")
        else:
            print(f"Error creating layer: {layer_response.status_code}, {layer_response.text}")
            return
    
    
    print(f"Layer Published Successfully.")
    
    
    
 



# Watchdog Event Handler
import os
import subprocess
import zipfile

# Grant full permissions using icacls (Windows-specific)
def grant_file_permissions(file_path):
    try:
        # Run the icacls command to grant full permissions to the file
        subprocess.run(["icacls", file_path, "/grant", "Everyone:F"], check=True)
        print(f"Full permissions granted to {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error while granting permissions to {file_path}: {e}")

class GeoWatcherHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".zip"):
            zip_file_path = event.src_path
            file_name = os.path.basename(zip_file_path).split('.')[0]
            directory = os.path.dirname(zip_file_path)

            # Grant permissions to the zip file before processing
            grant_file_permissions(zip_file_path)

            try:
                # Extract the zip file to check for required shapefile components
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(directory)

                # Now check if the zip file contains all required shapefile components
                shapefile_base = None
                for file in zip_ref.namelist():
                    if file.lower().endswith(".shp"):
                        shapefile_base = file.lower().replace(".shp", "")
                        break
                
                # Ensure that all required shapefile components exist
                required_files = [".shp", ".shx", ".dbf", ".prj"]
                missing_files = [ext for ext in required_files if not os.path.exists(os.path.join(directory, shapefile_base + ext))]

                if missing_files:
                    print(f"Warning: Missing required shapefile components for '{file_name}': {', '.join(missing_files)}")
                    return

                print(f"All required files found for '{file_name}'. Uploading to GeoServer...")

                # Trigger upload and publish
                upload_and_publish_layer(zip_file_path, file_name)

            except zipfile.BadZipFile:
                print(f"Error: The file '{zip_file_path}' is not a valid zip file.")
            except Exception as e:
                print(f"Error while processing zip file '{zip_file_path}': {e}")


# Main function
def main():
    path_to_watch = r"C:\Users\shadil\Desktop\python\uploads"  # Adjust the path as necessary
    print(f"Watching directory: {path_to_watch} for zip file uploads...")

    event_handler = GeoWatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
