import dotenv 
import os 
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from functools import reduce 
from lxml import etree

class API:
    def air_list():
        dotenv.load_dotenv()
        decoding_key = os.getenv("decode_key")
        params ={'serviceKey' :decoding_key, 'pageNo' : '1', 'numOfRows' : '20' }
        url = os.getenv("ulsan_air_list")
        response = requests.get(url, params=params)
        root = ET.fromstring(response.content)
        # XML 데이터에서 필요한 정보 추출하여 DataFrame 만들기
        df = pd.DataFrame([
            {tag.tag: tag.text for tag in subsubchild}
            for child in root.findall('body')
            for subchild in child.findall('data')
            for subsubchild in subchild.findall('list')
        ])
        # 문자열 변환하기
        df = pd.DataFrame(df.applymap(lambda x: x.strip() if isinstance(x, str) else x))
        # print(df)
        df["CODE"] = df["CODE"].str.strip().astype('int')
        df["NAME"] = df["NAME"].str.strip()
        # df["CODE"] = df["CODE"]
        
        return df
    
    def air_korea():
        df = pd.read_csv("airquality/air_code_result.csv")
        df.rename(columns={
            "지역구":"region", 
            "도시": "city",
            "측정소코드": "CODE",
            "측정소명": "NAME",
            "주소": "address"
            }, inplace=True)
        df.drop(columns="NAME", inplace=True)
        return df
    
    def air_quality(city_code:str, start_date:str, end_date:str):
        dotenv.load_dotenv()
        decoding_key = os.getenv("decode_key")
        url = 'http://apis.data.go.kr/6310000/ulsanair/getUlsanairView'
        params = {
            "numOfRows":1, 
            "pageNo":1, 
            "serviceKey":decoding_key, 
            "city":city_code, 
            "sdate":start_date, 
            "edate":end_date
        }
        response = requests.get(url, params=params)
        root = ET.fromstring(response.content)
        # XML 데이터에서 필요한 정보 추출하여 DataFrame 만들기
        data = [
            {tag.tag: tag.text for tag in subsubchild}
            for child in root.findall('body')
            for subchild in child.findall('data')
            for subsubchild in subchild.findall('list')
        ]
        df = pd.DataFrame(data)
        if len(df)!=0:
            # 문자열 변환하기
            old_string = '\t'
            new_string = ''
            for col in list(df.columns):
                df[col] = df[col].apply(lambda x: x.replace(old_string, new_string))
            df['PLACE'] = df['PLACE'].str.strip()
            success = True
            result = df
        else:
            success = False
            result = []
        return success, result
    
    def predict_air(searchDate:str):
        try:
            dotenv.load_dotenv()
            decoding_key = os.getenv("decode_key")
            url = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMinuDustFrcstDspth'
            params ={
                'serviceKey' : decoding_key, 
                'returnType' : 'xml', 
                'searchDate' : searchDate, 
                'ver': 1.1
                }
            response = requests.get(url, params=params)
            xml = BeautifulSoup(response.text, features="xml")
            def convert_string(item, key):
                try:
                    return item.find(key).text.strip()
                except AttributeError:
                    return None 

            items = xml.findAll("item")
            item_list = []

            for item in items:
                item_dict = {
                    "dataTime": convert_string(item, "dataTime"),
                    "informCode": convert_string(item, "informCode"),
                    "informOverall": convert_string(item, "informOverall"),
                    "informCause": convert_string(item, "informCause"),
                    "informGrade": convert_string(item, "informGrade"),
                    "actionKnack": convert_string(item, "actionKnack"),
                    "imageUrl1": convert_string(item, "imageUrl1"),
                    "imageUrl2": convert_string(item, "imageUrl2"),
                    "imageUrl3": convert_string(item, "imageUrl3"),
                    "imageUrl4": convert_string(item, "imageUrl4"),
                    "imageUrl5": convert_string(item, "imageUrl5"),
                    "imageUrl6": convert_string(item, "imageUrl6"),
                    "imageUrl7": convert_string(item, "imageUrl7"),
                    "imageUrl8": convert_string(item, "imageUrl8"),
                    "imageUrl9": convert_string(item, "imageUrl9"),
                    "informData": convert_string(item, "informData")
                }
                item_list.append(item_dict)
            df = pd.DataFrame(item_list)
            df_grade = []
            for i in range(0, len(df)):
                data = df.iloc[i]["informGrade"]
                
                data_dict = {}
                data_dict["city"] = []
                data_dict["grade"] = []
                for item in data.split(","):
                    city, grade = item.split(" : ")
                    data_dict["city"].append(city)
                    data_dict["grade"].append(grade)
                df_temp = pd.DataFrame(data_dict)
                df_temp["dataTime"] = df.iloc[i]["dataTime"]
                df_temp["informData"] = df.iloc[i]["informData"]
                df_temp["informCode"] = df.iloc[i]["informCode"]
                
                df_grade.append(df_temp)

            df.drop(columns=["informGrade"], inplace=True)
            df_grade_merge = reduce(lambda left, right: pd.merge(left, right, on=['dataTime', 'informData', 'city', 'grade', 'informCode'], how='outer'), df_grade)
            
            return df_grade_merge, df
    
        except Exception as e:
            return [], []
        