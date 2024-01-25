import datetime as dt
from synth_data_module import HCAIBase, get_procedure_list, get_diagnosis_list, get_morbidity_list, calculate_age
import pandas as pd
import synth_data_module.mappings as mappings
import time
from io import StringIO


class HCAIPDDFormat(HCAIBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        procedure_list = get_procedure_list()
        diagnosis_list = get_diagnosis_list(length=8)
        morbidity_list = get_morbidity_list()

        # Define the fields we will care about
        self.fields_dict = (
                [{'fieldid': 'typcare', 'name': 'Type of Care', 'length': 1},
                 {'fieldid': 'oshpd_id', 'name': 'Facility Identification Number', 'length': 6},  # NeedToFix
                 {'fieldid': 'oshpd_id9', 'name': 'Facility Identification Number Long', 'length': 9},  # NeedToDo
                 {'fieldid': 'hplzip', 'name': 'Hospital Zip Code', 'length': 5},
                 {'fieldid': 'hplcnty', 'name': 'Hospital County', 'length': 2},
                 {'fieldid': 'data_id', 'name': 'Data Set Identification Number', 'length': 10},
                 {'fieldid': 'pat_id', 'name': 'Patient Identification Number', 'length': 12},
                 {'fieldid': 'bthdate', 'name': 'Date of Birth', 'length': 8},
                 {'fieldid': 'dob_raw', 'name': 'Date of Birth Raw', 'length': 8},
                 {'fieldid': 'agdyadm', 'name': 'Age in Days at Admission', 'length': 8},
                 {'fieldid': 'agdydsch', 'name': 'Age in Days at Discharge', 'length': 8},
                 {'fieldid': 'agyradm', 'name': 'Age in Years at Admission', 'length': 8},
                 {'fieldid': 'agyrdsch', 'name': 'Age in Years at Discharge', 'length': 8},
                 {'fieldid': 'agecatadm', 'name': 'Age Range at Admission', 'length': 2},
                 {'fieldid': 'agecatdsch', 'name': 'Age Range at Discharge', 'length': 2},
                 {'fieldid': 'agecatdsch10', 'name': 'Age in Years at Discharge 10', 'length': 2},
                 {'fieldid': 'sex', 'name': 'Sex', 'length': 1},
                 {'fieldid': 'ethncty', 'name': 'Ethnicity', 'length': 2},
                 {'fieldid': 'race1', 'name': 'Race', 'length': 2},
                 {'fieldid': 'race2', 'name': 'Race 2', 'length': 2},  # NeedToDo
                 {'fieldid': 'race3', 'name': 'Race 3', 'length': 2},  # NeedToDo
                 {'fieldid': 'race4', 'name': 'Race 4', 'length': 2},  # NeedToDo
                 {'fieldid': 'race5', 'name': 'Race 5', 'length': 2},  # NeedToDo
                 {'fieldid': 'race_aman', 'name': 'Race American Indian', 'length': 1},  # NeedToDo
                 {'fieldid': 'race_asian', 'name': 'Race Asian', 'length': 1},  # NeedToDo
                 {'fieldid': 'race_black', 'name': 'Race Black', 'length': 1},  # NeedToDo
                 {'fieldid': 'race_nhpi', 'name': 'Race NHPI', 'length': 1},  # NeedToDo
                 {'fieldid': 'race_white', 'name': 'Race White', 'length': 1},  # NeedToDo
                 {'fieldid': 'race_other', 'name': 'Race Other', 'length': 1},  # NeedToDo
                 {'fieldid': 'race_grp', 'name': 'Normalized Ethnicity', 'length': 1},  # NeedToDo
                 {'fieldid': 'admtdate', 'name': 'Admission Date', 'length': 8},
                 {'fieldid': 'admtday', 'name': 'Admission Day of the Week', 'length': 1},
                 {'fieldid': 'admtmth', 'name': 'Admission Month', 'length': 2},
                 {'fieldid': 'qtr_adm', 'name': 'Admission Quarter', 'length': 1},
                 {'fieldid': 'admtyr', 'name': 'Admission Year', 'length': 4},
                 {'fieldid': 'dschdate', 'name': 'Discharge Date', 'length': 8},
                 {'fieldid': 'mth_dsch', 'name': 'Discharge Month', 'length': 2},
                 {'fieldid': 'qtr_dsch', 'name': 'Discharge Quarter', 'length': 1},
                 {'fieldid': 'dsch_yr', 'name': 'Discharge Year', 'length': 4},
                 {'fieldid': 'counter', 'name': 'Counter', 'length': 8},
                 {'fieldid': 'los', 'name': 'Length Of Stay', 'length': 8},
                 {'fieldid': 'los_adj', 'name': 'Adjusted Length of Stay', 'length': 8},
                 {'fieldid': 'srcpo_ns', 'name': 'Point of Origin', 'length': 1},
                 {'fieldid': 'srcroute_ns', 'name': 'Route of Admission', 'length': 1},
                 {'fieldid': 'admtype_ns', 'name': 'Type of Admission', 'length': 1},
                 {'fieldid': 'MDC', 'name': 'Major Diagnostic Category', 'length': 2},  # NeedToDo
                 {'fieldid': 'MSDRG', 'name': 'Medicare Severity-Diagnosis Related Group', 'length': 3},  # NeedToDo
                 {'fieldid': 'cat-code', 'name': 'MS-DRG Category', 'length': 1},  # NeedToDo
                 {'fieldid': 'sev-code', 'name': 'MS-DRG Severity Code', 'length': 1},  # NeedToDo
                 {'fieldid': 'grouper', 'name': 'MS-DRG Grouper Version', 'length': 4},  # NeedToDo
                 {'fieldid': 'diag_p', 'name': 'Principal Diagnosis', 'length': 8},
                 {'fieldid': 'poa_p', 'name': 'Present on Admission for Principal Diagnosis', 'length': 1}]
                + diagnosis_list
                + procedure_list
                + morbidity_list +
                [{'fieldid': 'ssn', 'name': 'Social Security Number', 'length': 9},
                 {'fieldid': 'rln', 'name': 'Record Linkage Number', 'length': 9},  # Set to SSN
                 {'fieldid': 'disp', 'name': 'Disposition of Patient', 'length': 2},
                 {'fieldid': 'charge', 'name': 'Total Charges', 'length': 8},
                 {'fieldid': 'charge_adj', 'name': 'Total Charges Adjusted', 'length': 8},  # Set to Total Charges
                 {'fieldid': 'abstrec', 'name': 'Abstract Record Number', 'length': 12},  # Set to SSN
                 {'fieldid': 'dnr', 'name': 'Prehospital Care & Resuscitation - DNR Order', 'length': 1},
                 {'fieldid': 'pay_cat', 'name': 'Payer Category', 'length': 2},
                 {'fieldid': 'pay_type', 'name': 'Type of Coverage', 'length': 1},
                 {'fieldid': 'pay_plan', 'name': 'Plan Code Number', 'length': 4},
                 {'fieldid': 'pls_abbr', 'name': 'Preferred Language Spoken', 'length': 3},
                 {'fieldid': 'pls_wrtin', 'name': 'Preferred Language Spoken Write In', 'length': 24},
                 {'fieldid': 'patcnty', 'name': 'Patient Address - County', 'length': 2},
                 {'fieldid': 'patzip', 'name': 'Patient Address - Zip Code', 'length': 5},
                 ])
        self.exclude_columns = ['Procedure Codes', 'Procedure Dates', 'Diagnosis Codes',
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
        return f'{self.synthea_output.output_loc}/formatted_data/HCAIPDD/{ftype}_HCAIPDD_' \
               f'{date_time.strftime("%m-%d-%Y_%H%M")}.{fextension}'

    def format_data(self):
        # StringIO acts like a file object, but collects its output in
        # a string instead of writing to a file.
        sbuffer = StringIO()
        df = self.output_df.copy()
        if self.kwargs['Verbose']:
            df[self.final_fields['name'].tolist()].to_csv(sbuffer, index=False)
        else:
            df.rename(columns=dict(zip(self.all_fields["name"], self.all_fields["fieldid"])), inplace=True)
            df[self.final_fields['fieldid'].tolist()].to_csv(sbuffer, index=False)
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
            encounters['Admission Date'] = encounters.iloc[:, 1].apply(lambda x: x.strftime('%m%d%Y'))
            encounters['Discharge Date'] = encounters.iloc[:, 2].apply(lambda x: x.strftime('%m%d%Y'))
        except TypeError:
            encounters['Admission Date'] = encounters.iloc[:, 1].apply(
                lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').strftime('%m%d%Y'))
            encounters['Discharge Date'] = encounters.iloc[:, 2].apply(
                lambda x: dt.datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ').strftime('%m%d%Y'))
        # Pandas dayofweek is indexed starting 2 days before the desired index for HCAI format, so we add 2 and mod 7
        # Pandas dayofweek is indexed starting 2 days before the desired index for HCAI format, so we add 2 and mod 7
        encounters['Admission Day of the Week'] = encounters.iloc[:, 1].apply(
            lambda x: (pd.to_datetime(x).dayofweek + 2) % 7).astype(object)
        encounters['Admission Month'] = pd.to_datetime(encounters.iloc[:, 1]).dt.month.astype(object)
        encounters['Admission Quarter'] = pd.to_datetime(encounters.iloc[:, 1]).dt.quarter.astype(object)
        encounters['Admission Year'] = pd.to_datetime(encounters.iloc[:, 1]).dt.year.astype(object)
        encounters['Discharge Month'] = pd.to_datetime(encounters.iloc[:, 2]).dt.month.astype(object)
        encounters['Discharge Quarter'] = pd.to_datetime(encounters.iloc[:, 2]).dt.quarter.astype(object)
        encounters['Discharge Year'] = pd.to_datetime(encounters.iloc[:, 2]).dt.year.astype(object)

        if self.kwargs['YearRange']:
            year_range = list(map(int, self.kwargs['YearRange'].split("-")))
            encounters = encounters[(encounters['Discharge Year'] >= year_range[0])
                                    & (encounters['Discharge Year'] <= year_range[1])]

        # encounters['Principal Diagnosis'] = encounters.iloc[:, 13]  # Needs mapping for ICD-10
        encounters['Principal Diagnosis'] = mappings.snomedicdbasicmap(encounters.iloc[:, 13])
        encounters['Total Charges'] = encounters.iloc[:, 11].apply(lambda x: str(min(int(x.split('.')[0]), 9999999)))
        encounters['Total Charges Adjusted'] = encounters.iloc[:, 11].apply(lambda x: str(min(int(x.split('.')[0]), 9999999)))
        print('SUB-CHECK - Encounters Shape: ', encounters.shape)

        # Prepare and merge organizations name as Facility Name (replace IDs with real names) into encounters
        organizations = self.synthea_output.organizations_df()
        organizations['organization_id'] = organizations.iloc[:, 0]
        organizations['Facility Identification Number'] = mappings.hcai(organizations.iloc[:, 1], length=6)
        organizations['Facility Identification Number Long'] = mappings.hcai(organizations.iloc[:, 1], length=9)
        organizations['Hospital County'] = mappings.CAcity(organizations.iloc[:, 3])
        organizations['Hospital Zip Code'] = organizations.iloc[:, 5].apply(lambda x: x[:5])
        encounters = encounters.merge(organizations[['organization_id', 'Hospital County', 'Hospital Zip Code',
                                      'Facility Identification Number', 'Facility Identification Number Long']],
                                      how='left', left_on='organization_id', right_on='organization_id')
        print('SUB-CHECK - Facility  merged.  Encounters Shape: ', encounters.shape)

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
        observations['Preferred Language Spoken Write In'] = observations.iloc[:, 2]
        observations['Preferred Language Spoken'] = mappings.language(observations.iloc[:, 2])
        observations = observations.loc[observations['description'] == 'Preferred language']
        encounters = encounters.merge(observations[['encounter_id', 'Preferred Language Spoken Write In',
                                                    'Preferred Language Spoken']],
                                      how='left', left_on='encounter_id', right_on='encounter_id')
        print('SUB-CHECK - observations and language merged.  Encounters Shape: ', encounters.shape)

        # Merge the encounters dataframe into self.output_df, keeping only the fields we care about
        self.output_df = self.output_df.merge(encounters[[
            'encounter_id', 'Admission Date', 'Admission Day of the Week', 'Admission Month', 'Admission Quarter',
            'Admission Year', 'Discharge Date', 'Discharge Month', 'Discharge Quarter', 'Discharge Year',
            'Principal Diagnosis', 'Total Charges', 'Total Charges Adjusted', 'Payer Category', 'Hospital County',
            'Hospital Zip Code', 'Facility Identification Number', 'Facility Identification Number Long',
            'Preferred Language Spoken Write In', 'Preferred Language Spoken']],
            how='left', left_on='patient_id', right_on=encounters.iloc[:, 3])
        print('Encounter info added.  Shape: ', self.output_df.shape)
        self.output_df = self.output_df.dropna(subset=['encounter_id']).reset_index(drop=True)
        print('Patients with no encounters of desired type dropped.  Shape: ', self.output_df.shape)

        self.output_df['Age in Days at Admission'] = self.output_df.apply(
            lambda x: calculate_age(x['Date of Birth'], x['Admission Date'], "agedays"), axis=1)
        self.output_df['Age in Days at Discharge'] = self.output_df.apply(
            lambda x: calculate_age(x['Date of Birth'], x['Discharge Date'], "agedays"), axis=1)
        self.output_df['Age in Years at Admission'] = self.output_df.apply(
            lambda x: calculate_age(x['Date of Birth'], x['Admission Date'], "years"), axis=1)
        self.output_df['Age in Years at Discharge'] = self.output_df.apply(
            lambda x: calculate_age(x['Date of Birth'], x['Discharge Date'], "years"), axis=1)
        self.output_df['Age Range at Admission'] = self.output_df.apply(
            lambda x: calculate_age(x['Date of Birth'], x['Admission Date'], "range5"), axis=1)
        self.output_df['Age Range at Discharge'] = self.output_df.apply(
            lambda x: calculate_age(x['Date of Birth'], x['Discharge Date'], "range5"), axis=1)
        self.output_df['Age in Years at Discharge 10'] = self.output_df.apply(
            lambda x: calculate_age(x['Date of Birth'], x['Discharge Date'], "range10"), axis=1)
        self.output_df['Length Of Stay'] = self.output_df.apply(
            lambda x: calculate_age(x['Admission Date'], x['Discharge Date'], "staydays"), axis=1)
        self.output_df['Adjusted Length Of Stay'] = self.output_df.apply(
            lambda x: calculate_age(x['Admission Date'], x['Discharge Date'], "adjstaydays"), axis=1)
        print('Added age and duration statistics for admission and discharge.  Shape: ', self.output_df.shape)

        del encounters
