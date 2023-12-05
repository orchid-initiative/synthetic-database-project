from synth_data_module import Synthea, SyntheaOutput, create_formatter, clear_old_files
from log_helpers import log_helpers as log
import time
import os
import datetime as dt
import argparse


def parse_arguments():
    # Initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-T', '--EncounterType', help='Specify Encounter Type',
                        choices=['inpatient', 'outpatient', 'ambulatory', 'wellness', 'virtual', 'urgentcare',
                                 'emergency'], default='inpatient')
    parser.add_argument('-C', '--City', help='Specify the City, State for the synthea location', default=None)
    parser.add_argument('-G', '--Gender', help='Specify the gender of patients',
                        choices=['M', 'F'], default=False)
    parser.add_argument('-N', '--PersonCount', help='Specify the number of people to simulate', type=int,
                        choices=range(1, 5000), default=100)

    parser.add_argument('-O', '--FormatType', help='Specify the type of output',
                        choices=['HCAI_CSV', 'HCAI_FW', 'NEW_NEW', "all"], default="all")
    parser.add_argument('-V', '--Verbose', help='Include additional fields, not part of offical outputs', default=False)

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
    generate_synthea_patients(args)
    format_data(args)
    log.printSectionSubHeader('Total Elapsed Time')
    log.printElapsedTime(start)


def generate_synthea_patients(args):
    if args.FormatOnly:
        pass

    # Identify the path for the synthea java jar - it should be in the same folder as this script.  Initialize Synthea
    file_path = os.path.realpath(__file__)
    directory = os.path.dirname(file_path)
    jar_file = os.path.join(directory, 'synthea-with-dependencies.jar')
    synthea = Synthea(jar_file, 'synthea_settings')  # initialize the module

    # Call this first to provide some command line feedback to the user
    city, state = synthea.parse_city(args.City)

    # Divert remaining logs to a saved log file
    log.setSysOut(f'logs/{__file__}_{dt.date.today()}.log')

    # Subsequent Synthea runs append data to the CSVs (this is a setting) so we clear out the past output at the
    # start of each full run_synthea run - "formatted_data_DATETIME".csv is the only output persisting
    log.printSectionHeader('Clearing Old Local Data')
    clear_old_files()

    # Run Synthea with global parameters and run-specific parameters
    log.printSectionHeader('Running Synthea')

    # Collect Patients
    log.printSectionSubHeader('Creating Patient Records')
    synth_start = time.time()
    synthea.specify_popsize(size=args.PersonCount)
    synthea.specify_gender(gender=args.Gender)
    synthea.specify_city(state, city)
    synthea.run_synthea()
    log.printElapsedTime(synth_start, "Patients created in: ")


def format_data(args):
    if args.SyntheaGenOnly:
        pass
    # Format data to our desired layout
    log.printSectionHeader('Formatting Data')
    form_start = time.time()
    if not args.SyntheaGenOnly:
        create_formatter(args, synthea_output=SyntheaOutput())
    log.printElapsedTime(form_start, "Formatted output created in: ")


if __name__ == "__main__":
    main()
