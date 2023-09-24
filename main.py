import sys

import pandas as pd
import re
import time
from functools import wraps
import os
import geopandas as gpd
from shapely import Point, Polygon
import seaborn as sns
import matplotlib.pyplot as plt


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
    """
    Converte as coordenadas de data_df em objetos do tipo Point, as coordenadas de contour_df em objeto Polygon
    Seleciona e retorna data_df apenas os pontos que estão dentro do polígono de contour_df.
    :param contour_df:
    :param data_df:
    :return: data_df pd.DataFrame
    """
    contour_geometry = Polygon(contour_df[['lat', 'long']].values)
    data_df = gpd.GeoDataFrame(
        data_df, crs='EPSG:4326',
        geometry=[Point(coord) for coord in zip(data_df['lat'], data_df['long'])]
    )
    data_df = data_df.loc[data_df['geometry'].within(contour_geometry), :]
    return pd.DataFrame(data_df)


def plot_accumulated_precipitation(data_df: pd.DataFrame, x='forecasted_date', y='data_value') -> None:
    """
    Recebe dados de previsão de precipitação da área de interesse já agrupados por dia previsto.
    Calcula a soma cumulativa e plota em dois eixos, barras e linhas, a precipitação diária e acumulada do preríodo.
    :param data_df:
    :param x: período previsto (dd/mm/yy)
    :param y: valor de precipitação previsto
    :return: exporta gráfico
    """
    data_df['cumsum'] = data_df[y].cumsum()

    _ = sns.set(style='whitegrid', font_scale=1)
    ax1 = sns.barplot(x=data_df[x], y=data_df[y], color='orange', alpha=0.2)
    ax1.set_xlabel('Dia previsto')
    ax1.set_ylabel('Precipitacao Diária (mm)', fontdict={'family': 'sans-serif', 'size': 10}, labelpad=20.0)
    ax1.set_xticks(data_df[x])
    ax1.set_xticklabels(data_df[x], va='center', rotation=45, size=10, fontdict={'family': 'sans-serif', 'size': 8})
    ax1.yaxis.grid(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['top'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)

    ax2 = ax1.twinx()
    _ = sns.lineplot(x=data_df[x], y=data_df['cumsum'], color='orange', linestyle='-', linewidth=2, marker='o',
                     markersize=5, ax=ax2)
    ax2.set_ylabel('Precipitação Acumulada (mm)', fontdict={'family': 'sans-serif', 'size': 10}, labelpad=20.0)
    ax2.yaxis.grid(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)

    [ax2.text(data_df.at[i, 'forecasted_date'], data_df.at[i, 'cumsum'], round(data_df.at[i, 'cumsum'], 2), ha='right',
              size=9) for i in range(data_df.shape[0])]

    plt.legend(labels=['Precipitação acumulada (mm)', 'Precipitação diária (mm)'], bbox_to_anchor=(0.8, -0.2))
    plt.title('Precipitação diária e acumulada (mm)', fontdict={'family': 'sans-serif', 'size': 12}, pad=30.0)
    plt.tight_layout()
    plt.savefig(f"ETA40_pacummulated{data_df[x].min().replace('/', '')}a{data_df[x].max().replace('/', '')}.png")


def select_files_by_forecast_date(path: str, date: str) -> list:
    """
    Seleciona e retorna os arquivos do diretório path que tenham o padrão p{date}
    :param path:
    :param date:
    :return:
    """
    forecast_files = [it for it in os.listdir(path) if f'p{date}' in it]
    return forecast_files


def main() -> None:
    forecast_files_dir = './forecast_files'
    forecast_date = '011221'
    contour_file = './PSATCMG_CAMARGOS.bln'

    forecast_files = select_files_by_forecast_date(forecast_files_dir, forecast_date)
    forecast_files = [os.path.join(forecast_files_dir, it) for it in forecast_files]
    forecasted_date_pattern = re.compile(r'a(\d{6})\.dat')
    forecasted_dates = [forecasted_date_pattern.split(it)[1] for it in forecast_files]
    forecasted_dates = [pd.to_datetime(it, format='%d%m%y').strftime("%d/%m/%y") for it in forecasted_dates]

    data_df = pd.DataFrame()
    for filename, forecasted_date in zip(forecast_files, forecasted_dates):
        temp = read_data_file(filename)
        temp['forecasted_date'] = forecasted_date
        data_df = pd.concat([data_df, temp], axis=0)

    contour_df: pd.DataFrame = read_contour_file(contour_file)
    data_df = apply_contour(contour_df=contour_df, data_df=data_df)

    data_df = data_df.groupby('forecasted_date')[['data_value']].sum().reset_index()
    plot_accumulated_precipitation(data_df, x='forecasted_date', y='data_value')


if __name__ == '__main__':
    main()
