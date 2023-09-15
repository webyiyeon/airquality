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
session = db.get_session()

# Create your views here.
# def index(request):
#     return HttpResponse("Hello, World!")

def index(request): 
    try:
        stime = time.time() # 소요시간 측정용
        _now = datetime.datetime.strftime(datetime.datetime.now(pytz.timezone('Asia/Seoul')) - datetime.timedelta(minutes=30), "%Y-%m-%d %H:00:00")

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

        df, df_info = API.predict_air(_now.split()[0])
        if len(df) != 0:
            df = df.iloc[0:19]
            city_info = session.query(
                models.CityInfo.city_nm_kr, models.CityInfo.latitude, models.CityInfo.longitude
            ).all()
            df_city = pd.DataFrame(city_info).rename(columns={"city_nm_kr":"city"})
            df = pd.merge(df, df_city, on="city", how="outer").reset_index()
            predict_ = list(df.T.to_dict().values())
        else:
            predict_ = []
        
        if len(df_info) != 0:
            df_info["informOverall"] = df_info["informOverall"].str.replace("'", "`")
            df_info.reset_index(inplace=True)
            inform_ = list(df_info.T.to_dict().values())
        else:
            inform_ = []
        
        etime = time.time()
        print("소요시간:", etime - stime)
        session.close()
        return render(
            request, 
            'index.html', 
            {
                'air_quality': result, 
                'city_dist': city_dist_dict,
                'predict': predict_,
                'inform': inform_
                }
            )
    
    except Exception as e:
        print("Failed to connect to MySQL DB", e)
        return render(request, 'error.html')
    
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
