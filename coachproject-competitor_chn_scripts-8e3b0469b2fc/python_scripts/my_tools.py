#!/usr/bin/env python
# encoding: utf-8
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
import sys
#from configparser import ConfigParser

#from pandas import read_sql, DataFrame
#from urllib import parse
#from pathlib import Path
#from sqlalchemy.engine import create_engine, url
#from sqlalchemy import text


### please add database connector here

###settings###
# config = ConfigParser()
# config.read('config.ini')
# db_user = config.get('whateverdatabase', 'USER')
# db_password = config.get('whateverdatabase', 'PASSWORD')


###tools###
def get_ts():
    return datetime.now().replace(day=1)-timedelta(days=1)

def get_rolling_months_list(dt,n):
    month_list = [(dt-relativedelta(months=i)).strftime("%Y-%m").replace('-','') for i in range(1,n+1)]
    return month_list
