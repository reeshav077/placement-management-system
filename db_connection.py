import importlib

def get_connection():
    try:
        mysql_connector = importlib.import_module("mysql.connector")
    except ModuleNotFoundError:
        print("\n[!] Database driver not found. Install it with: pip install mysql-connector-python\n")
        return None

    try:
        connection = mysql_connector.connect(
            host="gateway01.ap-northeast-1.prod.aws.tidbcloud.com",      # e.g., gateway01.us-east-1.prod.aws.tidbcloud.com
            port=4000,
            user="2jTesgJV7zGtc6q.root",      # e.g., 3x8abc.root
            password="yQel1GXGSumLcEH2",
            database="placement_db",
            ssl_disabled=False,
            ssl_verify_cert=False
        )
        return connection
    except mysql_connector.Error as err:
        print(f"\n[!] Database Connection Error: {err}\n")
        return None