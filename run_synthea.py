from synth_data_module import Synthea, FormatOutput, clear_old_files, parse_args
from log_helpers import log_helpers as log
import time
import os
import datetime as dt

start = time.time()
log.setSysOut(f'{__file__}_{dt.date.today()}.log')
output_loc = 'output/'

# Subsequent Synthea runs append data to the CSVs (this is a setting) so we clear out the past output at the start of
# each full run_synthea run.  "formatted_data_DATETIME".csv is the only output that persists between runs
log.printSectionHeader('Clearing Old Local Data')
clear_old_files()

# Identify the path for the synthea java jar
file_path = os.path.realpath(__file__)
directory = os.path.dirname(file_path)
jar_file = os.path.join(directory, 'synthea-with-dependencies.jar')

# Run Synthea with global parameters and run-specific parameters
encounter_type = parse_args()
log.printSectionHeader('Running Synthea')

# Collect Females
log.printSectionSubHeader('Creating Female Records')
sub_start = time.time()
synthea = Synthea(jar_file, 'synthea_settings')  # initialize the module
synthea.specify_popSize(40)
synthea.specify_gender('F')
# synthea.specify_city('California', 'Pasadena')
synthea.run_synthea()
log.printElapsedTime(sub_start, "Females created in: ")

# Collect Males
'''log.printSectionSubHeader('Creating Male Records')
sub_start = time.time()
synthea = Synthea(jar_file, 'synthea_settings') # initialize the module
synthea.specify_popSize(1220)
synthea.specify_gender('M')
synthea.run_synthea()
log.printElapsedTime(sub_start, "Males created in: ")'''

# Format data to our desired layout
log.printSectionHeader('Formatting Data')
form_start = time.time()
FormatOutput('010735', output_loc, encounter_type)
log.printElapsedTime(form_start, "Formatted output created in: ")


log.printSectionSubHeader('Total Elapsed Time')
log.printElapsedTime(start)
