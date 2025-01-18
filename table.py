import os
import psycopg2 # type: ignore
from dotenv import load_dotenv # type: ignore

load_dotenv()

def create_table(connection_string):
    """
    Creates a table in a PostgreSQL database using the provided connection string.

    Args:
        connection_string (str): The PostgreSQL connection string.

    Returns:
        str: Success or error message.
    """
    query = """
    CREATE TABLE filetable (
        id SERIAL PRIMARY KEY,
        file_name TEXT NOT NULL,
        isupdated TEXT,
        status TEXT ,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    try:
        # Connect to the database
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cursor:
                # Check if the table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'filetable'
                    );
                """)
                table_exists = cursor.fetchone()[0]

                if table_exists:
                    # Fetch and print existing table data
                    cursor.execute("SELECT * FROM filetable;")
                    rows = cursor.fetchall()
                    print("Existing data in 'filetable':")
                    for row in rows:
                        print(row)
                    return "Table 'filetable' already exists. Data logged above."

                # Create the table if it does not exist
                cursor.execute(query)
                conn.commit()
                return "Table 'filetable' created successfully."

    except psycopg2.Error as e:
        return f"An error occurred: {e}"

# Example usage
DATABASE_URL = os.getenv("DATABASE_URL")
result = create_table(DATABASE_URL)
print(result)
