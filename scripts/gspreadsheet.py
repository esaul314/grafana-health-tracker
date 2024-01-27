import configparser
import argparse
import gspread
import pandas as pd
import mysql.connector
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


def get_google_sheet_data(sheet_id, worksheet_name, keyfile_name, range_name='A:F'):
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(keyfile_name, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(sheet_id).worksheet('Sheet1')

    tstamp_data = sheet.col_values(1)[31:]  # Column A, starting from row 32
    systolic_data = sheet.col_values(3)[31:]  # Column C
    diastolic_data = sheet.col_values(4)[31:]  # Column D
    pulse_data = sheet.col_values(5)[31:]  # Column E
    comment_data = sheet.col_values(6)[31:]  # Column F

    data = zip(tstamp_data, systolic_data, diastolic_data, pulse_data, comment_data)
    df = pd.DataFrame(data, columns=['tstamp', 'systolic', 'diastolic', 'pulse', 'comment'])
    return df

    # data = sheet.get('A32:E')
    # return pd.DataFrame(data[1:], columns=['tstamp', 'systolic', 'diastolic', 'pulse', 'comment'])

def insert_data_to_mysql(df, mysql_config, user_id=1):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()


    insert_query = """
    INSERT INTO slipstreamdb.blood_pressure (systolic, diastolic, pulse, comment, user_id, tstamp, created)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    for row in df.itertuples(index=False):
        if any(field == '' for field in [row.systolic, row.diastolic, row.pulse, row.tstamp]):
            raise ValueError(f"Empty field detected in row: {row}")

        cursor.execute("SELECT COUNT(*) FROM slipstreamdb.blood_pressure WHERE tstamp = %s", (row.tstamp,))
        if cursor.fetchone()[0] == 0:
            cursor.execute(insert_query, (row.systolic, row.diastolic, row.pulse, row.comment, user_id, row.tstamp, datetime.now()))

    conn.commit()
    cursor.close()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--keyfile', help='Path to the Google service account keyfile', default=None)
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

    df = get_google_sheet_data(sheet_id, worksheet_name, keyfile_name)
    insert_data_to_mysql(df, mysql_config, user_id=1)

if __name__ == '__main__':
    main()
