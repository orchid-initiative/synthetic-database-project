from synth_data_module import *
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
    parser.add_argument('-N', '--PersonCount', help='Number of patients', type=int, metavar="[1-5000]",
                        choices=range(1, 5000), default=100)
    parser.add_argument('-O', '--FormatType', help='Specify the type of output',
                        choices=['HCAI_Inpatient_CSV', 'HCAI_Inpatient_FW', 'HCAI_PDD_CSV', 'HCAI_PDD_SAS', "all"],
                        default="all")
    parser.add_argument('-ID', '--FacilityID', help='Specify the Facility ID to tag', default='010735')
    parser.add_argument('-V', '--Verbose', help='Include additional fields, not part of offical outputs', default=False)
    parser.add_argument('-A', '--Age', help='Separate the output by year', default=False)

    # Add arguments that allow reports to be generated on a yearly basis.  To avoid excess files, add date restriction
    group1 = parser.add_argument_group()
    parser.add_argument('-Y', '--Yearly', help='Separate the output by year', action='store_true', default=False)
    parser.add_argument('-R', '--YearRange', help='Restrict output to certain years', default=False)

    # Add an argument to just run formatting code (i.e. bypass running synthea again and do not delete output/ files)
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('-F', '--FormatOnly', help='Only Run Formatting code', action='store_true', default=False)
    group2.add_argument('-D', '--SyntheaGenOnly', help='Only Run Synthea Data Generation, not Formatting',
                        action='store_true', default=False)
    args = parser.parse_args()
    if args.Yearly and args.YearRange is None:
        parser.error("--Yearly requires --YearRange")

    return args


def main():
    start = time.time()
    args_dict = vars(parse_arguments())

    # Call this first to provide some command line feedback to the user about location choices
    city, state = parse_city(args_dict['City'])

    # Divert remaining logs to a saved log file
    setSysOut(f'logs/{__file__}_{dt.date.today()}.log')

    # Generate patient data
    generate_synthea_patients(city, state, **args_dict)

    # Format patient data
    report_data(**args_dict)

    # Timekeeping stats
    printSectionSubHeader('Total Elapsed Time')
    printElapsedTime(start)


def generate_synthea_patients(city, state, **kwargs):
    if kwargs['FormatOnly']:
        return

    # Identify the path for the synthea java jar - it should be in the same folder as this script.  Initialize Synthea
    file_path = os.path.realpath(__file__)
    directory = os.path.dirname(file_path)
    jar_file = os.path.join(directory, 'synthea-with-dependencies.jar')
    synthea = Synthea(jar_file, 'synthea_settings')  # initialize the module

    # Subsequent Synthea runs append data to the CSVs (this is a setting) so we clear out the past output at the
    # start of each full run_synthea run - "formatted_data_DATETIME".csv is the only output persisting
    printSectionHeader('Clearing Old Local Data')
    clear_old_files()

    # Run Synthea with global parameters and run-specific parameters
    printSectionHeader('Running Synthea')

    # Collect Patients
    printSectionSubHeader('Creating Patient Records')
    synth_start = time.time()
    synthea.specify_popsize(size=kwargs['PersonCount'])
    synthea.specify_gender(gender=kwargs['Gender'])
    synthea.specify_age(minage=kwargs['Age'].split("-")[0], maxage=kwargs['Age'].split("-")[1])
    synthea.specify_city(state, city)
    synthea.run_synthea()
    printElapsedTime(synth_start, "Patients created in: ")


def report_data(**kwargs):
    if kwargs['SyntheaGenOnly']:
        return
    # Format data to our desired layout
    printSectionHeader('Formatting Data')
    form_start = time.time()
    formatter = create_formatter(**kwargs)
    formatter.gather_data()
    data = formatter.format_data()
    formatter.write_data(data)
    printElapsedTime(form_start, "Formatted output created in: ")


if __name__ == "__main__":
    main()
