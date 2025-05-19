import sqlite3

class ConnectionAccessor():
    def __init__(self):
        pass

class DatabaseConnection():
    def __init__(self, path: str):
        self.connection = sqlite3.connect(path)

    def close(self):
        self.c

