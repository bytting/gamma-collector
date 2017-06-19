
import os, sqlite3

def create(msg):
    dbpath = os.expanduser("~/ashes/")
    if not os.path.isdir(dbpath):
        os.makedirs(dbpath)
    dbpath += msg["session_name"] + ".db"
    connection = sqlite3.connect(dbpath)
    cursor = connection.cursor()
    cursor.execute(''' ''')
    connection.commit()
    return connection

def close(connection):
    connection.close()

def insertSession(msg):
    pass

def insertSpectrum(spec):
    pass
