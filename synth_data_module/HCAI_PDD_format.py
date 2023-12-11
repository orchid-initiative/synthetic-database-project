import datetime as dt
from synth_data_module import HCAIBase, get_procedure_list, get_diagnosis_list, get_morbidity_list
import pandas as pd
import synth_data_module.mappings as mappings
import time


class HCAIPDDFormat(HCAIBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        procedure_list = get_procedure_list()
        diagnosis_list = get_diagnosis_list(length=8)
        morbidity_list = get_morbidity_list()
        self.fields_dict = (
                [{'fieldid': 'typcare', 'name': 'Type of Care', 'length': 1},
                 {'fieldid': 'oshpd_id', 'name': 'Facility Identification Number', 'length': 6},
                 {'fieldid': 'oshpd_id9', 'name': 'Facility Identification Number Long', 'length': 9},  # NeedToDo
                 {'fieldid': 'hplzip', 'name': 'Hospital Zip Code', 'length': 5},  # NeedToDo
                 {'fieldid': 'hplcnty', 'name': 'Hospital County', 'length': 2},  # NeedToDo
                 {'fieldid': 'data_id', 'name': 'Data Set Identification Number', 'length': 10},  # NeedToDo
                 {'fieldid': 'pat_id', 'name': 'Patient Identification Number', 'length': 12},  # NeedToDo
#                {'fieldid': '', 'name': 'Facility Name', 'length': 0},
                 {'fieldid': 'bthdate', 'name': 'Date of Birth', 'length': 8},
                 {'fieldid': 'dob_raw', 'name': 'Date of Birth Raw', 'length': 8},
                 {'fieldid': 'agdyadm', 'name': 'Age in Days at Admission', 'length': 8},  # NeedToDo
                 {'fieldid': 'agdydsch', 'name': 'Age in Days at Discharge', 'length': 8},  # NeedToDo
                 {'fieldid': 'agyradm', 'name': 'Age in Years at Admission', 'length': 8},  # NeedToDo
                 {'fieldid': 'agyrdsch', 'name': 'Age in Years at Discharge', 'length': 8},  # NeedToDo
                 {'fieldid': 'agecatadm', 'name': 'Age Range at Admission', 'length': 2},  # NeedToDo
                 {'fieldid': 'agecatdsch', 'name': 'Age Range at Discharge', 'length': 2},  # NeedToDo
                 {'fieldid': 'agecatdsch10', 'name': 'Age in Years at Discharge 10', 'length': 2},  # NeedToDo
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
                 {'fieldid': '', 'name': 'Not in Use 1', 'length': 5},
                 {'fieldid': 'admtdate', 'name': 'Admission Date', 'length': 8},
                 {'fieldid': 'admtday', 'name': 'Admission Day of the Week', 'length': 1},
                 {'fieldid': 'admtmth', 'name': 'Admission Month', 'length': 2},
                 {'fieldid': 'qtr_adm', 'name': 'Admission Quarter', 'length': 1},
                 {'fieldid': 'admtyr', 'name': 'Admission Year', 'length': 4},
                 {'fieldid': 'dschdate', 'name': 'Discharge Date', 'length': 8},
                 {'fieldid': 'mth_dsch', 'name': 'Discharge Month', 'length': 2},
                 {'fieldid': 'qtr_dsch', 'name': 'Discharge Quarter', 'length': 1},
                 {'fieldid': 'dsch_yr', 'name': 'Discharge Year', 'length': 4},
                 {'fieldid': 'counter', 'name': 'Counter', 'length': 8},  # NeedToDo
                 {'fieldid': 'los', 'name': 'Length Of Stay', 'length': 8},  # NeedToDo
                 {'fieldid': 'los_adj', 'name': 'Adjusted Length of Stay', 'length': 8},  # NeedToDo
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
                + diagnosis_list +
                [{'fieldid': '', 'name': 'Diagnosis Codes', 'length': 250},
                 {'fieldid': '', 'name': 'Present on Admission', 'length': 100}]
                + procedure_list +
                [{'fieldid': '', 'name': 'Procedure Codes', 'length': 375},
                 {'fieldid': '', 'name': 'Procedure Dates', 'length': 375}]
                + morbidity_list +
                [{'fieldid': '', 'name': 'External Causes of Morbidity and Present on Admission', 'length': 96,
                  'justification': 'left'},
                 {'fieldid': 'ssn', 'name': 'Social Security Number', 'length': 9},
                 {'fieldid': 'rln', 'name': 'Record Linkage Number', 'length': 9},
                 {'fieldid': 'disp', 'name': 'Disposition of Patient', 'length': 2},
                 {'fieldid': 'charge', 'name': 'Total Charges', 'length': 8},
                 {'fieldid': 'charge_adj', 'name': 'Total Charges Adjusted', 'length': 8},  # NeedToDo
                 {'fieldid': 'abstrec', 'name': 'Abstract Record Number', 'length': 12},
                 {'fieldid': 'dnr', 'name': 'Prehospital Care & Resuscitation - DNR Order', 'length': 1},
                 {'fieldid': 'pay_cat', 'name': 'Payer Category', 'length': 2},
                 {'fieldid': 'pay_type', 'name': 'Type of Coverage', 'length': 1},
                 {'fieldid': 'pay_plan', 'name': 'Plan Code Number', 'length': 4},
                 {'fieldid': 'pls_abbr', 'name': 'Preferred Language Spoken', 'length': 3},
                 {'fieldid': 'pls_wrtin', 'name': 'Preferred Language Spoken Write In', 'length': 24},
                 {'fieldid': '', 'name': 'Patient Address - Address Number and Street Name', 'length': 40},
                 {'fieldid': '', 'name': 'Patient Address - City', 'length': 30},
                 {'fieldid': 'patcnty', 'name': 'Patient Address - County', 'length': 2},  # NeedToDo
                 {'fieldid': '', 'name': 'Patient Address - State', 'length': 2},
                 {'fieldid': 'patzip', 'name': 'Patient Address - Zip Code', 'length': 5},
                 {'fieldid': '', 'name': 'Patient Address - Country Code', 'length': 2},
                 {'fieldid': '', 'name': 'Patient Address - Homeless Indicator', 'length': 1},
                 {'fieldid': '', 'name': 'Not in Use 2', 'length': 356}
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
        return f'{self.synthea_output.output_loc}/formatted_data/HCAIPDD/{ftype}_HCAIPDD_' \
               f'{date_time.strftime("%m-%d-%Y_%H%M")}.{fextension}'

    def add_encounters(self):
        encounters = self.synthea_output.encounters_df()
        encounters['encounter_id'] = encounters.iloc[:, 0]
        encounters['organization_id'] = encounters.iloc[:, 4]
        encounters['payer_id'] = encounters.iloc[:, 6]
        encounters['EncounterClass'] = encounters.iloc[:, 7]
        print(self.kwargs)
        print(self.kwargs['EncounterType'])
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

        # Merge the encounters dataframe into self.output_df, keeping only the fields we care about
        self.output_df = self.output_df.merge(encounters[[
            'encounter_id', 'Admission Date', 'Admission Day of the Week', 'Admission Month', 'Admission Quarter',
            'Admission Year', 'Discharge Date', 'Discharge Month', 'Discharge Quarter', 'Discharge Year',
            'Principal Diagnosis', 'Total Charges', 'Payer Category', 'Facility Name']],
            how='left', left_on='patient_id', right_on=encounters.iloc[:, 3])
        print('Encounter info added.  Shape: ', self.output_df.shape)
        self.output_df = self.output_df.dropna(subset=['encounter_id']).reset_index(drop=True)
        print('Patients with no encounters of desired type dropped.  Shape: ', self.output_df.shape)
        del encounters
