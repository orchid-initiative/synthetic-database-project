import datetime as dt
import pandas as pd
import numpy as np
import synth_data_module.mappings as mappings
import glob
import os
import time


class FormatOutput:
    def __init__(self, facility_id, output_loc, encounter_type):
        self.output_df = None
        self.output_loc = output_loc
        self.facility_id = facility_id
        self.encounter_type = encounter_type
        procedure_list = get_procedure_list()
        diagnosis_list = get_diagnosis_list()
        self.final_fields = ([{'name': 'Type of Care', 'length': 1, 'justification': 'left'},
                              {'name': 'Facility Identification Number', 'length': 6, 'justification': 'left'},
                              {'name': 'Date of Birth', 'length': 8, 'justification': 'left'},
                              {'name': 'Sex', 'length': 1, 'justification': 'left'},
                              {'name': 'Ethnicity', 'length': 2, 'justification': 'left'},
                              {'name': 'Race', 'length': 10, 'justification': 'left'},
                              {'name': 'Not in Use', 'length': 5, 'justification': 'left'},
                              {'name': 'Admission Date', 'length': 12, 'justification': 'left'},
                              {'name': 'Point of Origin', 'length': 1, 'justification': 'left'},
                              {'name': 'Route of Admission', 'length': 1, 'justification': 'left'},
                              {'name': 'Type of Admission', 'length': 1, 'justification': 'left'},
                              {'name': 'Discharge Date', 'length': 12, 'justification': 'left'},
                              {'name': 'Principal Diagnosis', 'length': 7, 'justification': 'left'},
                              {'name': 'Present on Admission for Principal Diagnosis', 'length': 1,
                               'justification': 'left'}] + diagnosis_list + [
                                 {'name': 'Diagnosis Codes', 'length': 250, 'justification': 'left'},
                                 {'name': 'Present on Admission', 'length': 100, 'justification': 'left'}]
                             + procedure_list + [{'name': 'Procedure Codes', 'length': 375, 'justification': 'left'},
                                                 {'name': 'Procedure Dates', 'length': 375, 'justification': 'left'},
                                                 {'name': 'Other Procedure Codes and Other Procedure Dates',
                                                  'length': 0, 'justification': 'left'},
                                                 {'name': 'External Causes of Morbidity and Present on Admission',
                                                  'length': 96, 'justification': 'left'},
                                                 {'name': 'Patient SSN', 'length': 9, 'justification': 'left'},
                                                 {'name': 'Disposition of Patient', 'length': 2,
                                                  'justification': 'left'},
                                                 {'name': 'Total Charges', 'length': 8, 'justification': 'right'},
                                                 {'name': 'Abstract Record Number (Optional)', 'length': 12,
                                                  'justification': 'left'},
                                                 {'name': 'Prehospital Care & Resuscitation - DNR Order', 'length': 2,
                                                  'justification': 'left'},
                                                 {'name': 'Payer Category', 'length': 2, 'justification': 'left'},
                                                 {'name': 'Type of Coverage', 'length': 1, 'justification': 'left'},
                                                 {'name': 'Plan Code Number', 'length': 4, 'justification': 'right'},
                                                 {'name': 'Preferred Spoken Language', 'length': 24,
                                                  'justification': 'left'},
                                                 {'name': 'Patient Address - Address Number and Street Name',
                                                  'length': 40, 'justification': 'left'},
                                                 {'name': 'Patient Address - City', 'length': 30,
                                                  'justification': 'left'},
                                                 {'name': 'Patient Address - State', 'length': 2,
                                                  'justification': 'left'},
                                                 {'name': 'Patient Address - Zip Code', 'length': 5,
                                                  'justification': 'left'},
                                                 {'name': 'Patient Address - Country Code', 'length': 2,
                                                  'justification': 'left'},
                                                 {'name': 'Patient Address - Homeless Indicator', 'length': 1,
                                                  'justification': 'left'}])
        self.fields_info = pd.DataFrame.from_dict(self.final_fields)
        self.add_demographics()
        self.add_encounters(encounter_type)
        self.add_procedures()
        self.add_other_diagnosis()
        self.hard_coding()
        self.fill_missing()
        self.fixed_width_output()
        date_time = dt.datetime.fromtimestamp(time.time())
        self.output_df[self.fields_info['name'].tolist()].to_csv(
            f'{output_loc}/formatted_data/csv_formatted_data_{date_time.strftime("%d-%m-%Y_%H%M%S")}.csv', index=False)

    def add_demographics(self, ):
        patients = pd.read_csv(f'{self.output_loc}/csv/patients.csv', dtype=str, header=None)
        patients['patient_id'] = patients.iloc[:, 0]
        patients['Date of Birth'] = patients.iloc[:, 1].apply(lambda x: x.replace('-', ''))
        patients['Sex'] = patients.iloc[:, 14]
        patients['Ethnicity'] = mappings.ethnicity(patients.iloc[:, 13])
        patients['Race'] = mappings.race(patients.iloc[:, 12])
        patients['Patient SSN'] = patients.iloc[:, 3].fillna('000000001').apply(lambda x: x.replace('-', ''))
        patients['Patient Address - Address Number and Street Name'] = patients.iloc[:, 16]
        patients['Patient Address - City'] = patients.iloc[:, 17]
        patients['Patient Address - State'] = patients.iloc[:, 18]
        patients['Patient Address - Zip Code'] = patients.iloc[:, 20].fillna('XXXXX')
        self.output_df = patients[['patient_id', 'Date of Birth', 'Sex', 'Ethnicity', 'Race',
                                   'Patient SSN', 'Patient Address - Address Number and Street Name',
                                   'Patient Address - City', 'Patient Address - State',
                                   'Patient Address - Zip Code']]
        print('Demographics added.  Shape: ', self.output_df.shape)
        del patients

    def add_encounters(self, encounter_type):
        encounters = pd.read_csv(f'{self.output_loc}/csv/encounters.csv', dtype=str, parse_dates=[1, 2], header=0)
        encounters['encounter_id'] = encounters.iloc[:, 0]
        encounters['payer_id'] = encounters.iloc[:, 6]
        encounters['EncounterClass'] = encounters.iloc[:, 7]
        encounters = encounters.loc[encounters['EncounterClass'] == encounter_type, :].copy()
        try:
            encounters['Admission Date'] = encounters.iloc[:, 1].apply(lambda x: x.strftime('%Y%m%d'))
            encounters['Discharge Date'] = encounters.iloc[:, 2].apply(lambda x: x.strftime('%Y%m%d'))
        except TypeError:
            encounters['Admission Date'] = encounters.iloc[:, 1].apply(
                lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d'))
            encounters['Discharge Date'] = encounters.iloc[:, 2].apply(
                lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d'))
        # encounters['Principal Diagnosis'] = encounters.iloc[:, 13]  # Needs mapping for ICD-10
        encounters['Principal Diagnosis'] = mappings.snomedicdbasicmap(encounters.iloc[:, 13])
        encounters['Total Charges'] = encounters.iloc[:, 11].apply(lambda x: min(int(x.split('.')[0]), 9999999))
        print('SUB-CHECK - Encounters Shape: ', encounters.shape)
        # Prepare and merge payers info (replace IDs with real payer data) into encounters
        payers = pd.read_csv(f'{self.output_loc}/csv/payers.csv', dtype=str, parse_dates=[1, 2], header=0)
        payers['payer_id'] = payers.iloc[:, 0]
        payers['Payer Category'] = payers.apply(mappings.payer_category, axis=1).astype(str)
        encounters = encounters.merge(payers[['payer_id', 'Payer Category']], how='left', left_on='payer_id',
                                      right_on='payer_id')
        # Prepare and merge PoA codes - NOT IN USE CURRENTLY
        # cpcds = pd.read_csv(f'{self.output_loc}/cpcds/CPCDS_Claims.csv', dtype=str, parse_dates=[1, 2], header=0)
        # cpcds['claim_id'] = payers.iloc[:, 8]
        # cpcds['claim_poa'] = payers.iloc[:, 90]
        # cpcds['claim_principal'] = payers.iloc[:, 92]
        print('SUB-CHECK - Payers and codes merged.  Encounters Shape: ', encounters.shape)
        self.output_df = self.output_df.merge(encounters[['encounter_id', 'Admission Date', 'Discharge Date',
                                                          'Principal Diagnosis', 'Total Charges', 'Payer Category']],
                                              how='left', left_on='patient_id', right_on=encounters.iloc[:, 3])
        print('Encounter info added.  Shape: ', self.output_df.shape)
        self.output_df = self.output_df.dropna(subset=['encounter_id']).reset_index(drop=True)
        print('Patients with no encounters of desired type dropped.  Shape: ', self.output_df.shape)
        del encounters

    def add_procedures(self):
        procedures = pd.read_csv(f'{self.output_loc}/csv/procedures.csv', dtype=str, parse_dates=[0, 1], header=0)
        # TODO procedures are not included in the current basic snomed map, find them.  Pass-through for now
        # procedures['Procedure Codes'] = mappings.snomedicdbasicmap(procedures.iloc[:, 4])
        procedures['encounter_id'] = procedures.iloc[:, 3]
        procedures['Procedure Codes'] = procedures.iloc[:, 4]
        try:
            procedures['Procedure Dates'] = procedures.iloc[:, 0].apply(lambda x: x.strftime('%Y%m%d'))
        except TypeError:
            procedures['Procedure Dates'] = procedures.iloc[:, 0].apply(
                lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d'))
        print('SUB-CHECK - Procedures Shape pre group: ', procedures.shape)
        # print('procedure codes pre group: ', procedures.iloc[:, : 8])

        procedures = procedures.groupby('encounter_id').agg(lambda x: tuple(x)).reset_index()
        print('SUB-CHECK - Procedures Shape post group: ', procedures.shape)
        # print('procedure codes post group: ', procedures.iloc[:, : 8])

        self.output_df = self.output_df.merge(procedures[['Procedure Codes', 'Procedure Dates']],
                                              how='left', left_on='encounter_id', right_on=procedures.iloc[:, 0])
        print('Procedures info added.  Shape: ', self.output_df.shape)
        # print('procedure codes2: ', self.output_df['Procedure Codes'])

        self.output_df = self.output_df.apply(modify_row, axis=1, args=(
            ['Procedure Codes', 'Procedure Dates'], ['Procedure Code', 'Procedure Date']))

        print('Procedure info formatted.   Shape: ', self.output_df.shape)

        del procedures

    def add_other_diagnosis(self):
        diagnosis = pd.read_csv(f'{self.output_loc}/cpcds/CPCDS_Claims.csv', dtype=str, header=0)

        diagnosis['encounter_id'] = diagnosis.iloc[:, 8]

        diagnosis['Diagnosis Codes'] = mappings.snomedicdbasicmap(diagnosis.iloc[:, 88])
        diagnosis['Diagnosis Codes'].replace("", np.nan, inplace=True)
        diagnosis.dropna(subset=['Diagnosis Codes'], inplace=True)

        diagnosis['Present on Admission'] = diagnosis.iloc[:, 90]

        print('SUB-CHECK - Diagnosis Shape pre group: ', diagnosis.shape)

        diagnosis = diagnosis.groupby('encounter_id').agg(lambda x: tuple(x)).reset_index()
        print('SUB-CHECK - Diagnosis Shape post group: ', diagnosis.shape)

        self.output_df = self.output_df.merge(diagnosis[['Diagnosis Codes', 'Present on Admission']],
                                              how='left', left_on='encounter_id', right_on=diagnosis.iloc[:, 0])

        print('Diagnosis info added.  Shape: ', self.output_df.shape)

        self.output_df = self.output_df.apply(modify_row, axis=1, args=(
            ['Diagnosis Codes', 'Present on Admission'], ['Diagnosis', 'Present on Admission']))

        del diagnosis

    def hard_coding(self):
        self.output_df['Type of Care'] = 1
        self.output_df['Facility Identification Number'] = self.facility_id
        self.output_df['Not in Use'] = '     '
        self.output_df['Type of Admission'] = np.random.choice(['1', '2', '3', '4', '5', '9'], size=len(self.output_df))
        self.output_df['Point of Origin'] = np.random.choice(['1', '2', '4', '5', '6', '8', 'D', 'E', 'F', 'G'])
        self.output_df.loc[self.output_df['Type of Admission'] == '4', 'Point of Origin'] = np.random.choice(['5', '6'])
        self.output_df['Route of Admission'] = '3'
        self.output_df.loc[self.output_df['Type of Admission'] == '1', 'Route of Admission'] = np.random.choice(
            ['1', '2'])
        self.output_df['Disposition of Patient'] = np.random.choice(mappings.disposition(), size=len(self.output_df))
        self.output_df['Prehospital Care & Resuscitation - DNR Order'] = np.random.choice(['Y', 'N'],
                                                                                          size=len(self.output_df))
        self.output_df['Abstract Record Number (Optional)'] = np.arange(1, len(self.output_df) + 1)
        print('Hard-coded fields added.  Shape: ', self.output_df.shape)

    def fill_missing(self):
        cols = list(self.output_df.columns)
        missing = list(set(self.fields_info['name'].tolist()).difference(cols))
        for col in missing:
            print(col, " is missing, assigning null values")
            self.output_df[col] = None

    def fixed_width_output(self):
        df = self.output_df.copy()

        columns = self.fields_info['name'].tolist()

        df = df[columns]

        formats = []
        for width, justification in zip(self.fields_info.length, self.fields_info.justification):
            if justification == 'left':
                fmt = '{' + f':<{width}' + '}'
                fmt = fmt.format
            else:
                fmt = '{' + f':>{width}' + '}'
                fmt = fmt.format
            formats.append(fmt)

        tuple_columns = ['Procedure Codes', 'Procedure Dates', 'Diagnosis Codes', 'Present on Admission']
        df = df.drop(columns=tuple_columns)

        formatters = {key: value for key, value in zip(columns, formats) if key not in tuple_columns}

        df.fillna('', inplace=True)

        fixed_width_str = df.to_string(formatters=formatters, col_space=5, header=False, index=False)

        print('Fixed Width Converted. Shape: ', df.shape)
        print(fixed_width_str)
        date_time = dt.datetime.fromtimestamp(time.time())
        filename = f'{self.output_loc}/formatted_data/fixed_width_data_{date_time.strftime("%d-%m-%Y_%H%M%S")}.csv'
        with open(filename, "w") as text_file:
            text_file.write(fixed_width_str)


# Functions for various formatting operations above
def get_procedure_list():
    procedure_list = []
    for i in range(1, 25):
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
    for i in range(2, 25):
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
            for code, date, i in zip(first, second, range(1, 25)):
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
