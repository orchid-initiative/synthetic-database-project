from abc import ABC, abstractmethod
from configparser import ConfigParser
from io import StringIO
from synth_data_module import Formatter, SyntheaOutput, modify_procedure_row, modify_diagnosis_row, calculate_age
import datetime as dt
import os
import pandas as pd
import numpy as np
import synth_data_module.mappings as mappings
import time


class HCAIBase(Formatter, ABC):
    def __init__(self, timers, **kwargs):
        self.output_df = pd.DataFrame
        self.timers = timers
        self.synthea_output = SyntheaOutput()
        self.kwargs = kwargs
        # TODO all_fields and final_fields will be defined in the subclass - I dont know the proper way to handle this
        self.all_fields = pd.DataFrame()
        self.final_fields = pd.DataFrame()

        # Grab the synthea_settings txt file and consume the settings as a dictionary for use as needed
        java_configs = ConfigParser()
        study = self.kwargs['Study']
        if study:
            settingsfile = f'StudyOverrides/{study}/synthea_settings'
        else:
            settingsfile = "synthea_settings"
        with open(settingsfile) as stream:
            java_configs.read_string("[SETTINGS]\n" + stream.read())
        self.country_code = java_configs['SETTINGS']['generate.geography.country_code']

    def gather_data(self):
        self.add_demographics()
        self.add_encounters()
        self.add_procedures()
        self.add_other_diagnosis()
        self.hard_coding()
        self.fill_missing()
        self.type_data()

    def write_data(self, data, filename=None):
        filename = (filename or self.suggested_filename())
        with open(filename, "w") as f:
            f.write(data)

        if self.kwargs['Yearly']:
            self.write_yearly_data(data, filename)

    def write_yearly_data(self, data, filename):
        # Create the directory to put the yearly files in and identify their base names
        basename = os.path.basename(filename).split(".")[0]
        directory = os.path.abspath(filename).split(".")[0]
        os.mkdir(directory)

        all_data = pd.read_csv(StringIO(data), dtype=str)
        year_range = list(map(int, self.kwargs['YearRange'].split("-")))
        for year in range(year_range[0], year_range[1]+1):
            sbuffer = StringIO()
            all_data[all_data['dsch_yr'] == str(year)].to_csv(sbuffer, index=False)
            yearly_filename = f'{directory}/{basename}_{year}.csv'
            with open(yearly_filename, "w") as f:
                f.write(sbuffer.getvalue())

    def add_demographics(self):
        demo_start = time.time()
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
        print('Demographics added. Shape: ', self.output_df.shape)

        del patients
        self.timers.record_time('Demographics', demo_start)

    @abstractmethod
    def add_encounters(self) -> pd.DataFrame:
        pass

    def add_procedures(self):
        proc_start = time.time()
        procedures = self.synthea_output.procedures_df(subfields=[0, 3, 4])

        # TODO procedures are not included in the current basic snomed map, find them.  Pass-through for now.
        #  Note that these are also longer and get truncated by field length later!
        #  procedures['Procedure Codes'] = mappings.snomedicdbasicmap(procedures.iloc[:, 2])
        # Reminder that column index 1 here is the column index 3 from the procedures.csv due to our subfields parameter
        procedures['encounter_id'] = procedures.iloc[:, 1]

        # We do have some static LARC-related mappings, so try those, but for most results, its a passthrough of SNOMED
        procedures['Procedure Codes'] = mappings.larcsnomedmap(procedures.iloc[:, 2])

        # Similar to encounters, we handle either date formatting here
        try:
            procedures['Procedure Dates'] = procedures.iloc[:, 0].apply(lambda x: x.strftime('%Y%m%d'))
        except TypeError:
            procedures['Procedure Dates'] = procedures.iloc[:, 0].apply(
                lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d'))

        # Grab Admission Date from output_df
        procedures = procedures.merge(self.output_df[['encounter_id', 'Admission Date']],
                                      how='left', on='encounter_id')
        procedures['Procedure Days'] = procedures.apply(
            lambda x: calculate_age(x['Admission Date'], x['Procedure Dates'], "staydays"), axis=1)

        # Group codes by encounter_id to consolidate to one row for each encounter - this makes later merges easier
        print('SUB-CHECK - Procedures Shape pre group: ', procedures.shape)
        procedures = procedures.groupby('encounter_id').agg(lambda x: tuple(x)).reset_index()

        print('SUB-CHECK - Procedures Shape post group: ', procedures.shape)

        # Assign some MSDRG codes used in the LARC study.  Ordered so the most accurate one assigns.
        procedures.loc[procedures['Procedure Codes'].apply(lambda x: '66348005' in x),              # Parturition
                       ['Medicare Severity-Diagnosis Related Group', 'Major Diagnostic Category']] = ['807', '14']
        procedures.loc[procedures['Procedure Codes'].apply(lambda x: '85548006' in x),              # Episiotomy
                       ['Medicare Severity-Diagnosis Related Group', 'Major Diagnostic Category']] = ['768', '14']
        procedures.loc[procedures['Procedure Codes'].apply(lambda x: '11466000' in x),              # C-section
                       ['Medicare Severity-Diagnosis Related Group', 'Major Diagnostic Category']] = ['788', '14']

        # Merge procedure code and date into output_df and then do a special formatting operation for the lists
        self.output_df = self.output_df.merge(procedures[['encounter_id', 'Procedure Codes', 'Procedure Dates', 'Procedure Days', 'Medicare Severity-Diagnosis Related Group']],
                                              how='left', on='encounter_id')
        print('Procedures info added.  Shape: ', self.output_df.shape)

        self.output_df = self.output_df.apply(modify_procedure_row, axis=1, args=(
            ['Procedure Codes', 'Procedure Dates', 'Procedure Days'], ['Procedure Code', 'Procedure Date', 'Procedure Days']))
        print('Procedure info formatted.   Shape: ', self.output_df.shape)

        del procedures
        self.timers.record_time('Procedures', proc_start)

    def add_other_diagnosis(self):
        diagnosis_start = time.time()
        # As the file sizes get large, a full read_csv becomes impossible, so we select the columns we want to use and
        # effectively reindex them in the dataframe we are creating (i.e. column 8 in the csv becomes column 0, etc.)
        diagnosis = self.synthea_output.diagnosis_df(subfields=[8, 21, 88, 90])

        # Reminder that column index 0 here is the column index 8 from the CPCSD_Claims.csv due to our usecols parameter
        diagnosis['encounter_id'] = diagnosis.iloc[:, 0]
        diagnosis['coverage_id'] = diagnosis.iloc[:, 1]
        diagnosis['Diagnosis Codes'] = mappings.snomedicdbasicmap(diagnosis.iloc[:, 2])
        diagnosis['Diagnosis Codes'].replace("", np.nan, inplace=True)
        diagnosis.dropna(subset=['Diagnosis Codes'], inplace=True)
        diagnosis['Present on Admission'] = diagnosis.iloc[:, 3]


        # Group up the diagnosis codes by encounter_id
        print('SUB-CHECK - Diagnosis Shape pre group: ', diagnosis.shape)
        diagnosis = diagnosis.groupby(['encounter_id', 'coverage_id']).agg(lambda x: tuple(x)).reset_index()
        print('SUB-CHECK - Diagnosis Shape post group: ', diagnosis.shape)

        # Add in Coverage Type
        coverages = self.synthea_output.coverages_df(subfields=[0, 4])
        coverages['coverage_id'] = coverages.iloc[:, 0]
        coverages['Type of Coverage'] = mappings.cov_to_pay_type(coverages.iloc[:, 1])
        diagnosis = diagnosis.merge(coverages[['coverage_id', 'Type of Coverage']], how='left', left_on='coverage_id',
                                    right_on='coverage_id')

        self.output_df = self.output_df.merge(diagnosis[['Type of Coverage', 'Diagnosis Codes', 'Present on Admission']],
                                              how='left', left_on='encounter_id', right_on=diagnosis.iloc[:, 0])

        print('Diagnosis info added.  Shape: ', self.output_df.shape)

        self.output_df = self.output_df.apply(modify_diagnosis_row, axis=1, args=(
            ['Diagnosis Codes', 'Present on Admission'], ['Diagnosis', 'Present on Admission']))

        del diagnosis
        self.timers.record_time('Diagnoses', diagnosis_start)

    def hard_coding(self):
        hardcoding_start = time.time()

        # Hard code Type of Care to be 1 ("Acute Care") always for now
        care_s = pd.Series([1 for _ in range(len(self.output_df.index))])
        self.output_df = pd.concat([self.output_df, care_s.rename('Type of Care')], axis=1)

        # Display coverage type = 0 for any payer catagory 07,08,09
        self.output_df.loc[self.output_df['Payer Category'].isin(['07', '08', '09']), 'Type of Coverage'] = '0'

        # Display plan codes only for coverage type 1 (HMO), display 0000 for all other
        self.output_df.loc[self.output_df['Type of Coverage'].isin(['0', '2', '3']), 'Plan Code Number'] = '0000'

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
        self.timers.record_time('Hardcoding', hardcoding_start)

    def fill_missing(self):
        cols = list(self.output_df.columns)
        missing = sorted(list(set(self.final_fields['name'].tolist()).difference(cols)))
        none_s = pd.Series([None for _ in range(len(self.output_df.index))])
        print("\n", "Missing Fields: assigning null values", "\n")
        for col in missing:
            print("  ", col)
            # self.output_df[col] = None
            self.output_df = pd.concat([self.output_df, none_s.rename(col)], axis=1)
        print("End Missing Fields")

    def type_data(self):
        self.output_df = self.output_df.convert_dtypes()
