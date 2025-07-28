import os
from dotenv import load_dotenv
import pymysql 


class DBConnect:
    def __init__(self):
        
        # Load environment variables from .env file
        load_dotenv()

        self.db_host = os.getenv('DB_HOST')
        self.db_name = os.getenv('DB_NAME')
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.connection = pymysql.connect(
            host= self.db_host,
            user= self.db_user,
            password= self.db_password,
            database= self.db_name,
            port=3306,  # Default MySQL port
        )

    def dump_gold_prices(self, gold_price_entries):
        with self.connection.cursor() as cursor:
            for entry in gold_price_entries:
                sql = """
                INSERT INTO gold_prices (price, country_id, gold_type, year, month, date, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    entry['price'], 
                    entry['country_id'], 
                    entry['gold_type'], 
                    entry['year'], 
                    entry['month'], 
                    entry['date'], 
                    entry['timestamp']
                ))
            self.connection.commit()
        print(f'[LOG] Successfully dumped {len(gold_price_entries)} entries to the database.')
    def close_connection(self):
        if self.connection:
            self.connection.close()
            print('[LOG] Database connection closed.')
        else:
            print('[LOG] No active database connection to close.')


db_connection = DBConnect()