import json
import requests
import psycopg2



class DBConnect():

    def __init__(self):
        pass


    def connect_to_db(self):
        self.connection = psycopg2.connect(user='db_user',
                                           password='db_password',
                                           database='db_name',
                                           host='db_host')
        print('Connection established')


    def check_connection(self):
        if self.connection is None:
            msg = 'Connection not established'
            raise Exception(msg)
        pass

