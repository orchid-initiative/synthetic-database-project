from abc import ABC, abstractmethod
from configparser import ConfigParser
from synth_data_module import Formatter, SyntheaOutput, modify_row
import datetime as dt
import pandas as pd
import numpy as np
import synth_data_module.mappings as mappings



class HCAIBase(Formatter, ABC):
    def __init__(self, **kwargs):
        self.output_df = pd.DataFrame
        self.synthea_output = SyntheaOutput()
        self.kwargs = kwargs
        self.facility_id = self.kwargs['FacilityID']
        # TODO all_fields and final_fields will be defined in the subclass - I dont know the proper way to handle this
        self.all_fields = pd.DataFrame()
        self.final_fields = pd.DataFrame()

        # Grab the synthea_settings txt file and consume the settings as a dictionary for use as needed
        java_configs = ConfigParser()
        with open("synthea_settings") as stream:
            java_configs.read_string("[SETTINGS]\n" + stream.read())
        self.country_code = java_configs['SETTINGS']['generate.geography.country_code']

    def gather_data(self):
        self.add_demographics()
        self.add_encounters()
        self.add_procedures()
        self.add_other_diagnosis()
        self.hard_coding()
        self.fill_missing()

    def write_data(self, data, filename=None):
        with open(filename or self.suggested_filename(), "w") as f:
            f.write(data)

    def add_demographics(self):
        patients = self.synthea_output.patients_df()
        patients['patient_id'] = patients.iloc[:, 0]
        try:
            patients['Date of Birth'] = patients.iloc[:, 1].apply(lambda x: x.strftime('%m%d%Y'))
            patients['Date of Birth Raw'] = patients.iloc[:, 1].apply(lambda x: x.strftime('%m%d%Y'))
        except AttributeError:
            patients['Date of Birth'] = patients.iloc[:, 1].apply(
                lambda x: dt.datetime.strptime(x, '%Y-%m-%d').strftime('%m%d%Y'))
            patients['Date of Birth Raw'] = patients.iloc[:, 1 ].apply(
                lambda x: dt.datetime.strptime(x, '%Y-%m-%d').strftime('%m%d%Y'))
        patients['Sex'] = patients.iloc[:, 14]
        patients['Ethnicity'] = mappings.ethnicity(patients.iloc[:, 13])
        patients['Race'] = mappings.race(patients.iloc[:, 12])
        patients['Social Security Number'] = patients.iloc[:, 3].fillna('000000001').apply(lambda x: x.replace('-', ''))
        patients['Record Linkage Number'] = patients.iloc[:, 3].fillna('000000001').apply(lambda x: x.replace('-', ''))
        patients['Abstract Record Number'] = patients.iloc[:, 3].fillna('000000001')
        patients['Patient Address - Address Number and Street Name'] = patients.iloc[:, 16]
        patients['Patient Address - City'] = patients.iloc[:, 17]
        patients['Patient Address - State'] = patients.iloc[:, 18]
        patients['Patient Address - County'] = mappings.CAcounty(patients.iloc[:, 19])
        patients['Patient Address - Zip Code'] = patients.iloc[:, 21].fillna('XXXXX')
        patients['Patient Address - Country Code'] = self.country_code
        self.output_df = patients[['patient_id', 'Date of Birth', 'Date of Birth Raw', 'Sex', 'Ethnicity', 'Race',
                                   'Social Security Number', 'Record Linkage Number', 'Abstract Record Number',
                                   'Patient Address - Address Number and Street Name', 'Patient Address - City',
                                   'Patient Address - State', 'Patient Address - County', 'Patient Address - Zip Code',
                                   'Patient Address - Country Code']]
        print('Demographics added.  Shape: ', self.output_df.shape)
        del patients

    @abstractmethod
    def add_encounters(self) -> pd.DataFrame:
        pass

    def add_procedures(self):
        procedures = self.synthea_output.procedures_df(subfields=[0, 3, 4])

        # TODO procedures are not included in the current basic snomed map, find them.  Pass-through for now.
        #  Note that these are also longer and get truncated by field length later!
        #  procedures['Procedure Codes'] = mappings.snomedicdbasicmap(procedures.iloc[:, 4])
        # Reminder that column index 1 here is the column index 3 from the procedures.csv due to our subfields parameter
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
        diagnosis = self.synthea_output.diagnosis_df(subfields=[8, 88, 90])

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

        # The patients are already processed in order, so we can go through them and count unique SSNs to assign an ID
        result_series = pd.Series(0, index=range(len(self.output_df)))
        for i in range(len(self.output_df)):
            subset_series = self.output_df['Social Security Number'].iloc[:i + 1]
            unique_count = 100000000000 + subset_series.nunique()
            result_series.iloc[i] = unique_count
        self.output_df['Patient Identification Number'] = result_series

        dsi_s = pd.Series(np.arange(1000000001, len(self.output_df) + 1000000001))
        self.output_df = pd.concat([self.output_df, dsi_s.rename('Data Set Identification Number')], axis=1)

        count_s = pd.Series(np.arange(1, len(self.output_df) + 1))
        self.output_df = pd.concat([self.output_df, count_s.rename('Counter')], axis=1)

        print('Hard-coded fields added.  Shape: ', self.output_df.shape)

    def fill_missing(self):
        cols = list(self.output_df.columns)
        missing = list(set(self.final_fields['name'].tolist()).difference(cols))
        none_s = pd.Series([None for _ in range(len(self.output_df.index))])
        for col in missing:
            print(col, "is missing, assigning null values")
            # self.output_df[col] = None
            self.output_df = pd.concat([self.output_df, none_s.rename(col)], axis=1)
