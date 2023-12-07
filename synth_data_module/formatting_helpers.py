import glob
import os
from abc import ABC, abstractmethod


class Formatter(ABC):
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


def get_diagnosis_list():
    diagnosis_list = []
    for i in range(2, 26):
        diagnosis = {'name': f'Diagnosis {i}', 'length': 7, 'justification': 'left'}
        diagnosis_list.append(diagnosis)
        present_on_admission = {'name': f'Present on Admission {i}', 'length': 1, 'justification': 'left'}
        diagnosis_list.append(present_on_admission)

    return diagnosis_list


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


# Functions for maintaining data outputs and arguments for runtime
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
