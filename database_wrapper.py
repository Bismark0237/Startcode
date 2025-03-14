import mysql.connector

class Database:
    def __init__(self, host, gebruiker, wachtwoord, database):
        """
        Initialiseer een nieuwe database.

        Parameters:
            host (str): Het adres van de MySQL-server.
            gebruiker (str): De gebruikersnaam voor de database.
            wachtwoord (str): Het wachtwoord voor de database.
            database (str): De naam van de database.
        """
        self.host = host
        self.gebruiker = gebruiker
        self.wachtwoord = wachtwoord
        self.database = database
        self.connection = None

    def connect(self):
        """Maakt verbinding met de MySQL-database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.gebruiker,
                password=self.wachtwoord,
                database=self.database
            )
            print("✅ Verbonden met de database!")
        except mysql.connector.Error as err:
            print(f"❌ Fout bij verbinden met de database: {err}")

    def execute_query(self, query, params=None):
        """
        Voert een SQL-query uit.

        Parameters:
            query (str): De SQL-query.
            params (tuple, optional): De parameters voor de query.

        Returns:
            list of dicts: Query-resultaten als het een SELECT-query is.
            bool: True bij een succesvolle INSERT/UPDATE/DELETE.
        """
        if not self.connection:
            print("❌ Niet verbonden met de database!")
            return None

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params)

            if cursor.description:  # SELECT-query
                result = cursor.fetchall()
            else:  # INSERT/UPDATE/DELETE-query
                self.connection.commit()
                result = cursor.rowcount > 0

            cursor.close()
            return result
        except mysql.connector.Error as err:
            print(f"❌ Fout bij uitvoeren van query: {err}")
            return None

    def close(self):
        """Sluit de verbinding met de database."""
        if self.connection:
            self.connection.close()
            print("✅ Databaseverbinding gesloten.")
        else:
            print("❌ Geen actieve databaseverbinding om te sluiten.")
