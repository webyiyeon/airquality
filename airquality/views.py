from django.shortcuts import render
from django.http import HttpResponse

import pandas as pd
import datetime
import pytz
import numpy as np

from sqlalchemy import desc, distinct, and_

from airquality.api import API
from airquality.geo import Geo
from airquality.utils import Utils
from airquality.conn import DBConnection
import airquality.models as models 

import time
from functools import reduce

db = DBConnection()
db.init_db()


# Create your views here.
# def index(request):
#     return HttpResponse("Hello, World!")

def index(request): 
    try:
        session = db.get_session()
        stime = time.time() # 소요시간 측정용
        _now = datetime.datetime.now(pytz.timezone('Asia/Seoul')) - datetime.timedelta(minutes=30)
        _yesterday = datetime.datetime.strftime(_now - datetime.timedelta(days=1), "%Y-%m-%d %H:00:00")
        _now = datetime.datetime.strftime(_now, "%Y-%m-%d %H:00:00")
        

        station_info = session.query(models.StationInfo).filter(models.StationInfo.use_yn == 'Y').all()
        df_station_info = pd.DataFrame([s.__dict__ for s in station_info])
        # 불필요한 열 제거 (예: SQLAlchemy에서 자동 생성된 열)
        df_station_info = df_station_info.drop('_sa_instance_state', axis=1)
        df_station_info["station_cd"] = df_station_info["station_cd"].astype('str')
        city_list = list(set(df_station_info["station_city"].to_list()))
        city_dist_dict = {}
        for i in range(0, len(city_list)):
            city_dist_dict[city_list[i]] = list(set(df_station_info.loc[df_station_info["station_city"] == city_list[i]]["station_dist"].to_list()))

        pollutant_kr = session.query(
            distinct(models.PollutantInfo.pltnt_cd), models.PollutantInfo.pltnt_kr
        ).all()
        pollutant_kr = [{pltnt_cd: pltnt_kr} for pltnt_cd, pltnt_kr in pollutant_kr]    

        air_quality = session.query(
            models.IndexNow, models.PollutantNow).join(
                models.PollutantNow,
                (models.IndexNow.datetime == models.PollutantNow.datetime) & 
                (models.IndexNow.station_cd == models.PollutantNow.station_cd)).filter(
                    models.IndexNow.datetime == _now).all()
        
        if not air_quality:
            # 데이터가 없을 경우 최근 데이터 조회
            air_quality = session.query(
                models.IndexNow, models.PollutantNow).join(
                    models.PollutantNow,
                    (models.IndexNow.datetime == models.PollutantNow.datetime) & 
                    (models.IndexNow.station_cd == models.PollutantNow.station_cd)).filter(
                        models.IndexNow.datetime <= _now).order_by(desc(models.PollutantNow.datetime)).all()
        
        _list = []
        
        index_now, pollutant_now = air_quality[0]
        
        _dict = {}
        _dict["key"] = 0
        _dict["station_cd"] = index_now.station_cd 
        _dict["CAI"] = round(index_now.CAI, 0)
        _dict.update(
            {
                "station_nm": df_station_info.loc[df_station_info["station_cd"] == index_now.station_cd]['station_nm'].reset_index(drop=True)[0],
                "latitude": df_station_info.loc[df_station_info["station_cd"] == index_now.station_cd]['latitude'].reset_index(drop=True)[0],
                "longitude": df_station_info.loc[df_station_info["station_cd"] == index_now.station_cd]['longitude'].reset_index(drop=True)[0],
                "pltnt_cd": index_now.pltnt_cd,
                "station_dist": df_station_info.loc[df_station_info["station_cd"] == index_now.station_cd]['station_dist'].reset_index(drop=True)[0],
                "station_city": df_station_info.loc[df_station_info["station_cd"] == index_now.station_cd]['station_city'].reset_index(drop=True)[0]
            }
        )
        _dict[pollutant_now.pltnt_cd] = pollutant_now.value
        
        for i in range(0, len(air_quality)-1):
            index_now, pollutant_now = air_quality[i]
            index_now2, pollutant_now2 = air_quality[i+1]

            if index_now.station_cd == index_now2.station_cd:
                if len(df_station_info.loc[df_station_info['station_cd']==index_now.station_cd]) == 0:
                    pass 
                else:
                    _dict.update(
                        {pollutant_now2.pltnt_cd: pollutant_now2.value}
                    )
            else:
                _list.append(_dict)
                if len(df_station_info.loc[df_station_info['station_cd']==index_now2.station_cd]) == 0:
                    pass 
                else:
                    _dict = {}
                    _dict["key"] = 0
                    _dict["station_cd"] = index_now2.station_cd 
                    _dict["CAI"] = round(index_now2.CAI, 0)
                    _dict[pollutant_now2.pltnt_cd] = pollutant_now2.value 
                    station_info = session.query(models.StationInfo).filter(models.StationInfo.station_cd == index_now2.station_cd)[0]
                    _dict.update(
                        {
                            "station_nm": station_info.station_nm,
                            "latitude": station_info.latitude,
                            "longitude": station_info.longitude,
                            "pltnt_cd": index_now.pltnt_cd,
                            "station_dist": station_info.station_dist,
                            "station_city": station_info.station_city
                        }
                    )
                
            if index_now.CAI == None:
                air_quality_temp = session.query(
                models.IndexNow, models.PollutantNow).join(
                    models.PollutantNow,
                    (models.IndexNow.datetime == models.PollutantNow.datetime) & 
                    (models.IndexNow.station_cd == models.PollutantNow.station_cd) &
                    (models.IndexNow.station_cd == index_now.station_cd) &
                    (models.IndexNow.CAI != 'null')
                        ).filter(
                        models.IndexNow.datetime < _now).order_by(desc(models.PollutantNow.datetime)).limit(1).all()

        result = _list

        # df = session.query(models.ForecastNow).filter(models.ForecastNow.datetime <= _now).all()
        df = pd.read_sql_query(
                sql = session.query(models.ForecastNow).filter((models.ForecastNow.datetime <= _now)&(models.ForecastNow.datetime > _yesterday)).statement,
                con = db.engine
            )
        df.rename(columns={"city_nm_kr":"city"}, inplace=True)
        
        forecast_ = {}
        # df, df_info = API.forecast_air(_now.split()[0])
        if len(df) != 0:
            # df = df.iloc[0:19]
            city_info = session.query(
                models.CityInfo.city_nm_kr, models.CityInfo.latitude, models.CityInfo.longitude
            ).all()
            df_city = pd.DataFrame(city_info).rename(columns={"city_nm_kr":"city"})
            df = pd.merge(df, df_city, on="city", how="outer").reset_index()
            # 가장 최근 날짜만 조회 
            latest_ = datetime.datetime.strftime(max(list(set(df["datetime"].to_list()))), "%Y-%m-%d %H:%M:%S")
            df["datetime"] = df["datetime"].astype("str")
            df = df.loc[df["datetime"]==latest_]
            df["inform_date"] = df["inform_date"].astype('str')
            grouped_dict_ = dict(iter(df.groupby('pltnt_cd')))

            for code in ["O3", "PM10", "PM25"]:
                forecast_[code] = dict(iter(grouped_dict_[code].groupby('inform_date')))
                for inform_date in list(forecast_[code].keys()):
                    forecast_[code][inform_date] = list(forecast_[code][inform_date].T.to_dict().values())
        else:
            pass
        
        df_info = pd.read_sql_query(
                sql = session.query(models.ForecastNowOverall).filter((models.ForecastNowOverall.datetime <= _now)&(models.ForecastNowOverall.datetime > _yesterday)).statement,
                con = db.engine
            )
        if len(df_info) != 0:
            df_info["inform_overall"] = df_info["inform_overall"].str.replace("'", "`")
            df_info["inform_cause"] = df_info["inform_cause"].str.replace("'", "`")
            df_info["datetime"] = df_info["datetime"].astype('str')
            df_info["inform_date"] = df_info["inform_date"].astype('str')
            df_info.reset_index(inplace=True)
            inform_ = list(df_info.T.to_dict().values())
        else:
            inform_ = []
        
        etime = time.time()
        print("소요시간:", etime - stime)
        
        return render(
            request, 
            'index.html', 
            {
                'air_quality': result, 
                'city_dist': city_dist_dict,
                'forecast': forecast_,
                'latest': latest_,
                'inform': inform_
                }
            )

    except Exception as e:
        print("Error", e)
        session.rollback()
        return render(request, 'error.html')

    finally:
        session.close()
    
from django.shortcuts import render
from django.shortcuts import render

def error_page(request):
  # 오류 메시지를 가져온다.
  error_message = request.META.get('HTTP_X_ERROR_MESSAGE', '')

  # 오류 페이지를 렌더링한다.
  context = {
    'error_message': error_message,
  }
  return render(request, 'error.html', context)
