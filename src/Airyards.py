import json
import requests
import psycopg2
from .DBConnect import DBConnect
from slugify import slugify
import pandas as pd


class Airyards(DBConnect):

    json_cols = ['full_name', 'slug_name','position', 'team', 'rec_yards', 'rec',
                 'week', 'ms_air_yards', 'tm_airyards', 'yac',
                 'target_share', 'tm_att', 'aypt', 'air_yards', 'wopr', 'tar',
                 'racr', 'year', 'half_ppr', 'full_ppr', 'no_ppr'] ## need a list to preserve order

    json_col_type = {'full_name': str, 'slug_name':str, 'position':str, 'team':str, 'rec_yards': float,
                     'rec':float, 'week': int, 'ms_air_yards': float,
                     'tm_airyards':float, 'yac':float, 'target_share':float,
                     'tm_att':float, 'aypt': float,'air_yards':float, 'wopr':float, 'tar':float,
                     'racr': float, 'year':int, 'half_ppr':float, 'full_ppr':float,  'no_ppr':float}

    half_ppr = {'rec_yards': 0.1, 'rec': 0.5}
    full_ppr = {'rec_yards': 0.1, 'rec': 1}

    def __init__(self, year=2017):
        if year is not None:
            self.year = year
        else:
            print('No year input on init, assuming year 2017')
            self.year = 2017
        self.source = None
        self.connection = None
        self.data_json = None
        self.connect_to_db()
        self.url = 'http://airyards.com/{}/weeks'.format(str(year))
        #self.wipe_airyards_table -- done on "Wipe DataBase" command
        #self.update_airyards_table
        pass


    def remove_airyards_table(self):
        self.check_connection()
        to_do = 'DROP TABLE IF EXISTS "public"."airyards";'
        with self.connection.cursor() as cursor:
            cursor.execute(to_do)
            print('airyards table dropped')


    def create_airyards_table(self):
        self.check_connection()
        to_do = 'CREATE TABLE "public"."airyards" (' \
                '"full_name" varchar(100) COLLATE "default",' \
                'slug_name varchar(100) COLLATE "default",' \
                '"position" varchar(100) COLLATE "default",' \
                '"team" varchar(100) COLLATE "default",' \
                '"rec_yards" FLOAT,' \
                '"rec" FLOAT,' \
                '"week" int4 NOT NULL,' \
                '"ms_air_yards" FLOAT,' \
                '"tm_airyards" FLOAT,' \
                '"yac" FLOAT,' \
                '"target_share" FLOAT,' \
                '"tm_att" FLOAT,' \
                '"aypt" FLOAT,' \
                '"air_yards" FLOAT,' \
                '"wopr" FLOAT,' \
                '"tar" FLOAT,'\
                '"racr" FLOAT,' \
                '"year" INT,' \
                '"half_ppr" FLOAT,' \
                '"full_ppr" FLOAT,' \
                '"no_ppr" FLOAT);'
        with self.connection.cursor() as cursor:
            cursor.execute(to_do)
        self.connection.commit()
        print('public.airyards table created')


    def wipe_airyards_table(self):
        self.remove_airyards_table()
        self.create_airyards_table()
        print('Database Wiped')


    def update_airyards_table(self):
        self.request_data()
        try:
            if self.data_json is None:
                msg = 'Data not loaded'
                raise Exception(msg)
            else:
                self.insert_into_db(self.data_json)
                print('Database updated')
        except Exception as e:
            msg = 'Upload errored. ERR - {}'.format(str(e))
            raise Exception(msg)


    def request_data(self):
        self.source = requests.get(self.url).text
        self.data_json = json.loads(self.source)
        self.process_data()
        pass


    def _slug_str(self, string):
        if string is None:
            res = slugify('None')
        else:
            res = slugify(string)
        return res


    def process_data(self):
        """
        Method that loops thru list of dicts and appends year k,v. Will add more
        :return: None
        """
        for d in self.data_json:
            d['year'] = self.year
            d['slug_name'] = self._slug_str(d['full_name'])
            d.update(self.calc_fp(d))


    def insert_into_db(self, data_json):
        if data_json is None:
            msg = 'Data is None type'
            raise Exception(msg)
        else:
            insert_statement = 'INSERT INTO airyards (full_name, ' \
                               'slug_name, ' \
                               'position, ' \
                               'team, ' \
                               'rec_yards, ' \
                               'rec,' \
                               'week, ' \
                               'ms_air_yards, ' \
                               'tm_airyards, ' \
                               'yac, ' \
                               'target_share, ' \
                               'tm_att, ' \
                               'aypt, ' \
                               'air_yards, ' \
                               'wopr, ' \
                               'tar, '\
                               'racr, ' \
                               'year, ' \
                               'half_ppr, ' \
                               'full_ppr, ' \
                               'no_ppr) VALUES ('
        with self.connection.cursor() as cursor:
            for x in data_json:
                try:
                    print('Inserting {}'.format(x['full_name']))
                    v_str = ','.join([self.pickformat(i, x[i]) for i in self.json_cols])
                except Exception as e:
                    print(e)
                pass ## eww
                to_do = insert_statement + v_str + ')'
                print(to_do)
                cursor.execute(to_do)
                self.connection.commit()
            print('data inserted')
        pass


    def calc_fp(self, x):
        """
        Method that calculates 1/2 and full ppr fantasy points
        :param x:
        :return: {'half_ppr':value, 'full_ppr':value}
        """
        half_ppr = sum([x[i] * j for i, j in self.half_ppr.items()])
        full_ppr = sum([x[i] * j for i, j in self.full_ppr.items()])
        return ({'half_ppr': half_ppr, 'full_ppr': full_ppr, 'no_ppr': x['rec_yards'] * 0.1})


    def pull_player_year_season(self, year, player_name):
        """
        Method that will extract player and year data, aggregate up to _____ grain.
        :param year: list of years to pull player data against
        :param player_name: string player name to search for
        :return: data dict of player data - keyed by week, year
        """
        if type(year) != list:
            raise Exception("year parameter should be of type list, "\
                            "received type {}".format(str(type(year))))
        if type(player_name) != str:
            raise Exception("player_name parameter should be of type string, "\
                            "received type {}".format(str(type(player_name))))
        slug_name = slugify(player_name)
        query_str = """
        SELECT * from airyards where slug_name = {}
        """.format(slug_name)
        return(query_str)


    def pickformat(self, col, val):
        res = None
        if self.json_col_type[col] == str:
            res = "'{}'".format(str(val).replace("'",""))
        else:
            res = str(val)
        return(res)


    def sandbox_reception_leaders(self, year = 2017):
        '''
        Method that calculates aggregate 'rec_yards', 'air_yards', 'rec', 'tar', 'yac', 'tm_att' for a fixed year
        :param year: year number to query
        :return: none; csv is written to disk
        '''
        to_agg = ['rec_yards', 'air_yards', 'rec', 'tar', 'yac', 'tm_att']
        to_agg_str = ', '.join(['sum({}) as {}'.format(i, i) for i in to_agg])
        to_do = '''
        select
            slug_name,
            year,
            {0}
        from airyards
            where year = {1}
        group by slug_name, year
        order by rec_yards DESC, air_yards DESC
        '''.format(to_agg_str, year)

        hold = []
        with self.connection.cursor() as cursor:
            cursor.execute(to_do)
            # cols = [c[0].decode('utf8') for c in cursor.description]
            cols = [c[0] for c in cursor.description]
            # dat = cursor.fetchall()
            # i = 0
            for row in cursor:
                hold.append(dict(zip(cols, row)))
                # if i < 100:
                #    print(dict(zip(cols, row)))
                # i+=1
        return(pd.DataFrame(hold).to_csv(index=False))







