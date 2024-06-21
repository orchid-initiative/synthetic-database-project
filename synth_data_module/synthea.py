import subprocess
import time
import datetime as dt
import pandas as pd


class SyntheaOutput:
    def __init__(self):
        self.output_loc = "output/"

    @staticmethod
    def optimize_types(df):
        """Optimize the data types of the DataFrame to reduce memory usage."""
        for col in df.select_dtypes(include=['int']).columns:
            df[col] = pd.to_numeric(df[col], downcast='unsigned')
        for col in df.select_dtypes(include=['float']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
        # for col in df.select_dtypes(include=['object']).columns:
        #     num_unique_values = len(df[col].unique())
        #     num_total_values = len(df[col])
        #     if num_unique_values / num_total_values < 0.5:
        #         # Replace null values with a placeholder
        #         df[col] = df[col].fillna('Unknown')
        #         unique_values = df[col].unique()
        #         df[col] = pd.Categorical(df[col], categories=unique_values, ordered=False)
        return df

    def chunk_csv_reader(self, path, parse_dates=None, subfields=None):
        # Initialize an empty DataFrame for procedures
        chunk_size = 100000
        path = f'{self.output_loc}{path}'
        all_chunks = []
        for chunk in pd.read_csv(path, dtype=str, parse_dates=parse_dates, header=0, usecols=subfields,
                                 chunksize=chunk_size):
            chunk = self.optimize_types(chunk)
            all_chunks.append(chunk)
        # Concatenate all chunks into a single DataFrame
        df = pd.concat(all_chunks, ignore_index=True)
        return df

    def patients_df(self) -> pd.DataFrame:
        return self.chunk_csv_reader('/csv/patients.csv')

    # As the CSV files get large, a full read_csv becomes impractical, so we select the columns we want to use and
    # effectively reindex them in the dataframe we are creating (i.e. column 3 in the csv becomes new column 1, etc.)
    def encounters_df(self, subfields: list = None) -> pd.DataFrame:
        return self.chunk_csv_reader('/csv/encounters.csv', parse_dates=[1, 2], subfields=subfields)

    def procedures_df(self, subfields: list = None) -> pd.DataFrame:
        return self.chunk_csv_reader('/csv/procedures.csv', parse_dates=[0, 1], subfields=subfields)

    def diagnosis_df(self, subfields: list = None) -> pd.DataFrame:
        return self.chunk_csv_reader('/cpcds/CPCDS_Claims.csv', subfields=subfields)

    def coverages_df(self, subfields: list = None) -> pd.DataFrame:
        return self.chunk_csv_reader('/cpcds/CPCDS_Coverages.csv', subfields=subfields)

    def organizations_df(self, subfields: list = None) -> pd.DataFrame:
        return self.chunk_csv_reader('/csv/organizations.csv', parse_dates=[1, 2])

    def payers_df(self, subfields: list = None) -> pd.DataFrame:
        return self.chunk_csv_reader('/csv/payers.csv', parse_dates=[1, 2])

    def observations_df(self, subfields: list = None) -> pd.DataFrame:
        return self.chunk_csv_reader('/csv/observations.csv', subfields=subfields)


class Synthea:
    # Intentionally using 2 spaces between args so they can be easily split later for passing into subprocess.Popen for
    # the synthea java run.  (to support city names that contain a single space staying together rather than splitting)
    def __init__(self, jar_file, config_file):
        self.java_command = f'java  -jar  {jar_file}  -c  {config_file}'

    def specify_popsize(self, size):
        self.java_command = self.java_command + f'  -p  {size}'

    def specify_gender(self, gender=None):
        if gender:
            self.java_command = self.java_command + f'  -g  {gender}'

    def specify_age(self, minage, maxage):
        self.java_command = self.java_command + f'  -a  {minage}-{maxage}'

    def specify_module_overrides(self, module_overrides=False, studyfolder=''):
        if module_overrides:
            if studyfolder != '':
                self.java_command = self.java_command + f'  -d  {studyfolder}'
            else:
                self.java_command = self.java_command + f'  -d  StudyOverrides'

    # used if you want to focus on one area - one can also specify hospital list in overrides/hospitals file in the Jar
    def specify_city(self, state=None, city=None):
        if city:
            self.java_command = self.java_command + f'  {state}  {city}'
        elif state:
            self.java_command = self.java_command + f'  {state}'

    def run_synthea(self):
        # Split by double space to allow for multi-word city names (that are separated by 1 space).  It's very likely
        # there is a more elegant way to do this though.
        print(self.java_command)
        java_command_list = self.java_command.split('  ')
        print(java_command_list)
        child = subprocess.Popen(java_command_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output_str = child.stdout.read().decode()  # decode converts from bytes to string object
        timestamp = time.time()
        date_time = dt.datetime.fromtimestamp(timestamp)
        with open(f'logs/full_synthea_stdout_{date_time.strftime("%Y-%m-%d_%H%M%S")}.txt', 'w') as output:
            output.write(output_str)
        run_options = output_str[output_str.index('Running with options'):output_str.index(' -- ') - 2]
        total_records = output_str[output_str.index('Records: '):output_str.index('RNG')]
        print(run_options, total_records, sep='\n\n')
