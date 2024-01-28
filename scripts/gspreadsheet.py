import configparser
import argparse
import gspread
import pandas as pd
import mysql.connector
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def get_google_sheet_data(sheet_id, worksheet_name, keyfile_name, column_mappings, start_row=1):
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(keyfile_name, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).worksheet(worksheet_name)

    fetched_columns = {}
    for field, col in column_mappings.items():
        col_range = f'{col}{start_row}:{col}'
        # logging.info(f"Fetching data for {col_range}")
        fetched_data = sheet.get(col_range)
        fetched_columns[field] = [item for sublist in fetched_data for item in sublist]
        # logging.info(f"Fetched data for {field} (Column {col}): {fetched_data}")

    data = list(zip(*fetched_columns.values()))
    # logging.info(f"Data: {data}")
    df = pd.DataFrame(data, columns=list(column_mappings.keys()))
    return df

def insert_data_to_mysql(df, mysql_config, user_id=1):
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()

        insert_query = f"""
        INSERT INTO {mysql_config['database']}.blood_pressure (systolic, diastolic, pulse, comment, user_id, tstamp, created)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        for row in df.itertuples(index=False):
            # logging.info(f"Row: {row}")
            if any(field == '' for field in [row.systolic, row.diastolic, row.pulse, row.tstamp]):
                raise ValueError(f"Empty field detected in row: {row}")

            cursor.execute(f"SELECT COUNT(*) FROM {mysql_config['database']}.blood_pressure WHERE tstamp = %s", (row.tstamp,))
            if cursor.fetchone()[0] == 0:
                cursor.execute(insert_query, (row.systolic, row.diastolic, row.pulse, row.comment, user_id, row.tstamp, datetime.now()))

        conn.commit()

    except Exception as e:
        logging.error(f"Error inserting data to MySQL: {e}")

    finally:
        cursor.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Read blood pressure data from a Google Sheet and insert into a DB.')
    parser.add_argument('--keyfile', help='Path to the Google service account keyfile', default='/app/scripts/keyfile.json')
    parser.add_argument('--config', help='Path to config file', default='/app/scripts/config.ini')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    sheet_id = config['GoogleSheets']['sheet_id']
    worksheet_name = config['GoogleSheets']['worksheet_name']
    range_name = config['GoogleSheets']['range_name']
    keyfile_name = config['General']['keyfile_name']

    mysql_config = {
        'user': config['MySQL']['user'],
        'password': config['MySQL']['password'],
        'host': config['MySQL']['host'],
        'database': config['MySQL']['database']
    }

    column_mappings = {
        'tstamp': config['GoogleSheets']['tstamp_column'],
        'systolic': config['GoogleSheets']['systolic_column'],
        'diastolic': config['GoogleSheets']['diastolic_column'],
        'pulse': config['GoogleSheets']['pulse_column'],
        'comment': config['GoogleSheets']['comment_column']
    }

    start_row = config['GoogleSheets'].getint('start_row', 1)
    df = get_google_sheet_data(sheet_id, worksheet_name, keyfile_name, column_mappings, start_row)


    insert_data_to_mysql(df, mysql_config, user_id=1)

if __name__ == '__main__':
    main()
