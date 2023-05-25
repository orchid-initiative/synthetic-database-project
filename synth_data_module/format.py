import subprocess
import time
import datetime
import pandas as pd
import numpy as np
import synth_data_module.mappings as mappings

class Format_Output():
    def __init__(self, facility_id, output_loc):
        self.output_loc = output_loc
        self.facility_id = facility_id
        self.final_fields = ['Type of Care','Facility Identification Number','Date of Birth','Sex','Ethnicity','Race',
                        'Not in Use','Admission Date','Point of Origin','Route of Admission','Type of Admission',
                        'Discharge Date','Principal Diagnosis','Present on Admission for Principal Diagnosis',
                        'Other Diagnosis and Present on Admission','Principal Procedure Code',
                        'Principal Procedure Date','Other Procedure Codes and Other Procedure Dates',
                        'External Casues of Morbidity and Present on Admission','Patient SSN',
                        'Disposition of Patient','Total Charges','Abstract Record Number (Optional)',
                        'Prehospital Care & Resuscitation - DNR Order','Payer Category','Type of Covereage',
                        'Plan Code Number','Preferred Spoken Language','Patient Address - Address Number and Street Name',
                        'Patient Address - City','Patient Address - State','Patient Address - Zip Code',
                        'Patient Address - Country Code','Patient Address - Homeless Indicator']
        self.add_demographics()
        self.add_encounters()
        self.hard_coding()
        self.fill_missing()
        self.output_df[self.final_fields].to_csv(f'{output_loc}/../formatted_data.csv', index=False)

    def add_demographics(self, ):
        patients = pd.read_csv(f'{self.output_loc}/patients.csv', dtype = str, header=None)
        patients['patient_id'] = patients.iloc[:,0]
        patients['Date of Birth'] = patients.iloc[:,1].apply(lambda x: x.replace('-',''))
        patients['Sex'] = patients.iloc[:,14]
        patients['Ethnicity'] = mappings.ethnicity(patients.iloc[:,12])
        patients['Race'] = mappings.race(patients.iloc[:,13])
        patients['Patient SSN'] = patients.iloc[:,3].fillna('000000001').apply(lambda x: x.replace('-',''))
        patients['Patient Address - Address Number and Street Name'] = patients.iloc[:,16]
        patients['Patient Address - City'] = patients.iloc[:,17]
        patients['Patient Address - State'] = patients.iloc[:,18]
        patients['Patient Address - Zip Code'] = patients.iloc[:,20].fillna('XXXXX')
        self.output_df = patients[['patient_id', 'Date of Birth', 'Sex','Ethnicity','Race',
                                    'Patient SSN','Patient Address - Address Number and Street Name',
                                    'Patient Address - City','Patient Address - State',
                                    'Patient Address - Zip Code']]
        print('Demographics added.  Shape: ', self.output_df.shape)
        del patients

    def add_encounters(self):
        encounters = pd.read_csv(f'{self.output_loc}/encounters.csv', dtype = str, parse_dates = [1,2], header=None)
        encounters['encounter_id'] = encounters.iloc[:,0]
        encounters['EncounterClass'] = encounters.iloc[:,7]
        encounters = encounters.loc[encounters['EncounterClass']=='inpatient',:].copy()
        encounters['Admission Date'] = encounters.iloc[:,1].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d'))
        encounters['Discharge Date'] = encounters.iloc[:,2].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d'))
        encounters['Principal Diagnosis'] = encounters.iloc[:,13] # Needs mapping for ICD-10
        encounters['Total Charges'] = encounters.iloc[:,11].apply(lambda x: min(int(x.split('.')[0]), 9999999))
        self.output_df = self.output_df.merge(encounters[['encounter_id','Admission Date',
                                                        'Discharge Date','Principal Diagnosis',
                                                        'Total Charges']], 
                                                how = 'left', left_on = 'patient_id', right_on = encounters.iloc[:,3])
        print('Encounter info added.  Shape: ', self.output_df.shape)
        del encounters

    def hard_coding(self):
        self.output_df['Type of Care'] = 1
        self.output_df['Facility Identification Number'] = self.facility_id
        self.output_df['Not in Use'] = '     '
        self.output_df['Type of Admission'] = np.random.choice(['1','2','3','4','5','9'], size=len(self.output_df))
        self.output_df['Point of Origin'] = np.random.choice(['1','2','4','5','6','8','D','E','F','G'])
        self.output_df.loc[self.output_df['Type of Admission']=='4','Point of Origin'] = np.random.choice(['5','6'])
        self.output_df['Route of Admission'] = '3'
        self.output_df.loc[self.output_df['Type of Admission']=='1','Route of Admission'] = np.random.choice(['1','2'])
        self.output_df['Disposition of Patient'] = np.random.choice(mappings.disposition(), size = len(self.output_df))
        self.output_df['Prehospital Care & Resuscitation - DNR Order'] = np.random.choice(['Y','N'], size = len(self.output_df))
        self.output_df['Abstract Record Number (Optional)'] = np.arange(1, len(self.output_df) + 1)
        print('Hard-coded fields added.  Shape: ', self.output_df.shape)

    def fill_missing(self):
        cols = list(self.output_df.columns)
        missing = list(set(self.final_fields).difference(cols))
        for col in missing:
            self.output_df[col] = None


