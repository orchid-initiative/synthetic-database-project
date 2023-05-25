from synth_data_module import Synthea, Format_Output
from log_helpers import log_helpers as log
import time
import datetime as dt

start = time.time()
log.setSysOut(f'{__file__}_{dt.date.today()}.log')
output_loc = 'output/csv'


log.printSectionHeader('Running Synthea')
# Todo - how can we make this a relative path more generic for users?  I got "Unable to access jarfile" error without
#   the full path specified.
jar_file = '/home/travis/IdeaProjects/synthetic-database-project/synthea-with-dependencies.jar'


# Collect Females
log.printSectionSubHeader('Creating Female Records')
sub_start = time.time()
synthea = Synthea(jar_file,'synthea_settings') # initialize the module
synthea.specify_popSize(1252)
synthea.specify_gender('F')
synthea.run_synthea()
log.printElapsedTime(sub_start, "Females created in: ")

# Collect Males
log.printSectionSubHeader('Creating Male Records')
sub_start = time.time()
synthea = Synthea(jar_file,'synthea_settings') # initialize the module
synthea.specify_popSize(1220)
synthea.specify_gender('M')
synthea.run_synthea()
log.printElapsedTime(sub_start, "Males created in: ")

# Format data to our desired layout
log.printSectionHeader('Formatting Data')
form_start = time.time()
Format_Output('010735',output_loc)
log.printElapsedTime(form_start, "Formatted output created in: ")


log.printSectionSubHeader('Total Elapsed Time')
log.printElapsedTime(start)
