import datetime as dt
from configparser import ConfigParser
import pandas as pd
import numpy as np
import synth_data_module.mappings as mappings
import glob
import os
import time


class FormatOutput:
    def __init__(self, facility_id, output_loc, encounter_type):
        self.output_df = pd.DataFrame
        self.output_loc = output_loc
        self.facility_id = facility_id
        self.encounter_type = encounter_type
        procedure_list = get_procedure_list()
        diagnosis_list = get_diagnosis_list()
        self.fields_dict = (
                [{'name': 'Type of Care', 'length': 1, 'justification': 'left'},
                 {'name': 'Facility Identification Number', 'length': 6, 'justification': 'left'},
                 {'name': 'Facility Name', 'length': 0, 'justification': 'left'},
                 {'name': 'Date of Birth', 'length': 8, 'justification': 'left'},
                 {'name': 'Sex', 'length': 1, 'justification': 'left'},
                 {'name': 'Ethnicity', 'length': 2, 'justification': 'left'},
                 {'name': 'Race', 'length': 10, 'justification': 'left'},
                 {'name': 'Not in Use 1', 'length': 5, 'justification': 'left'},
                 {'name': 'Admission Date', 'length': 12, 'justification': 'left'},
                 {'name': 'Point of Origin', 'length': 1, 'justification': 'left'},
                 {'name': 'Route of Admission', 'length': 1, 'justification': 'left'},
                 {'name': 'Type of Admission', 'length': 1, 'justification': 'left'},
                 {'name': 'Discharge Date', 'length': 12, 'justification': 'left'},
                 {'name': 'Principal Diagnosis', 'length': 7, 'justification': 'left'},
                 {'name': 'Present on Admission for Principal Diagnosis', 'length': 1, 'justification': 'left'}]
                + diagnosis_list +
                [{'name': 'Diagnosis Codes', 'length': 250, 'justification': 'left'},
                 {'name': 'Present on Admission', 'length': 100, 'justification': 'left'}]
                + procedure_list +
                [{'name': 'Procedure Codes', 'length': 375, 'justification': 'left'},
                 {'name': 'Procedure Dates', 'length': 375, 'justification': 'left'},
                 {'name': 'External Causes of Morbidity and Present on Admission', 'length': 96,
                  'justification': 'left'},
                 {'name': 'Patient SSN', 'length': 9, 'justification': 'left'},
                 {'name': 'Disposition of Patient', 'length': 2, 'justification': 'left'},
                 {'name': 'Total Charges', 'length': 8, 'justification': 'right'},
                 {'name': 'Abstract Record Number (Optional)', 'length': 12, 'justification': 'left'},
                 {'name': 'Prehospital Care & Resuscitation - DNR Order', 'length': 2, 'justification': 'left'},
                 {'name': 'Payer Category', 'length': 2, 'justification': 'left'},
                 {'name': 'Type of Coverage', 'length': 1, 'justification': 'left'},
                 {'name': 'Plan Code Number', 'length': 4, 'justification': 'right'},
                 {'name': 'Preferred Spoken Language', 'length': 24, 'justification': 'left'},
                 {'name': 'Patient Address - Address Number and Street Name', 'length': 40, 'justification': 'left'},
                 {'name': 'Patient Address - City', 'length': 30, 'justification': 'left'},
                 {'name': 'Patient Address - State', 'length': 2, 'justification': 'left'},
                 {'name': 'Patient Address - Zip Code', 'length': 5, 'justification': 'left'},
                 {'name': 'Patient Address - Country Code', 'length': 2, 'justification': 'left'},
                 {'name': 'Patient Address - Homeless Indicator', 'length': 1, 'justification': 'left'},
                 {'name': 'Not in Use 2', 'length': 356, 'justification': 'left'}
                 ])
        self.tuple_columns = ['Procedure Codes', 'Procedure Dates', 'Diagnosis Codes', 'Present on Admission']
        self.fields_info = pd.DataFrame.from_dict(self.fields_dict)
        self.final_fields = self.fields_info.drop(
            self.fields_info[self.fields_info['name'].isin(self.tuple_columns)].index)
        # Grab the synthea_settings txt file and consume the settings as a dictionary for use as needed
        java_configs = ConfigParser()
        with open("synthea_settings") as stream:
            java_configs.read_string("[SETTINGS]\n" + stream.read())
        self.country_code = java_configs['SETTINGS']['generate.geography.country_code']
        self.add_demographics()
        self.add_encounters(encounter_type)
        self.add_procedures()
        self.add_other_diagnosis()
        self.hard_coding()
        self.fill_missing()
        self.fixed_width_output()
        date_time = dt.datetime.fromtimestamp(time.time())
        self.output_df[self.final_fields['name'].tolist()].to_csv(
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
        patients['Patient Address - Zip Code'] = patients.iloc[:, 21].fillna('XXXXX')
        patients['Patient Address - Country Code'] = self.country_code
        self.output_df = patients[['patient_id', 'Date of Birth', 'Sex', 'Ethnicity', 'Race',
                                   'Patient SSN', 'Patient Address - Address Number and Street Name',
                                   'Patient Address - City', 'Patient Address - State',
                                   'Patient Address - Zip Code', 'Patient Address - Country Code']]
        print('Demographics added.  Shape: ', self.output_df.shape)
        del patients

    def add_encounters(self, encounter_type=None):
        encounters = pd.read_csv(f'{self.output_loc}/csv/encounters.csv', dtype=str, parse_dates=[1, 2], header=0)
        encounters['encounter_id'] = encounters.iloc[:, 0]
        encounters['organization_id'] = encounters.iloc[:, 4]
        encounters['payer_id'] = encounters.iloc[:, 6]
        encounters['EncounterClass'] = encounters.iloc[:, 7]
        if encounter_type:
            encounters = encounters.loc[encounters['EncounterClass'] == encounter_type, :].copy()

        # We had some issues getting the date format correct if headers were used in synthea, this try/except handles
        # both cases more smoothly now
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
        encounters['Total Charges'] = encounters.iloc[:, 11].apply(lambda x: str(min(int(x.split('.')[0]), 9999999)))
        print('SUB-CHECK - Encounters Shape: ', encounters.shape)

        # Prepare and merge organizations name as Facility Name (replace IDs with real names) into encounters
        organizations = pd.read_csv(f'{self.output_loc}/csv/organizations.csv', dtype=str, parse_dates=[1, 2], header=0)
        organizations['organization_id'] = organizations.iloc[:, 0]
        organizations['Facility Name'] = organizations.iloc[:, 1]
        encounters = encounters.merge(organizations[['organization_id', 'Facility Name']], how='left',
                                      left_on='organization_id', right_on='organization_id')
        print('SUB-CHECK - Facility Name merged.  Encounters Shape: ', encounters.shape)

        # Prepare and merge payers info (replace IDs with real payer data) into encounters
        payers = pd.read_csv(f'{self.output_loc}/csv/payers.csv', dtype=str, parse_dates=[1, 2], header=0)
        payers['payer_id'] = payers.iloc[:, 0]
        payers['Payer Category'] = payers.apply(mappings.payer_category, axis=1).astype(str)
        encounters = encounters.merge(payers[['payer_id', 'Payer Category']], how='left', left_on='payer_id',
                                      right_on='payer_id')
        print('SUB-CHECK - Payers and codes merged.  Encounters Shape: ', encounters.shape)

        # Merge the encounters dataframe into self.output_df, keeping only the fields we care about
        self.output_df = self.output_df.merge(encounters[['encounter_id', 'Admission Date', 'Discharge Date',
                                                          'Principal Diagnosis', 'Total Charges', 'Payer Category',
                                                          'Facility Name']],
                                              how='left', left_on='patient_id', right_on=encounters.iloc[:, 3])
        print('Encounter info added.  Shape: ', self.output_df.shape)
        self.output_df = self.output_df.dropna(subset=['encounter_id']).reset_index(drop=True)
        print('Patients with no encounters of desired type dropped.  Shape: ', self.output_df.shape)
        del encounters

    def add_procedures(self):
        # As the file sizes get large, a full read_csv becomes impossible, so we select the columns we want to use and
        # effectively reindex them in the dataframe we are creating (i.e. column 3 in the csv becomes column 1, etc.)
        procedures = pd.read_csv(f'{self.output_loc}/csv/procedures.csv', dtype=str, parse_dates=[0, 1], header=0,
                                 usecols=[0, 3, 4])
        # TODO procedures are not included in the current basic snomed map, find them.  Pass-through for now.
        #  Note that these are also longer and get truncated by field length later!
        #  procedures['Procedure Codes'] = mappings.snomedicdbasicmap(procedures.iloc[:, 4])

        # Reminder that column index 1 here is the column index 3 from the procedures.csv due to our usecols parameter
        procedures['encounter_id'] = procedures.iloc[:, 1]
        procedures['Procedure Codes'] = procedures.iloc[:, 2]
        # Similar to encounters, we handle either date formatting
        try:
            procedures['Procedure Dates'] = procedures.iloc[:, 0].apply(lambda x: x.strftime('%Y%m%d'))
        except TypeError:
            procedures['Procedure Dates'] = procedures.iloc[:, 0].apply(
                lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d'))

        # Group codes by encounter_id to consolidate to one row for each encounter - this makes later merges easier
        print('SUB-CHECK - Procedures Shape pre group: ', procedures.shape)
        procedures = procedures.groupby('encounter_id').agg(lambda x: tuple(x)).reset_index()
        print('SUB-CHECK - Procedures Shape post group: ', procedures.shape)

        # Merge procedure code and date into output_df and then do a special formatting operation for the lists
        self.output_df = self.output_df.merge(procedures[['Procedure Codes', 'Procedure Dates']],
                                              how='left', left_on='encounter_id', right_on=procedures.iloc[:, 0])
        print('Procedures info added.  Shape: ', self.output_df.shape)

        self.output_df = self.output_df.apply(modify_row, axis=1, args=(
            ['Procedure Codes', 'Procedure Dates'], ['Procedure Code', 'Procedure Date']))
        print('Procedure info formatted.   Shape: ', self.output_df.shape)

        del procedures

    def add_other_diagnosis(self):
        # As the file sizes get large, a full read_csv becomes impossible, so we select the columns we want to use and
        # effectively reindex them in the dataframe we are creating (i.e. column 8 in the csv becomes column 0, etc.)
        diagnosis = pd.read_csv(f'{self.output_loc}/cpcds/CPCDS_Claims.csv', dtype=str, header=0, usecols=[8, 88, 90])

        # Reminder that column index 0 here is the column index 8 from the CPCSD_Claims.csv due to our usecols parameter
        diagnosis['encounter_id'] = diagnosis.iloc[:, 0]

        diagnosis['Diagnosis Codes'] = mappings.snomedicdbasicmap(diagnosis.iloc[:, 1])
        diagnosis['Diagnosis Codes'].replace("", np.nan, inplace=True)
        diagnosis.dropna(subset=['Diagnosis Codes'], inplace=True)

        diagnosis['Present on Admission'] = diagnosis.iloc[:, 2]

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
        # Hard code Type of Care to be 1 ("Acute Care") always for now
        care_s = pd.Series([1 for _ in range(len(self.output_df.index))])
        self.output_df = pd.concat([self.output_df, care_s.rename('Type of Care')], axis=1)

        # Hard code Facility ID to be the passed in value from run_synthea
        # Todo: make this a runtime arg with a default value
        facility_s = pd.Series([self.facility_id for _ in range(len(self.output_df.index))])
        self.output_df = pd.concat([self.output_df, facility_s.rename('Facility Identification Number')], axis=1)

        # Randomly assign Type of Admission, Point of Origin, Route of Admission
        ta_s = pd.Series(np.random.choice(['1', '2', '3', '4', '5', '9'], size=len(self.output_df)))
        self.output_df = pd.concat([self.output_df, ta_s.rename('Type of Admission')], axis=1)
        po_s = pd.Series(np.random.choice(['1', '2', '4', '5', '6', '8', 'D', 'E', 'F', 'G'], size=len(self.output_df)))
        self.output_df = pd.concat([self.output_df, po_s.rename('Point of Origin')], axis=1)
        ra_s = pd.Series([3 for _ in range(len(self.output_df.index))])
        self.output_df = pd.concat([self.output_df, ra_s.rename('Route of Admission')], axis=1)

        # Narrow the choices of Point of Origin or Route of Admission depending on Type of Admission Value
        self.output_df.loc[self.output_df['Type of Admission'] == '4', 'Point of Origin'] = \
            np.random.choice(['5', '6'], size=len(self.output_df.loc[self.output_df['Type of Admission'] == '4']))
        self.output_df.loc[self.output_df['Type of Admission'] == '1', 'Route of Admission'] = \
            np.random.choice(['1', '2'], size=len(self.output_df.loc[self.output_df['Type of Admission'] == '1']))

        disposition_s = pd.Series(np.random.choice(mappings.disposition(), size=len(self.output_df)))
        self.output_df = pd.concat([self.output_df, disposition_s.rename('Disposition of Patient')], axis=1)

        dnr_s = pd.Series(np.random.choice(['Y', 'N'], size=len(self.output_df)))
        self.output_df = pd.concat([self.output_df, dnr_s.rename('Prehospital Care & Resuscitation - DNR Order')],
                                   axis=1)

        arn_s = pd.Series(np.arange(1, len(self.output_df) + 1))
        self.output_df = pd.concat([self.output_df, arn_s.rename('Abstract Record Number (Optional)')], axis=1)
        print('Hard-coded fields added.  Shape: ', self.output_df.shape)

    def fill_missing(self):
        cols = list(self.output_df.columns)
        missing = list(set(self.final_fields['name'].tolist()).difference(cols))
        none_s = pd.Series([None for _ in range(len(self.output_df.index))])
        for col in missing:
            print(col, "is missing, assigning null values")
            # self.output_df[col] = None
            self.output_df = pd.concat([self.output_df, none_s.rename(col)], axis=1)

    def fixed_width_output(self):
        df = self.output_df.copy()
        columns = self.final_fields['name'].tolist()
        df = df[columns]

        # Force left/right justification, min/max length and string type for each column and
        # keep a list of this format for all our columns
        formats = []
        for length, justification in zip(self.final_fields.length, self.final_fields.justification):
            if justification == 'left':
                justchar = '-'
            else:
                justchar = ''
            fmt = f'%{justchar}{length}.{length}s'
            formats += [fmt]

        df.fillna('', inplace=True)

        print('Fixed Width Converted. Shape: ', df.shape)
        date_time = dt.datetime.fromtimestamp(time.time())
        filename = f'{self.output_loc}/formatted_data/fixed_width_txt_{date_time.strftime("%d-%m-%Y_%H%M%S")}.txt'
        np.savetxt(filename, df, fmt=formats, delimiter='')


# Functions for various formatting operations above
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
