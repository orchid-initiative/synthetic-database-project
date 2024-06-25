########################################
# Functions to help with formatting data
########################################
import glob
import os
import math
from abc import ABC, abstractmethod
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np


class Formatter(ABC):
    @abstractmethod
    def gather_data(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def format_data(self) -> str:
        pass

    @abstractmethod
    def suggested_filename(self) -> str:
        pass

    @abstractmethod
    def write_data(self, data):
        pass


# Functions for various formatting operations
def get_procedure_list():
    # For Procedures, we are not given a principal vs other distinction from Synthea.  We use the first one in the list
    # as the principal procedure.
    procedure_list = []
    for i in range(0, 25):
        if i == 0:
            code = {'fieldid': 'proc_p', 'name': f'Principal Procedure Code', 'length': 7, 'justification': 'left'}
            procedure_list.append(code)
            date = {'fieldid': 'proc_pdt', 'name': f'Principal Procedure Date', 'length': 8, 'justification': 'left'}
            procedure_list.append(date)
            days = {'fieldid': 'proc_pdy', 'name': f'Principal Procedure Days', 'length': 8, 'justification': 'left'}
            procedure_list.append(days)
        else:
            code = {'fieldid': f'oproc{i}', 'name': f'Procedure Code {i}', 'length': 7, 'justification': 'left'}
            procedure_list.append(code)
            date = {'fieldid': f'procdt{i}', 'name': f'Procedure Date {i}', 'length': 8, 'justification': 'left'}
            procedure_list.append(date)
            days = {'fieldid': f'procdy{i}', 'name': f'Procedure Days {i}', 'length': 8, 'justification': 'left'}
            procedure_list.append(days)

    return procedure_list


def get_diagnosis_list(length):
    diagnosis_list = []
    for i in range(1, 25):
        diagnosis = {'fieldid': f'odiag{i}', 'name': f'Diagnosis {i}', 'length': length, 'justification': 'left'}
        diagnosis_list.append(diagnosis)
        present_on_admission = {'fieldid': f'opoa{i}', 'name': f'Present on Admission {i}', 'length': 1, 'justification': 'left'}
        diagnosis_list.append(present_on_admission)

    return diagnosis_list


def get_morbidity_list():
    morbidity_list = []
    for i in range(1, 13):
        morbidity = {'fieldid': f'ecm{i}', 'name': f'External Causes of Morbidity {i}', 'length': 8, 'justification': 'left'}
        morbidity_list.append(morbidity)
        present_on_admission = {'fieldid': f'epoa{i}', 'name': f'POA - External Causes of Morbidity {i}', 'length': 1,
                                'justification': 'left'}
        morbidity_list.append(present_on_admission)

    return morbidity_list


def modify_procedure_row(row, df_fields, new_fields):
    first = row[df_fields[0]]
    second = row[df_fields[1]]
    third = row[df_fields[2]]
    if True:  # 'Procedure Codes' in df_fields:
        if isinstance(first, tuple) and isinstance(second, tuple) and isinstance(third, tuple):
            for code, date, days, i in zip(first, second, third, range(0, 25)):
                if i == 0:
                    row[f'Principal {new_fields[0]}'] = code
                    row[f'Principal {new_fields[1]}'] = date
                    row[f'Principal {new_fields[2]}'] = days
                else:
                    row[f'{new_fields[0]} {i}'] = code
                    row[f'{new_fields[1]} {i}'] = date
                    row[f'{new_fields[2]} {i}'] = days
    return row


def modify_diagnosis_row(row, df_fields, new_fields):
    first = row[df_fields[0]]
    second = row[df_fields[1]]
    if True:  # 'Procedure Codes' in df_fields:
        if isinstance(first, tuple) and isinstance(second, tuple):
            for code, date, i in zip(first, second, range(0, 25)):
                if i == 0:
                    row[f'Principal {new_fields[0]}'] = code
                    row[f'{new_fields[1]} for Principal {new_fields[0]}'] = date
                else:
                    row[f'{new_fields[0]} {i}'] = code
                    row[f'{new_fields[1]} {i}'] = date
    return row


# Function to parse dates with multiple formats
def parse_date(date):
    try:
        return pd.to_datetime(date, format='%m%d%Y').tz_localize(None)
    except ValueError:
        try:
            return pd.to_datetime(date).tz_localize(None)
        except ValueError:
            return pd.NaT


def parse_date_vectorized(series):
    return pd.to_datetime(series, errors='coerce', format='%m%d%Y').fillna(pd.to_datetime(series, errors='coerce'))


# HCAI has specific criteria for age reporting
def calculate_age(df, date1, date2, form="agedays", fieldname='Procedure Days'):
    # Ensure Date Formatting, then calculate specialized date differences according to desired format
    df['date1'] = parse_date_vectorized(df[date1])
    df['date2'] = parse_date_vectorized(df[date2])
    df['basic_days'] = (df['date2'] - df['date1']).dt.days

    if form == "agedays":
        df[fieldname] = np.where(df['basic_days'] < 366, df['basic_days'].clip(lower=1), 0)
    elif form == "staydays":
        df[fieldname] = df['basic_days'].astype(float)  # Handle NaNs automatically
    elif form == 'adjstaydays':
        df[fieldname] = df['basic_days'].clip(lower=1)
    elif form == 'years':
        df[fieldname] = df.apply(lambda row: relativedelta(row['date2'], row['date1']).years, axis=1)
    elif form == 'range5':
        df[fieldname] = df.apply(lambda row: str(math.ceil((relativedelta(row['date2'], row['date1']).years + 1) / 5) +
                                                math.ceil(1 * (relativedelta(row['date2'], row['date1']).years /
                                                               (relativedelta(row['date2'], row['date1']).years + 1)))).zfill(2), axis=1)
    elif form == 'range10':
        df[fieldname] = df.apply(lambda row: str(math.ceil((relativedelta(row['date2'], row['date1']).years + 1) / 10) +
                                                math.ceil(1 * (relativedelta(row['date2'], row['date1']).years /
                                                               (relativedelta(row['date2'], row['date1']).years + 1)))).zfill(2), axis=1)
    return df


# Functions for maintaining data outputs and processing arguments for runtime
def clear_old_files():
    output_cpcds = 'output/cpcds/*'
    output_csvs = 'output/csv/*'
    output_fhirs = 'output/fhir/*'
    output_metadata = 'output/metadata/*'

    files0 = glob.glob(output_cpcds)
    for f in files0:
        os.remove(f)
    files1 = glob.glob(output_csvs)
    for f in files1:
        os.remove(f)
    files2 = glob.glob(output_fhirs)
    for f in files2:
        os.remove(f)
    files3 = glob.glob(output_metadata)
    for f in files3:
        os.remove(f)


def parse_city(specify_city=None):
    city = None
    state = None
    if specify_city:
        if len(specify_city.split(",")) == 2:
            city = str(specify_city.split(",")[0])
            state = str(specify_city.split(",")[1])
            print("Overriding default location Massachusetts to city, state: %s, %s " % (city, state))
        else:
            state = str(specify_city.split(",")[0])
            print("Overriding default location Massachusetts to state %s " % state)
    return city, state
