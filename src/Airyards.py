import json
import requests
import psycopg2
from .DBConnect import DBConnect
from slugify import slugify
import pandas as pd


class Airyards(DBConnect):

    json_cols = [ 'player_id', 'full_name', 'slug_name', 'team', 'position',
                  'week', 'rec', 'tar', 'rec_yards', 'air_yards', 'racr',
                  'yac', 'td', 'ms_air_yards', 'team_air', 'target_share',
                  'tm_att', 'aypt', 'wopr', 'rush_td',  'rush_yards', 'year'] ## need a list to preserve order

    str_cols = ['player_id', 'full_name', 'slug_name', 'team', 'position'] ##string columns
    float_cols = ['racr', 'tm_att', 'ms_air_yards', 'target_share', 'wopr',
                  'aypt', 'team_air'] ## float columns
    cols = str_cols + float_cols
    int_cols = set(json_cols) - set(cols) ## int columns (the rest)

    json_col_type = {i: str for i in str_cols}
    json_col_type.update({i: float for i in float_cols})
    json_col_type.update({i: int for i in int_cols})

    half_ppr = {'rec_yards': 0.1, 'rec': 0.5} ## deprecated attribute
    full_ppr = {'rec_yards': 0.1, 'rec': 1} ## deprecated attribute

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
                '"player_id" varchar(100) COLLATE "default",' \
                '"full_name" varchar(100) COLLATE "default",' \
                '"slug_name" varchar(100) COLLATE "default",' \
                '"team" varchar(100) COLLATE "default",' \
                '"position" varchar(100) COLLATE "default",' \
                '"week" int4 NOT NULL,' \
                '"rec" int4,' \
                '"tar" int4,' \
                '"rec_yards" int4,' \
                '"air_yards" int4,' \
                '"racr" FLOAT,' \
                '"yac" int4,' \
                '"td" int4,' \
                '"ms_air_yards" FLOAT,' \
                '"team_air" FLOAT,' \
                '"target_share" FLOAT,' \
                '"tm_att" FLOAT,' \
                '"aypt" FLOAT,' \
                '"wopr" FLOAT,' \
                '"rush_td" int4,' \
                '"rush_yards" int4,'\
                '"year" int4 NOT NULL);'
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
            ##d.update(self.calc_fp(d)) ## no longer calculating fantatsy pts


    def insert_into_db(self, data_json):
        if data_json in [None, []]:
            msg = 'No Data Received...'
            raise Exception(msg)
        else:
            self.check_data_json_cols()
            insert_statement = 'INSERT INTO airyards (player_id, '\
                               'full_name, '\
                               'slug_name, '\
                               'team, '\
                               'position, '\
                               'week, '\
                               'rec, '\
                               'tar, '\
                               'rec_yards, '\
                               'air_yards, '\
                               'racr, '\
                               'yac, '\
                               'td, '\
                               'ms_air_yards, '\
                               'team_air, '\
                               'target_share, '\
                               'tm_att, '\
                               'aypt, '\
                               'wopr, '\
                               'rush_td, '\
                               'rush_yards, '\
                               'year) VALUES ('
        with self.connection.cursor() as cursor:
            for x in data_json:
                print('Inserting {}'.format(x['full_name']))
                v_str = ','.join([self.pickformat(i, x[i]) for i in self.json_cols])
                to_do = insert_statement + v_str + ')'
                print(to_do)
                cursor.execute(to_do)
                self.connection.commit()
            print('data inserted')
        pass


    def calc_fp(self, x):
        """
        Method that calculates 1/2 and full ppr fantasy points -- method no longer used !!!
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


    def check_data_json_cols(self):
        """
        Method that checks to make sure all of self.json_cols are in self.data_json (will only check 1st record)
        :param self:
        :return: None
        """
        missing_fields = set(self.json_cols) - set(self.data_json[0].keys())
        if len(missing_fields) > 0:
            msg = 'Json Data is missing fields: {}'.format(' ,'.join(missing_fields))
            raise Exception(msg)
        pass


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







