from synth_data_module import Synthea
from log_helpers import log_helpers as log
import time
import datetime as dt

start = time.time()
log.setSysOut(f'{__file__}_{dt.date.today()}.log')

log.printSectionHeader('Running Synthea')
# initialize the module
jar_file = '/home/lsnortheim/projects/rileeki/synthea/synthea-with-dependencies.jar'
synthea = Synthea(jar_file,'synthea_settings')
synthea.specify_popSize(2)
synthea.run_synthea()

log.printElapsedTime(start)