from synth_data_module import Synthea
from log_helpers import log_helpers as log
import time
import datetime as dt

start = time.time()
log.setSysOut(f'{__file__}_{dt.date.today()}.log')

log.printSectionHeader('Running Synthea')
jar_file = '/home/lsnortheim/projects/rileeki/synthea/synthea-with-dependencies.jar'
# Collect Females
log.printSectionSubHeader('Creating Female Records')
sub_start = time.time()
synthea = Synthea(jar_file,'synthea_settings') # initialize the module
synthea.specify_popSize(12) #52)
synthea.specify_gender('F')
synthea.run_synthea()
log.printElapsedTime(sub_start, "Females created in: ")

# Collect Males
log.printSectionSubHeader('Creating Male Records')
sub_start = time.time()
synthea = Synthea(jar_file,'synthea_settings') # initialize the module
synthea.specify_popSize(12)#20)
synthea.specify_gender('M')
synthea.run_synthea()
log.printElapsedTime(sub_start, "Males created in: ")

log.printSectionSubHeader('Total Elapsed Time')
log.printElapsedTime(start)