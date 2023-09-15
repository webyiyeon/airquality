
import dotenv 
import os 
import pandas as pd
import requests

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool
import pymysql

class DBConnection:
    def __init__(self):
        self.engine = None
        self.session = None  # 세션 추가
        
    def init_db(self):
        dotenv.load_dotenv()
        dbinfo = os.getenv("dbinfo")
        self.engine = create_engine(
            dbinfo,
            pool_size=4,
            pool_recycle=28800,
            pool_pre_ping=True
        )
        self.engine = self.engine.execution_options(isolation_level="AUTOCOMMIT")
        self.session = sessionmaker(autoflush=False, bind=self.engine)
        # self.session = Session()
    

        # try:
        #     connection = self.engine.connect()
        #     print("Connected to MySQL DB")
        #     connection.close()
        # except Exception as e:
        #     print("Failed to connect to MySQL DB", e)
        
    def get_session(self):
        return self.session()
    
    def get_db(self):
        '''
        요청마다 DB세션 유지 함수
        '''
        if self.session is None:
            raise Exception("must be called init_db")
        # db_session = None 
        try:
            self.session.commit()
        except:
            self.session.rollback()
        finally:
            self.session.close()
            
    # @property
    # def session(self):
    #     return self.get_db
    
    # @property
    # def engine(self):
    #     return self.engine

Base = declarative_base()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# class DBConnection:
#     def __init__(self, db_uri):
#         self.engine = create_engine(
#             db_uri,
#             pool_size=4,
#             pool_recycle=28800,
#             pool_pre_ping=True
#         )
#         self.Session = sessionmaker(autoflush=False, bind=self.engine)



# db_connection = DBConnection('your_database_uri_here')

# # 이제 각각의 요청에서 세션을 얻을 수 있습니다.
# db_session = db_connection.get_session()
# try:
#     # SQLAlchemy 세션을 사용한 작업 수행
#     # db_session.query(...)
#     db_session.commit()
# except Exception as e:
#     db_session.rollback()
# finally:
#     db_session.close()
