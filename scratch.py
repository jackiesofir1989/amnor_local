from typing import List

import pandas as pd

df: pd.DataFrame = pd.read_excel('/home/jackie/PycharmProjects/app/MixerTableExcels/MixerTable.xlsx')
df = df.iloc[1:, 1:9]
df.columns = [i for i in range(len(df.columns))]
df.reset_index(drop=True, inplace=True)
top_df, freq_df = df[:3], df[3:]
freq_df.reset_index(drop=True, inplace=True)

ilv = [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000]
if ilv == [0, 0, 0, 0, 0, 0, 0, 0]:
    max_ilv = 0
else:
    max_ilv = (100 / max(ilv))

b = 100
norm_b = (b / 100)


def norm(_max_ilv, val, _norm_b) -> float:
    return ((_max_ilv * val) * 10) * _norm_b


def calc_freq_table(_freq_df: pd.DataFrame, _top_df: pd.DataFrame, _ilv: List[int], _norm_b: float) -> pd.DataFrame:
    a = []
    for rowIndex, row in _freq_df.iterrows():
        val = 0.0
        cI: int
        for cI, value in row.items():
            x = norm(max_ilv, _ilv[cI], _norm_b) / 1000
            y = _top_df[cI]
            val += value * x * y[0] * (((1 - x) * y[1]) + 1) / y[2]
        a.append(val)
    _freq_df.insert(8, 8, a)
    return _freq_df


def clac_PAR(_freq_df) -> float:
    offset, row_count = 5, 59
    a = _freq_df.loc[offset: offset + row_count, 8]
    return sum(a)


t = calc_freq_table(freq_df.copy(), top_df, ilv, norm_b)
print(t)
print([norm(max_ilv, v, (b / 100)) for v in ilv])
print(clac_PAR(t))

data = [[1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000],
        [100, 100, 100, 100, 100, 100, 100, 100],
        [0.0, 36.8, 0.0, 0.0, 0.0, 36.7, 0.3, 36.8, 48.3, 3.3],
        [1400, 1400, 1400, 1400, 1400, 1400, 1400, 1400]]
input_data = pd.DataFrame(data, index=['RxLight', 'Blink', 'Voltage', 'MaxCurrent'])
print(input_data)


def calc_inc_freq_table(_freq_df: pd.DataFrame, _top_df: pd.DataFrame, _data: pd.DataFrame) -> pd.DataFrame:
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


t2 = calc_inc_freq_table(freq_df, top_df, input_data.copy())
print(t2)


def clac_fpc(_data: pd.DataFrame) -> float:
    val = 0.0
    _data = _data.iloc[:, :8]
    for cI, items in _data.items():
        val += (items.Voltage * ((items.RxLight / 1000) * items.MaxCurrent / 1000)) * (items.Blink / 100)
    return val * 1.04


def clac_params(_freq_df: pd.DataFrame, _input_data: pd.DataFrame) -> pd.DataFrame:
    FixturePowerConsumption = clac_fpc(_input_data)
    TotalFixturePhotonFluxOutput = sum(_freq_df.loc[:, 8])
    FixturePAROutput = sum(_freq_df.loc[4:64, 8])
    FixturePhotonEfficacy = TotalFixturePhotonFluxOutput / FixturePowerConsumption
    AvgPPFDFromOneMeter = FixturePAROutput * 0.94
    BlueToPar = sum(_freq_df.loc[4:24, 8]) / FixturePAROutput * 100
    GreenToPar = sum(_freq_df.loc[25:43, 8]) / FixturePAROutput * 100
    RedToPar = sum(_freq_df.loc[44:64, 8]) / FixturePAROutput * 100
    FarRedToPar = sum(_freq_df.loc[65:80, 8]) / FixturePAROutput * 100
    RedToBlue = RedToPar / BlueToPar
    RedToFarRed = RedToPar / FarRedToPar
    RedAndFarRedToBlue = (RedToPar + FarRedToPar) / BlueToPar

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


print(clac_params(t2, input_data).to_string())
