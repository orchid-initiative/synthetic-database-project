from synth_data_module import Synthea, FormatOutput, clear_old_files
from log_helpers import log_helpers as log
import time
import os
import datetime as dt
import argparse


def parse_arguments():
    # Initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-T', '--Type', help='Specify Encounter Type',
                        choices=['inpatient', 'outpatient', 'ambulatory', 'wellness', 'virtual', 'urgentcare',
                                 'emergency'], default='inpatient')
    parser.add_argument('-C', '--SpecifyCity', help='Specify the City, State for the synthea location', default=False)
    # Add an argument to just run formatting code (i.e. bypass running synthea again and do not delete output/ files)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-F', '--FormatOnly', help='Only Run Formatting code', action='store_true', default=False)
    group.add_argument('-D', '--SyntheaGenOnly', help='Only Run Synthea Data Generation, not Formatting',
                       action='store_true', default=False)
    args = parser.parse_args()
    return args


def main():
    start = time.time()
    args = parse_arguments()
    if args.SpecifyCity:
        if len(args.SpecifyCity.split(",")) == 2:
            city = str(args.SpecifyCity.split(",")[0])
            state = str(args.SpecifyCity.split(",")[1])
            print("Overriding default location Massachusetts to city, state: %s, %s " % (city, state))
        else:
            city = None
            state = str(args.SpecifyCity.split(",")[0])
            print("Overriding default location Massachusetts to state %s " % state)

    log.setSysOut(f'logs/{__file__}_{dt.date.today()}.log')
    output_loc = 'output/'
    encounter_type = args.Type

    if not args.FormatOnly:
        # Subsequent Synthea runs append data to the CSVs (this is a setting) so we clear out the past output at the
        # start of each full run_synthea run - "formatted_data_DATETIME".csv is the only output persisting
        log.printSectionHeader('Clearing Old Local Data')
        clear_old_files()

        # Identify the path for the synthea java jar
        file_path = os.path.realpath(__file__)
        directory = os.path.dirname(file_path)
        jar_file = os.path.join(directory, 'synthea-with-dependencies.jar')

        # Run Synthea with global parameters and run-specific parameters
        log.printSectionHeader('Running Synthea')

        # TODO probably take out the M/F separation in favor of more general statistic seeking results
        # Collect Females
        log.printSectionSubHeader('Creating Female Records')
        sub_start = time.time()
        synthea = Synthea(jar_file, 'synthea_settings')  # initialize the module
        synthea.specify_popsize(size=500)
        synthea.specify_gender(gender='F')
        if args.SpecifyCity:
            synthea.specify_city(state, city)
        synthea.run_synthea()
        log.printElapsedTime(sub_start, "Females created in: ")

        # Collect Males
        log.printSectionSubHeader('Creating Male Records')
        sub_start = time.time()
        synthea = Synthea(jar_file, 'synthea_settings') # initialize the module
        synthea.specify_popsize(size=500)
        synthea.specify_gender(gender='M')
        if args.SpecifyCity:
            synthea.specify_city(state, city)
        synthea.run_synthea()
        log.printElapsedTime(sub_start, "Males created in: ")

    # Format data to our desired layout
    log.printSectionHeader('Formatting Data')
    form_start = time.time()
    if not args.SyntheaGenOnly:
        FormatOutput('010735', output_loc, encounter_type)
        log.printElapsedTime(form_start, "Formatted output created in: ")
    log.printSectionSubHeader('Total Elapsed Time')
    log.printElapsedTime(start)


if __name__ == "__main__":
    main()
