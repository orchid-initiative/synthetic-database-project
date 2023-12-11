import glob
import os
from abc import ABC, abstractmethod

import pandas as pd


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
    for i in range(1, 26):
        if i == 1:
            code = {'name': f'Principal Procedure Code', 'length': 7, 'justification': 'left'}
            procedure_list.append(code)
            date = {'name': f'Principal Procedure Date', 'length': 8, 'justification': 'left'}
            procedure_list.append(date)
        else:
            code = {'name': f'Procedure Code {i}', 'length': 7, 'justification': 'left'}
            procedure_list.append(code)
            date = {'name': f'Procedure Date {i}', 'length': 8, 'justification': 'left'}
            procedure_list.append(date)

    return procedure_list


def get_diagnosis_list(length):
    diagnosis_list = []
    for i in range(2, 26):
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


def modify_row(row, df_fields, new_fields):
    first = row[df_fields[0]]
    second = row[df_fields[1]]
    if True:  # 'Procedure Codes' in df_fields:
        if isinstance(first, tuple) and isinstance(second, tuple):
            for code, date, i in zip(first, second, range(1, 26)):
                if i == 1:
                    if new_fields[0] == 'Diagnosis':
                        row[f'Principal {new_fields[0]}'] = code
                        row[f'{new_fields[1]} for Principal {new_fields[0]}'] = date
                    else:
                        row[f'Principal {new_fields[0]}'] = code
                        row[f'Principal {new_fields[1]}'] = date
                else:
                    row[f'{new_fields[0]} {i}'] = code
                    row[f'{new_fields[1]} {i}'] = date
    return row


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
