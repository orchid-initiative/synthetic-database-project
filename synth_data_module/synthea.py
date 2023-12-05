import subprocess
import time
import datetime as dt
import pandas as pd


class SyntheaOutput:
    def __init__(self):
        self.output_loc = "output/"

    def patients_df(self) -> pd.DataFrame:
        return pd.read_csv(f'{self.output_loc}/csv/patients.csv', dtype=str, header=0)

    # As the CSV files get large, a full read_csv becomes impractical, so we select the columns we want to use and
    # effectively reindex them in the dataframe we are creating (i.e. column 3 in the csv becomes new column 1, etc.)
    def encounters_df(self, subfields: list = None) -> pd.DataFrame:
        return pd.read_csv(f'{self.output_loc}/csv/encounters.csv', dtype=str, parse_dates=[1, 2], header=0,
                           usecols=subfields)

    def procedures_df(self, subfields: list = None) -> pd.DataFrame:
        return pd.read_csv(f'{self.output_loc}/csv/procedures.csv', dtype=str, parse_dates=[0, 1], header=0,
                           usecols=subfields)

    def diagnosis_df(self, subfields: list = None) -> pd.DataFrame:
        return pd.read_csv(f'{self.output_loc}/cpcds/CPCDS_Claims.csv', dtype=str, header=0, usecols=subfields)

    def organizations_df(self, subfields: list = None) -> pd.DataFrame:
        return pd.read_csv(f'{self.output_loc}/csv/organizations.csv', dtype=str, parse_dates=[1, 2], header=0)

    def payers_df(self, subfields: list = None) -> pd.DataFrame:
        return pd.read_csv(f'{self.output_loc}/csv/payers.csv', dtype=str, parse_dates=[1, 2], header=0)


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

    # used if you want to focus on one area - one can also specify hospital list in overrides/hospitals file in the Jar
    def specify_city(self, state=None, city=None):
        if city:
            self.java_command = self.java_command + f'  {state}  {city}'
        elif state:
            self.java_command = self.java_command + f'  {state}'

    def parse_city(self, specify_city=None):
        city = None
        state = None
        if specify_city:
            if len(specify_city.split(",")) == 2:
                city = str(specify_city.split(",")[0])
                state = str(specify_city.split(",")[1])
                print("Overriding default location Massachusetts to city, state: %s, %s " % (city, state))
            else:
                state = str(specify_city.split(",")[0])
                print("Overriding default location Massachusetts to state %s " % state)
        return city, state


    def run_synthea(self):
        # Split by double space to allow for multi-word city names (that are separated by 1 space).  It's very likely
        # there is a more elegant way to do this though.
        java_command_list = self.java_command.split('  ')
        child = subprocess.Popen(java_command_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output_str = child.stdout.read().decode()  # decode converts from bytes to string object
        timestamp = time.time()
        date_time = dt.datetime.fromtimestamp(timestamp)
        with open(f'logs/full_synthea_stdout_{date_time.strftime("%d-%m-%Y_%H%M%S")}.txt', 'w') as output:
            output.write(output_str)
        run_options = output_str[output_str.index('Running with options'):output_str.index(' -- ') - 2]
        total_records = output_str[output_str.index('Records: '):output_str.index('RNG')]
        print(run_options, total_records, sep='\n\n')
