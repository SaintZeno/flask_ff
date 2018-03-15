import json
import requests
import psycopg2
from .DBConnect import DBConnect
from slugify import slugify
from .Airyards import Airyards
import pandas as pd

ay = Airyards(year=2017)

to_agg = ['rec_yards', 'air_yards', 'rec', 'tar', 'yac', 'tm_att']
to_agg_str = ', '.join(['sum({}) as {}'.format(i, i) for i in to_agg])
to_do =  '''
select
    slug_name,
    year,
    {0}
from airyards
    where year = {1}
group by slug_name, year
order by rec_yards DESC, air_yards DESC
'''.format(to_agg_str, ay.year)

hold = []
with ay.connection.cursor() as cursor:
    cursor.execute(to_do)
    #cols = [c[0].decode('utf8') for c in cursor.description]
    cols = [c[0] for c in cursor.description]
    #dat = cursor.fetchall()
    #i = 0
    for row in cursor:
        hold.append(dict(zip(cols, row)))
        #if i < 100:
        #    print(dict(zip(cols, row)))
        #i+=1
    temp = pd.DataFrame(hold)#.to_csv(index=False)

