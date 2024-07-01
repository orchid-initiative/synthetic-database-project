from synth_data_module import *
import time
import os
import datetime as dt
import argparse


# Initialize timers
timers = CreateTimers()

# Predefined Studies
predefined_studies = {
    'LARC': {'Gender': 'F', 'Age': '15-50', 'FormatType': 'HCAI_PDD_CSV', 'City': 'California',
             'EncounterType': 'emergency', 'ModuleOverrides': True, 'KeepModule': True},

#    'LARC': {'Gender': 'F', 'Age': '15-50', 'FormatType': 'HCAI_PDD_CSV', 'City': 'Los Angeles,California',
#             'EncounterType': 'emergency', 'KeepModule': True},

#    'LARC': {'Gender': 'F', 'Age': '15-50', 'FormatType': 'HCAI_PDD_CSV', 'City': 'Los Angeles,California',
#             'EncounterType': 'emergency', 'ModuleOverrides': True},
    # Add more predefined studies as needed
}
studyfolder = ''


def parse_arguments():
    global studyfolder
    # Initialize parser
    parser = argparse.ArgumentParser()

    parser.add_argument('-A', '--Age', help='Restrict the Age Range of Inspection', default=False)
    parser.add_argument('-C', '--City', help='Specify the City, State for the synthea location', default=None)
    parser.add_argument('-G', '--Gender', help='Specify the gender of patients', choices=['M', 'F'], default=False)
    #parser.add_argument('-ID', '--FacilityID', help='Specify the Facility ID to tag', default='010735')
    parser.add_argument('-M', '--ModuleOverrides', help='Allows local modules to be used instead of JAR modules',
                        action='store_true', default=False)
    parser.add_argument('-N', '--PersonCount', help='Number of patients', type=int, metavar="[1-15000]", default=100)
    parser.add_argument('-O', '--FormatType', help='Specify the type of output',
                        choices=['HCAI_Inpatient_CSV', 'HCAI_Inpatient_FW', 'HCAI_PDD_CSV', 'HCAI_PDD_SAS', "all"],
                        default="HCAI_PDD_CSV")
    parser.add_argument('-K', '--KeepModule', help='Specify a keep module JSON', action='store_true', default=False)
    parser.add_argument('-Study', choices=predefined_studies.keys(), help='Specify a predefined study name', default=None)
    parser.add_argument('-T', '--EncounterType', help='Specify Encounter Type',
                        choices=['inpatient', 'outpatient', 'ambulatory', 'wellness', 'virtual', 'urgentcare',
                                 'emergency'], default='inpatient')
    parser.add_argument('-V', '--Verbose', help='Include additional fields, not part of offical outputs', default=False)

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

    # Apply overrides based on the chosen study
    if args.Study in predefined_studies:
        studyfolder = f'StudyOverrides/{args.Study}/'
        for arg_name, arg_value in predefined_studies[args.Study].items():
            setattr(args, arg_name, arg_value)

    if args.Yearly and args.YearRange is None:
        parser.error("--Yearly requires --YearRange")

    return args


def main():
    args_dict = vars(parse_arguments())

    print(args_dict)
    # Custom validation for PersonCount
    if not (1 <= args_dict['PersonCount'] <= 50000):
        print("Error: PersonCount must be between 1 and 50000.")
        return

    # Call this first to provide some command line feedback to the user about location choices
    city, state = parse_city(args_dict['City'])

    # Divert remaining logs to a saved log file
    setSysOut(f'logs/{__file__}_{dt.date.today()}.log')

    # Generate patient data
    generate_synthea_patients(city, state, **args_dict)

    # Format patient data
    report_data(**args_dict)

    # Timekeeping stats
    printSectionSubHeader('Timekeeping Stats')
    timers.record_time('Total Elapsed Time', timers.start, suppress=True)
    timers.print_timers()


def generate_synthea_patients(city, state, **kwargs):
    if kwargs['FormatOnly']:
        return

    # Identify the path for the synthea java jar - it should be in the same folder as this script.  Initialize Synthea
    file_path = os.path.realpath(__file__)
    directory = os.path.dirname(file_path)
    jar_file = os.path.join(directory, 'synthea-with-dependencies.jar')
    synthea = Synthea(jar_file, f'{studyfolder}synthea_settings')  # initialize the module

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
    synthea.specify_keep_module(keep_module=kwargs['KeepModule'], studyfolder=studyfolder)
    synthea.specify_module_overrides(module_overrides=kwargs['ModuleOverrides'], studyfolder=studyfolder)
    if kwargs['Age']:
        synthea.specify_age(minage=kwargs['Age'].split("-")[0], maxage=kwargs['Age'].split("-")[1])
    synthea.specify_city(state, city)
    synthea.run_synthea()
    timers.record_time('Patient Records', synth_start)


def report_data(**kwargs):
    if kwargs['SyntheaGenOnly']:
        return
    # Format data to our desired layout
    printSectionHeader('Formatting Data')
    form_start = time.time()
    formatter = create_formatter(timers, **kwargs)
    formatter.gather_data()
    data = formatter.format_data()
    formatter.write_data(data)
    timers.record_time('Formatted Output', form_start)


if __name__ == "__main__":
    main()
