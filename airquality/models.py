from django.db import models

# Create your models here.
from airquality.conn import Base 
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Float, String, DateTime

class StationInfo(Base):
    __tablename__ = 'station_info'
    station_cd = Column(String, primary_key=True)
    station_nm = Column(String)
    station_adr = Column(String)
    station_dist = Column(String)
    station_city = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    use_yn = Column(String)
    
class PollutantInfo(Base):
    __tablename__ = 'pollutant_info'
    pltnt_nm = Column(String)
    pltnt_unit = Column(String)
    pltnt_cd = Column(String, primary_key=True)
    credit_hr = Column(Integer)
    cncnt_type = Column(String, primary_key=True)
    cncnt_value = Column(Float)
    status_level = Column(String)
    status_cd = Column(String, primary_key=True)
    pltnt_kr = Column(String)
    status_level_eng = Column(String)
    
class PollutantNow(Base):
    __tablename__ = 'pollutant_now'
    station_cd = Column(String, primary_key=True)
    datetime = Column(DateTime, primary_key=True)
    pltnt_cd = Column(String, primary_key=True)
    value = Column(Float)
    
class IndexNow(Base):
    __tablename__ = 'index_now'
    station_cd = Column(String, primary_key=True)
    datetime = Column(DateTime, primary_key=True)
    CAI = Column(Float)
    pltnt_cd = Column(String)
    level = Column(String)
    
class CityInfo(Base):
    __tablename__ = 'city_info'
    nation = Column(String, primary_key=True)
    city_nm = Column(String, primary_key=True)
    city_nm_kr = Column(String, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    use_yn = Column(String)
    