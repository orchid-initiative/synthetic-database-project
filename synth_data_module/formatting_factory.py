from synth_data_module import HCAIInpatientFormat, HCAIPDDFormat, Formatter
from io import StringIO


# Factory method
def create_formatter(**kwargs) -> Formatter: #, settings: argparse.Namespace
    if "HCAI_Inpatient" in kwargs['FormatType']:
        return HCAIInpatientFormat(**kwargs)
    elif "HCAI_PDD" in kwargs['FormatType']:
        return HCAIPDDFormat(**kwargs)
