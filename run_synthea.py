from synth_data_module import Synthea, FormatOutput
from log_helpers import log_helpers as log
import time
import os
import glob
import datetime as dt

start = time.time()
log.setSysOut(f'{__file__}_{dt.date.today()}.log')
output_loc = 'output/'
output_cpcds = 'output/cpcds/*'
output_csvs = 'output/csv/*'
output_fhirs = 'output/fhir/*'
output_metadata = 'output/metadata/*'

# Subsequent Synthea runs append data to the CSVs (this is a setting) so we clear out the past output at the start of each
# full run_synthea run.  "formatted_data_DATETIME".csv is the only output that persists between runs
log.printSectionHeader('Clearing Old Local Data')
files0 = glob.glob(output_cpcds)
for f in files0:
    os.remove(f)
files1 = glob.glob(output_csvs)
for f in files1:
    os.remove(f)
files2 = glob.glob(output_fhirs)
for f in files2:
    os.remove(f)
files3 = glob.glob(output_metadata)
for f in files3:
    os.remove(f)

log.printSectionHeader('Running Synthea')
# Todo - how can we make this a relative path more generic for users?  I got "Unable to access jarfile" error without
#   the full path specified.
file_path = os.path.realpath(__file__)
dir = os.path.dirname(file_path)
jar_file = os.path.join(dir, 'synthea-with-dependencies.jar')


# Collect Females
log.printSectionSubHeader('Creating Female Records')
sub_start = time.time()
synthea = Synthea(jar_file,'synthea_settings') # initialize the module
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
FormatOutput('010735',output_loc)
log.printElapsedTime(form_start, "Formatted output created in: ")


log.printSectionSubHeader('Total Elapsed Time')
log.printElapsedTime(start)
