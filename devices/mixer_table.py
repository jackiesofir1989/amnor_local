import logging
from math import isclose
from typing import List, Any, Tuple
import pandas as pd
from fastapi_utils.api_model import APIModel

from devices.schedule import Event


class MixerTable(APIModel):
    path: str
    ABS_TOLERANCE: int = 5  # how close the required value of PAR ro look for
    par: int = 0
    found_brightness: int = 100
    found_flag: bool = False
    top_df: pd.DataFrame = None
    freq_df: pd.DataFrame = None
    df: pd.DataFrame = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.load_table()
        # print(self.df)

    def load_table(self):
        self.df = pd.read_excel(self.path)
        self.df = self.df.iloc[1:, 1:9]
        self.df.columns = [i for i in range(len(self.df.columns))]
        self.df.reset_index(drop=True, inplace=True)
        self.top_df, self.freq_df = self.df[:3], self.df[3:]
        self.freq_df.reset_index(drop=True, inplace=True)
        # print(self.freq_df, self.top_df)

    def get_output_light_vector(self, input_light_vector: List[int], brightness: int) -> Tuple[list[int], float]:
        """calculate the vector,PAR as tuple if the brightness is zero, returns zeros.
         else values between 1-1000 are in order"""
        if input_light_vector == [0, 0, 0, 0, 0, 0, 0, 0]:
            return input_light_vector, 0.0
        max_ilv: float = 100 / max(input_light_vector)
        norm_b = (brightness / 100)
        # logging.critical(f'\n{input_light_vector}\n{brightness}\n')
        t = self.calc_freq_table(self.freq_df.copy(), self.top_df, input_light_vector, max_ilv, norm_b)
        # logging.critical(f'\n{t}')
        output_light_vector = [self.norm(max_ilv, v, norm_b) for v in input_light_vector]
        # logging.critical(f'\n{output_light_vector}\n{self.calc_par(t)}')
        return output_light_vector, self.calc_par(t)

    def calc_freq_table(self, _freq_df: pd.DataFrame, _top_df: pd.DataFrame, _ilv: List[int], max_ilv: int, _norm_b: float) -> pd.DataFrame:
        a = []
        for rowIndex, row in _freq_df.iterrows():
            val = 0.0
            cI: int
            for cI, value in row.items():
                x = self.norm(max_ilv, _ilv[cI], _norm_b) / 1000
                y = _top_df[cI]
                val += value * x * y[0] * (((1 - x) * y[1]) + 1) / y[2]
            a.append(val)
        _freq_df.insert(8, 8, a)
        return _freq_df

    @staticmethod
    def norm(_max_ilv, val, _norm_b) -> int:
        return ((_max_ilv * val) * 10) * _norm_b

    @staticmethod
    def calc_par(_freq_df) -> float:
        offset, row_count = 5, 59
        a = _freq_df.loc[offset: offset + row_count, 8]
        return sum(a)

    def get_brightness(self, event: Event, sensor_light_moles: float) -> int:
        """this returns the wanted brightness value, if the desired minus the measured value is equal or less than zero return 0,
        else use the binary search to find the value"""
        self.found_flag = False
        self.found_brightness = 100
        par_wanted = event.moles_desired - sensor_light_moles
        olv, par = self.get_output_light_vector(event.colors, 100)
        if par_wanted <= 0:
            """if the measured moles is bigger then the desired one turn off the lamps"""
            return 0
        elif par <= par_wanted:
            """if the maximum par is smaller then the wanted one send lamp to max"""
            return 100
        else:
            self.binary_search(event, 0, 100, par_wanted)
        logging.critical(f'{event}, Sensor PPFD: {sensor_light_moles}, Brightness: {self.found_brightness}, Par: {self.par}')
        return self.found_brightness

    def binary_search(self, event: Event, start_value: int, end_value: int, par_wanted: float):
        """This recursive function will look the closest brightness value to desired surface uMoles value"""
        middle = (start_value + end_value) // 2
        self.found_brightness = middle
        if middle == 100:
            self.found_flag = True
        if self.found_flag or self.found_brightness <= 0:
            return self.found_brightness
        olv, par = self.get_output_light_vector(event.colors, middle)
        par = round(par)
        self.par = par
        if isclose(par, par_wanted, abs_tol=self.ABS_TOLERANCE):
            self.found_flag = True
        elif par < par_wanted:
            self.binary_search(event, middle + 1, end_value, par_wanted)
        else:
            self.binary_search(event, start_value, middle - 1, par_wanted)

    @staticmethod
    def calc_solve_log(_freq_df: pd.DataFrame, _top_df: pd.DataFrame, _data: pd.DataFrame) -> pd.DataFrame:
        a = []
        for rowIndex, row in _freq_df.iterrows():
            val = 0.0
            cI: int
            for cI, value in row.items():
                x = _data.loc['RxLight', :][cI] / 1000
                y = _top_df[cI]
                val += value * x * y[0] * (((1 - x) * y[1]) + 1) / y[2] * _data.loc['Blink', :][cI] / 100
            a.append(val)
        _freq_df.insert(8, 8, a)
        return _freq_df

    def get_mixer_table_calc(self, rx_values: List[int], blink_values: List[int], voltage_values: List[float], max_current_values: List[int]) -> pd.DataFrame:
        input_data = pd.DataFrame([rx_values, blink_values, voltage_values, max_current_values], index=['RxLight', 'Blink', 'Voltage', 'MaxCurrent'])
        t2 = self.calc_solve_log(self.freq_df.copy(), self.top_df, input_data)
        return self.calc_params(t2, input_data)

    def calc_params(self, _freq_df: pd.DataFrame, _input_data: pd.DataFrame) -> pd.DataFrame:
        FixturePowerConsumption = self.calc_fpc(_input_data)
        TotalFixturePhotonFluxOutput = sum(_freq_df.loc[:, 8])
        FixturePAROutput = sum(_freq_df.loc[4:64, 8])
        if FixturePowerConsumption:
            FixturePhotonEfficacy = TotalFixturePhotonFluxOutput / FixturePowerConsumption
        else:
            FixturePhotonEfficacy = 0
        AvgPPFDFromOneMeter = FixturePAROutput * 0.94
        if FixturePAROutput:
            BlueToPar = sum(_freq_df.loc[4:24, 8]) / FixturePAROutput * 100
            GreenToPar = sum(_freq_df.loc[25:43, 8]) / FixturePAROutput * 100
            RedToPar = sum(_freq_df.loc[44:64, 8]) / FixturePAROutput * 100
            FarRedToPar = sum(_freq_df.loc[65:80, 8]) / FixturePAROutput * 100
            if BlueToPar:
                RedToBlue = RedToPar / BlueToPar
                RedToFarRed = RedToPar / FarRedToPar
                RedAndFarRedToBlue = (RedToPar + FarRedToPar) / BlueToPar
            else:
                RedToBlue = 0
                RedToFarRed = 0
                RedAndFarRedToBlue = 0
        else:
            BlueToPar = 0
            GreenToPar = 0
            RedToPar = 0
            FarRedToPar = 0
            RedToBlue = 0
            RedToFarRed = 0
            RedAndFarRedToBlue = 0

        _d = {
            'FixturePowerConsumption': [FixturePowerConsumption],
            'TotalFixturePhotonFluxOutput': [TotalFixturePhotonFluxOutput],
            'FixturePAROutput': [FixturePAROutput],
            'FixturePhotonEfficacy': [FixturePhotonEfficacy],
            'AvgPPFDFromOneMeter': [AvgPPFDFromOneMeter],
            'BlueToPar': [BlueToPar],
            'GreenToPar': [GreenToPar],
            'RedToPar': [RedToPar],
            'FarRedToPar': [FarRedToPar],
            'RedToBlue': [RedToBlue],
            'RedToFarRed': [RedToFarRed],
            'RedAndFarRedToBlue': [RedAndFarRedToBlue],
            }
        return pd.DataFrame(_d)

    @staticmethod
    def calc_fpc(_data: pd.DataFrame) -> float:
        val = 0.0
        _data = _data.iloc[:, :8]
        for cI, items in _data.items():
            val += (items.Voltage * ((items.RxLight / 1000) * items.MaxCurrent / 1000)) * (items.Blink / 100)
        return val * 1.04
