
import datetime
import pandas as pd
import numpy as np
from typing import List, Union
from urllib.parse import urlparse, ParseResult

class Utils:
    @staticmethod
    def print_map_type(df):
        df = df.T
        df.fillna(0,inplace=True)
        dict_temp = df.to_dict()
        result = list(dict_temp.values())

        return result