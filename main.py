import pandas as pd
import re
import time
from functools import wraps
import os


def read_data_file(file_path: str) -> pd.DataFrame:
    with open(file_path, 'r') as f:
        raw_file = f.readlines()

    list_dados = [line.split() for line in raw_file]
    float_raw_lines = [list(map(float, raw_line)) for raw_line in list_dados]
    return pd.DataFrame(float_raw_lines, columns=['lat', 'long', 'data_value'])


def read_contour_file(file_path: str) -> pd.DataFrame:
    line_split_comp = re.compile(r'\s*,')

    with open(file_path, 'r') as f:
        raw_file = f.readlines()

    l_raw_lines = [line_split_comp.split(raw_file_line.strip()) for raw_file_line in raw_file]
    l_raw_lines = list(filter(lambda item: bool(item[0]), l_raw_lines))
    float_raw_lines = [list(map(float, raw_line))[:2] for raw_line in l_raw_lines]
    header_line = float_raw_lines.pop(0)
    assert len(float_raw_lines) == int(header_line[0])
    return pd.DataFrame(float_raw_lines, columns=['lat', 'long'])


def apply_contour(contour_df: pd.DataFrame, data_df: pd.DataFrame) -> pd.DataFrame:
    pass


def main() -> None:
    forecast_files_dir = './forecast_files'
    forecast_files = os.listdir(forecast_files_dir)
    forecast_files = [os.path.join(forecast_files_dir, it) for it in forecast_files]
    forecasted_date_pattern = re.compile(r'a(\d{6})\.dat')
    forecasted_dates = [forecasted_date_pattern.split(it)[1] for it in forecast_files]
    forecasted_dates = [pd.to_datetime(it, format='%d%m%y').strftime("%d/%m/%y") for it in forecasted_dates]

    data_df = pd.DataFrame()
    for filename, forecasted_date in zip(forecast_files, forecasted_dates):
        temp = read_data_file(filename)
        temp['forecasted_date'] = forecasted_date
        data_df = pd.concat([data_df, temp], axis=0)
    print(data_df.shape, data_df.head())
    # contour_df: pd.DataFrame = read_contour_file('PSATCMG_CAMARGOS.bln')
    # contour_df: pd.DataFrame = apply_contour(contour_df=contour_df, data_df=data_df)


if __name__ == '__main__':
    main()
