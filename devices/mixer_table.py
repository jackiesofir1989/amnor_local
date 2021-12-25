from math import isclose
from typing import List, Any, Tuple

from fastapi_utils.api_model import APIModel

from devices.schedule import Event


class MixerTable(APIModel):
    path: str
    ABS_TOLERANCE: int = 5  # how close the required value of PAR ro look for
    par: int = 0
    found_brightness: int = 100
    found_flag: bool = False
    top_rows: List[List[float]] = []
    freq_rows: List[List[float]] = []
    solve_list: List[float] = []

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.load_table()

    def load_table(self):
        import pandas as pd
        read_file = pd.read_excel(self.path)[1:]
        read_file.columns = [i for i in range(9)]
        read_file = read_file.loc[:, 1:]
        self.top_rows, self.freq_rows = read_file[:3].values.tolist(), read_file[3:].values.tolist()

    def get_output_light_vector(self, input_light_vector: List[int], brightness: int) -> Tuple[list[int], float]:
        """calculate the vector,PAR as tuple if the brightness is zero, returns zeros.
         else values between 1-1000 are in order"""
        m_val = max(input_light_vector)
        n_b = brightness / 100  # brightness normalized
        self.solve_list = self.calc_solve_list(input_light_vector, m_val, n_b)
        if brightness <= 0:
            output_light_vector, par = [0 for _ in range(8)], 0.0
            return output_light_vector, par
        output_light_vector = [round(self.calc_it(m_val, value) * n_b) for value in input_light_vector]
        return output_light_vector, self.get_par()

    def calc_solve_list(self, input_light_vector: List[int], m_val: int, n_b: float) -> List[float]:
        """Some bullshit from eyal table calculations"""
        s_l = []
        for row in self.freq_rows:
            value = 0.0
            for i, cell in enumerate(row):
                if not cell:
                    continue
                a, b, c = self.top_rows[0][i], self.top_rows[1][i], self.top_rows[2][i]
                if m_val:
                    _l = self.calc_it(m_val, input_light_vector[i]) * n_b / 1000
                else:
                    _l = 0
                x = _l * a
                y = ((1 - _l) * b) + 1
                value += cell * x * y / c
            s_l.append(self.round_3_digit(value))
        return s_l

    @staticmethod
    def calc_it(m_val, val) -> float:
        try:
            return ((100 / m_val) * val) * 10
        except ZeroDivisionError:
            return 0

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
        # print('BRIGHTNESS', event, sensor_light_moles, self.found_brightness, self.par)
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
    def round_3_digit(value) -> float:
        return round(value, 4)

    def get_par_ratio(self, start_cell: int, end_cell: int) -> float:
        s, e = start_cell - 8, end_cell - 7
        # print(s, e, start_cell, end_cell)
        l_list = self.solve_list[s: e]
        # print(l_list, len(l_list))
        return self.round_3_digit(sum(l_list))

    def calc_solve_log(self, rx_values: List[int], blink_values: List[int]) -> List[float]:
        """Some bullshit from eyal table calculations"""
        # logging.warning(self.freq_rows, rx_values, blink_values)
        s_l = []
        for row in self.freq_rows:
            value = 0.0
            for i, cell in enumerate(row):
                if not cell or not rx_values[i] or not blink_values[i]:
                    continue
                a, b, c = self.top_rows[0][i], self.top_rows[1][i], self.top_rows[2][i]
                value += (cell * ((rx_values[i] / 1000) * a * (((1 - (rx_values[i] / 1000)) * b) + 1)) / c) * (blink_values[i] / 100)
                # _l = rx_values[i] / 1000
                # x = _l * a
                # y = ((1 - _l) * b) + 1
                # value += cell * x * y / c * blink_values[i] / 100
            s_l.append(self.round_3_digit(value))
        return s_l

    def get_total_power_consumption(self, rx_values: List[int], blink_values: List[int], voltage_values: List[float],
                                    max_current_values: List[int]) -> float:
        self.solve_list = self.calc_solve_log(rx_values, blink_values)
        # print(self.solve_list)
        total_watt = 0.0
        for i in range(8):
            total_watt += voltage_values[i] * rx_values[i] * max_current_values[i] * blink_values[i] / 100_000_000
        total_watt = total_watt * 1.04
        return self.round_3_digit(total_watt)

    def get_total_photon_flux_output(self) -> float:
        return self.get_par_ratio(8, 88)

    def get_par(self) -> float:
        return self.get_par_ratio(12, 72)

    def get_photon_efficiency(self, total_watt: float, total_photon_flux: float) -> float:
        try:
            return self.round_3_digit(total_photon_flux / total_watt)
        except ZeroDivisionError:
            return 0

    def get_avg_ppfd_in_corons(self, par: float) -> float:
        return self.round_3_digit(par * 0.94)

    def get_color_ratio(self, par: float, start_cell: int, end_cell: int) -> float:
        try:
            return self.round_3_digit(self.get_par_ratio(start_cell, end_cell) / par)
        except ZeroDivisionError:
            return 0

    def get_blue_ratio(self, par: float) -> float:
        return self.get_color_ratio(par, 12, 32) * 100

    def get_green_ratio(self, par: float) -> float:
        return self.get_color_ratio(par, 33, 51) * 100

    def get_red_ratio(self, par: float) -> float:
        return self.get_color_ratio(par, 52, 72) * 100

    def get_far_red_ratio(self, par: float) -> float:
        return self.get_color_ratio(par, 73, 88) * 100

    def get_red_blue_ratio(self, red: float, blue: float) -> float:
        try:
            return self.round_3_digit(red / blue)
        except ZeroDivisionError:
            return 0

    def get_red_far_red_ratio(self, red: float, far_red: float) -> float:
        try:
            return self.round_3_digit(red / far_red)
        except ZeroDivisionError:
            return 0

    def get_red_far_red_to_blue_ratio(self, red: float, far_red: float, blue: float) -> float:
        try:
            return self.round_3_digit((red + far_red) / blue)
        except ZeroDivisionError:
            return 0
