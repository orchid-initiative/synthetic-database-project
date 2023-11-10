import subprocess
import time
import datetime as dt
import pandas as pd

class SyntheaOutput:
    def procedure_list_file(self)-> str:
        return "procedure_list_file.csv"

    def procedure_df(subfields) -> pd.DataFrame:
        pass

class Synthea:
    # Intentionally using 2 spaces between args so they can be easily split later for passing into subprocess.Popen for
    # the synthea java run.  (to support city names that contain a single space staying together rather than splitting)
    def __init__(self, jar_file, config_file):
        self.java_command = f'java  -jar  {jar_file}  -c  {config_file}'

    def specify_popsize(self, size):
        self.java_command = self.java_command + f'  -p  {size}'

    def specify_gender(self, gender):
        self.java_command = self.java_command + f'  -g  {gender}'

    def specify_age(self, minage, maxage):
        self.java_command = self.java_command + f'  -a  {minage}-{maxage}'

    # used if you want to focus on one area - one can also specify hospital list in overrides/hospitals file in the Jar
    def specify_city(self, state, city=None):
        if city:
            print("I am passing in:"+ f' {state}  "{city}"')
            self.java_command = self.java_command + f'  {state}  {city}'
        else:
            self.java_command = self.java_command + f'  {state}'

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
