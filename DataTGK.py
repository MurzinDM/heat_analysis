import re
import requests
import pandas as pd
import numpy as np
import io
import urllib3
from bs4 import BeautifulSoup


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def frame_tgk():
    data = DataTGK('17.04.2020', '18.04.2020', ['52975'])
    data.auth_tgk()
    frame = data.get_devices_id()
    return frame


class DataTGK:
    """
    Get and change data from https://portal.tgc1.ru

    """

    def __init__(self):
        self.start_date = start_date
        self.finish_date = finish_date
        self.device_numbers = device_numbers
        self.data_type = 'hourly'
        self.s = requests.Session()

    def auth_tgk(self):
        auth = self.s.post("https://portal.tgc1.ru/auth/makeLogin",
                           {'login': 'user0016', 'password': 'Et7*6m_u1'},
                           verify=False
                           )

    def get_data_tgk(func):
        def inner_3(self):
            devices_id = func(self)
            url = "https://portal.tgc1.ru/directorate/archives/get/csv/0/" + devices_id[0] + "/" + \
                  self.start_date + "/" + self.finish_date + "/" + self.data_type
            response = self.s.get(url, verify=False)
            return response.content
        return inner_3

    def get_frame_tgk(func):
        def inner_4(self):
            content = func(self)
            frame = pd.read_csv(io.BytesIO(content), encoding='cp1251', sep=';', parse_dates=[['Дата', 'Время']],
                                index_col=0)
            return frame
        return inner_4

    def change_frame_tgk(func):
        def inner_5(self):
            frame = func(self)
            frame = np.round(frame[['M1, т', 'M2, т', 't1, гр.C', 't2, гр.C', 'P1, кгс/см2', 'P2, кгс/см2']], 1)
            return frame
        return inner_5

    @change_frame_tgk
    @get_frame_tgk
    @get_data_tgk
    def get_devices_id(self, a=0, devices_id=[], devices_info='') -> list:
        while a < len(self.device_numbers):
            myData = {'filter[DATE:dtfrom]': self.start_date, 'filter[DATE:dtto]': self.finish_date,
                      'filter[STRING:puserial]': self.device_numbers[a], 'onpage': '1'}
            response = self.s.post('https://portal.tgc1.ru/directorate/archives',
                                   data=myData,
                                   verify=False
                                   ).text
            devices_info += str(BeautifulSoup(response, 'lxml').tbody)
            a += 1
        devices_id = re.findall('form/0/(.+?)' + '/' + self.start_date, devices_info)
        return devices_id


print(frame_tgk())
