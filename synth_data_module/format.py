import time
import datetime as dt
import pandas as pd
import numpy as np
import synth_data_module.mappings as mappings


class FormatOutput:
    def __init__(self, facility_id, output_loc):
        self.output_df = None
        self.output_loc = output_loc
        self.facility_id = facility_id
        self.final_fields = ['Type of Care', 'Facility Identification Number', 'Date of Birth', 'Sex', 'Ethnicity',
                             'Race', 'Not in Use', 'Admission Date', 'Point of Origin', 'Route of Admission',
                             'Type of Admission', 'Discharge Date', 'Principal Diagnosis',
                             'Present on Admission for Principal Diagnosis', 'Other Diagnosis and Present on Admission',
                             'Procedure Codes', 'Procedure Dates',
                             'Other Procedure Codes and Other Procedure Dates',
                             'External Causes of Morbidity and Present on Admission', 'Patient SSN',
                             'Disposition of Patient', 'Total Charges', 'Abstract Record Number (Optional)',
                             'Prehospital Care & Resuscitation - DNR Order', 'Payer Category', 'Type of Coverage',
                             'Plan Code Number', 'Preferred Spoken Language',
                             'Patient Address - Address Number and Street Name',
                             'Patient Address - City', 'Patient Address - State', 'Patient Address - Zip Code',
                             'Patient Address - Country Code', 'Patient Address - Homeless Indicator']
        self.add_demographics()
        self.add_encounters()
        self.add_procedures()
        self.hard_coding()
        self.fill_missing()
        timestamp = time.time()
        date_time = dt.datetime.fromtimestamp(timestamp)
        self.output_df[self.final_fields].to_csv(
            f'{output_loc}/formatted_data_{date_time.strftime("%d-%m-%Y_%H%M%S")}.csv', index=False)

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

    def add_encounters(self):
        encounters = pd.read_csv(f'{self.output_loc}/csv/encounters.csv', dtype=str, parse_dates=[1, 2], header=0)
        encounters['encounter_id'] = encounters.iloc[:, 0]
        encounters['payer_id'] = encounters.iloc[:, 6]
        encounters['EncounterClass'] = encounters.iloc[:, 7]
        encounters = encounters.loc[encounters['EncounterClass'] == 'inpatient', :].copy()
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
        encounters = encounters.merge(payers[['payer_id','Payer Category']], how='left', left_on='payer_id',
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
        del encounters

    def add_procedures(self):
        procedures = pd.read_csv(f'{self.output_loc}/csv/procedures.csv', dtype=str, parse_dates=[0, 1], header=0)
        #procedures['Procedure Codes'] = mappings.snomedicdbasicmap(procedures.iloc[:, 4])
        procedures['encounter_id'] = procedures.iloc[:, 3]
        procedures['Procedure Codes'] = procedures.iloc[:, 4]
        try:
            procedures['Procedure Dates'] = procedures.iloc[:, 0].apply(lambda x: x.strftime('%Y%m%d'))
        except TypeError:
            procedures['Procedure Dates'] = procedures.iloc[:, 0].apply(
                lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d'))
        print('SUB-CHECK - Procedures Shape pre group: ', procedures.shape)
        print('procedure codes pre group: ', procedures.iloc[:, : 8])

        procedures = procedures.groupby('encounter_id').agg(lambda x: tuple(x)).reset_index()
        print('SUB-CHECK - Procedures Shape post group: ', procedures.shape)
        print('procedure codes post group: ', procedures.iloc[:, : 8])

        self.output_df = self.output_df.merge(procedures[['Procedure Codes', 'Procedure Dates']],
                                              how='left', left_on='encounter_id', right_on=procedures.iloc[:, 0])
        print('Procedures info added.  Shape: ', self.output_df.shape)
        print('procedure codes2: ', self.output_df['Procedure Codes'])

        del procedures

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
        missing = list(set(self.final_fields).difference(cols))
        for col in missing:
            print(col, " is missing, assigning null values")
            self.output_df[col] = None
