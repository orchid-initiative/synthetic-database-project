import datetime as dt
from synth_data_module import HCAIBase, get_procedure_list, get_diagnosis_list
import pandas as pd
import numpy as np
import synth_data_module.mappings as mappings
import time
from io import StringIO


class HCAIInpatientFormat(HCAIBase):
    def __init__(self, timers, **kwargs):
        super().__init__(timers, **kwargs)

        procedure_list = get_procedure_list()
        diagnosis_list = get_diagnosis_list(length=7)

        # Define the fields we will care about
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
                 {'name': 'Abstract Record Number', 'length': 12, 'justification': 'left'},
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
        self.exclude_columns = ['Facility Name', 'Procedure Codes', 'Procedure Dates', 'Diagnosis Codes',
                                'Present on Admission']
        self.all_fields = pd.DataFrame.from_dict(self.fields_dict)
        self.final_fields = self.all_fields.drop(
            self.all_fields[self.all_fields['name'].isin(self.exclude_columns)].index)

    def suggested_filename(self) -> str:
        if "CSV" in self.kwargs['FormatType']:
            ftype = "csv"
            fextension = "csv"
        else:
            ftype = "fw"
            fextension = "txt"
        date_time = dt.datetime.fromtimestamp(time.time())
        return f'{self.synthea_output.output_loc}/formatted_data/HCAIInpatient/{ftype}_HCAIInpatient_' \
               f'{date_time.strftime("%m-%d-%Y_%H%M")}.{fextension}'

    def format_data(self):
        # StringIO acts like a file object, but collects its output in
        # a string instead of writing to a file.
        sbuffer = StringIO()
        df = self.output_df.copy()

        # CSV data formatting
        if "CSV" in self.kwargs['FormatType']:
            if self.kwargs['Verbose']:
                df[self.all_fields['name'].tolist()].to_csv(sbuffer, index=False)
            else:
                df[self.final_fields['name'].tolist()].to_csv(sbuffer, index=False)

        # Fixed width data formatting
        else:
            df = df[self.final_fields['name'].tolist()]
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
            np.savetxt(sbuffer, df, fmt=formats, delimiter='')

        # getvalue() returns the string built up inside of the StringIO.
        return sbuffer.getvalue()

    def add_encounters(self):
        encounters = self.synthea_output.encounters_df()
        encounters['encounter_id'] = encounters.iloc[:, 0]
        encounters['organization_id'] = encounters.iloc[:, 4]
        encounters['payer_id'] = encounters.iloc[:, 6]
        encounters['EncounterClass'] = encounters.iloc[:, 7]
        if self.kwargs['EncounterType']:
            encounters = encounters.loc[encounters['EncounterClass'] == self.kwargs['EncounterType'], :].copy()

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
        organizations = self.synthea_output.organizations_df()
        organizations['organization_id'] = organizations.iloc[:, 0]
        organizations['Facility Name'] = organizations.iloc[:, 1]
        encounters = encounters.merge(organizations[['organization_id', 'Facility Name']], how='left',
                                      left_on='organization_id', right_on='organization_id')
        print('SUB-CHECK - Facility Name merged.  Encounters Shape: ', encounters.shape)

        # Prepare and merge payers info (replace IDs with real payer data) into encounters
        payers = self.synthea_output.payers_df()
        payers['payer_id'] = payers.iloc[:, 0]
        payers['Payer Category'] = payers.apply(mappings.payer_category, axis=1).astype(str)
        encounters = encounters.merge(payers[['payer_id', 'Payer Category']], how='left', left_on='payer_id',
                                      right_on='payer_id')
        print('SUB-CHECK - Payers and codes merged.  Encounters Shape: ', encounters.shape)

        # Prepare and merge observations info (for language) into encounters
        observations = self.synthea_output.observations_df(subfields=[2, 5, 6])
        observations['encounter_id'] = observations.iloc[:, 0]
        observations['description'] = observations.iloc[:, 1]
        observations = observations.loc[observations['description'] == 'Preferred language']
        observations['Preferred Language Spoken Write In'] = observations.iloc[:, 2]
        encounters = encounters.merge(observations[['encounter_id', 'Preferred Language Spoken Write In']],
                                      how='left', left_on='encounter_id', right_on='encounter_id')
        print('SUB-CHECK - observations and language merged.  Encounters Shape: ', encounters.shape)

        encounters['Preferred Language Spoken Write In'] = mappings.languagewritein(
            encounters['Preferred Language Spoken Write In'])
        encounters['Preferred Language Spoken'] = mappings.language(encounters['Preferred Language Spoken Write In'])

        # Merge the encounters dataframe into self.output_df, keeping only the fields we care about
        self.output_df = self.output_df.merge(encounters[['encounter_id', 'Admission Date', 'Discharge Date',
                                                          'Principal Diagnosis', 'Total Charges', 'Payer Category',
                                                          'Facility Name']],
                                              how='left', left_on='patient_id', right_on=encounters.iloc[:, 3])
        print('Encounter info added.  Shape: ', self.output_df.shape)
        self.output_df = self.output_df.dropna(subset=['encounter_id']).reset_index(drop=True)
        print('Patients with no encounters of desired type dropped.  Shape: ', self.output_df.shape)
        del encounters
