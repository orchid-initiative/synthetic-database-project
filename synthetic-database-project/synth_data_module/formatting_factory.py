from synth_data_module import HCAIInpatientFormat, HCAIPDDFormat, Formatter


# Factory method
def create_formatter(timers, **kwargs) -> Formatter: #, settings: argparse.Namespace
    print("FORMATTER", kwargs['FormatType'])
    if "HCAI_Inpatient" in kwargs['FormatType']:
        return HCAIInpatientFormat(timers, **kwargs)
    elif "HCAI_PDD" in kwargs['FormatType']:
        return HCAIPDDFormat(timers, **kwargs)
