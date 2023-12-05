from synth_data_module import HCAIFormat, Formatter
from io import StringIO


# Factory method
def create_formatter(args, synthea_output) -> Formatter: #, settings: argparse.Namespace
    if args.FormatType == "HCAI_FW":
        return HCAIFormat(args, synthea_output=synthea_output, csv=False)
    elif args.FormatType == "HCAI_CSV":
        return HCAIFormat(args, synthesa_output=synthea_output, csv=True)
#    elif args.FormatType == "NEW_NEW":
#        return NEW_Format(settings, "...")
        #....

# formatter = create_formatter("california_hospital_fixed_width", args)

# with open(formatter.suggested_filename(), "w") as f:
#     f.write(formatter.format_data(data))


