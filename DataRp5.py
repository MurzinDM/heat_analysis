import re
import requests
import pandas as pd
import numpy as np
import io
import gzip
import urllib3
from exceptions import input_date
from datetime import timedelta
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

start_date, finish_date = input_date()


class HeatAnalysis():
    @staticmethod
    def get_frames():
        frame1 = DataRp5(start_date, finish_date).get_data_rp5()
        data2 = DataTGK(start_date, finish_date)
        data2.auth_tgk()
        frame2 = data2.get_devices_id()
        return frame1, frame2

    def concatenation_frames(self):
        frame1, frame2 = self.get_frames()
        frame = frame1.join(frame2)
        return print(frame)

    def upgreat_frame(self):
        pass


class HeatReport():
    pass


class GetData():
    def __init__(self, start_date=None, finish_date=None, devices_number=None):
        self.start_date = start_date
        self.finish_date = finish_date


class DataRp5(GetData):
    """
    Get and change data from https://rp5.ru/

    """

    def __init__(self, start_date=None, finish_date=None):
        super().__init__(start_date, finish_date)
        self.s = requests.Session()
        self.data = {'wmo_id': '26063',
                     'a_date1': self.start_date,
                     'a_date2': self.finish_date,
                     'f_ed3': '12',
                     'f_ed4': '12',
                     'f_ed5': '3',
                     'f_pe': '1',
                     'f_pe1': '1',
                     'lng_id': '2',
                     'type': 'xls'
                     }

    def change_frame_rp5(func):
        def inner_2(self, a=0, *args, **kwargs):
            frame = func(self)
            frame = frame.drop(frame.index[range(0, 7)])
            frame = frame.drop(frame[range(2, 29)], axis=1)
            frame = pd.DataFrame(frame.values, columns=['Дата', 'Температура'])
            frame = frame.sort_values(by=['Дата', 'Температура'], ascending='False').reset_index(drop='True')
            frame['Дата'] = pd.to_datetime(frame['Дата'])
            new_rows = pd.DataFrame({'Дата': [np.nan, np.nan], 'Температура': [np.nan, np.nan]}, index=[1, 2])
            for i in range(0, frame.index[-1]):
                i += a
                frame = pd.concat([frame.loc[:i], new_rows, frame.loc[i + 1:]], sort='False').reset_index(drop=True)
                frame.loc[i + 1, 'Дата'] = frame.loc[i, 'Дата'] + timedelta(hours=1)
                frame.loc[i + 2, 'Дата'] = frame.loc[i, 'Дата'] + timedelta(hours=2)
                inter = np.interp([1, 2], [0, 3], [frame.loc[i, 'Температура'], frame.loc[i + 3, 'Температура']])
                frame.loc[i + 1, 'Температура'] = round(inter[0], 1)
                frame.loc[i + 2, 'Температура'] = round(inter[1], 1)
                a += 2
            frame.set_index('Дата', inplace=True)
            return frame

        return inner_2

    def file_bytes_exel(func):
        def inner_1(self, *args, **kwargs):
            content = func(self)
            with gzip.open(io.BytesIO(content)) as f:
                frame = pd.read_excel(f, header=None)
            return frame

        return inner_1

    @change_frame_rp5
    @file_bytes_exel
    def get_data_rp5(self):
        s = requests.Session()
        response = s.get(url="https://rp5.ru/")

        response_2 = s.post(url="https://rp5.ru/responses/reFileSynop.php",
                            data=self.data,
                            headers={"Referer": "https://rp5.ru/", "X-Requested-With": "XMLHttpRequest"}
                            )
        data_rp5 = requests.get(re.findall(r'href=(.+?)>Скачать', response_2.text)[0])
        return data_rp5.content


class DataTGK(GetData):
    """
    Get and change data from https://portal.tgc1.ru

    """

    def __init__(self, start_date=None, finish_date=None):
        super().__init__(start_date, finish_date)
        self.devices_number = re.findall('\d{4,10}', str(input('Введите номера приборов: ')))
        self.data_type = 'daily' if str(input('Тип показаний(часовые, суточные)')).lower() == 'суточные' else 'hourly'
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
            if self.data_type == 'hourly':
                frame = pd.read_csv(io.BytesIO(content), encoding='cp1251', sep=';', parse_dates=[['Дата', 'Время']],
                                    index_col=0)
            else:
                frame = pd.read_csv(io.BytesIO(content), encoding='cp1251', sep=';', index_col=0)
            return frame

        return inner_4

    def change_frame_tgk(func):
        def inner_5(self):
            frame = func(self)
            frame = np.round(frame[['M1, т', 'M2, т', 't1, гр.C', 't2, гр.C', 'P1, кгс/см2', 'P2, кгс/см2']], 1)
            frame.index.names = ['Дата']
            return frame

        return inner_5

    @change_frame_tgk
    @get_frame_tgk
    @get_data_tgk
    def get_devices_id(self, a=0, devices_id=[], devices_info=''):
        while a < len(self.devices_number):
            myData = {'filter[DATE:dtfrom]': self.start_date, 'filter[DATE:dtto]': self.finish_date,
                      'filter[STRING:puserial]': self.devices_number[a], 'onpage': '1'}
            response = self.s.post('https://portal.tgc1.ru/directorate/archives',
                                   data=myData,
                                   verify=False
                                   ).text
            devices_info += str(BeautifulSoup(response, 'lxml').tbody)
            a += 1
        devices_id = re.findall('form/0/(.+?)' + '/' + self.start_date, devices_info)
        return devices_id


HeatAnalysis().concatenation_frames()
