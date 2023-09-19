import unittest
from synth_data_module import FormatOutput

class FormatTest(unittest.TestCase):
    output_loc = 'output/'
    encounter_type = 'inpatient'
    format = FormatOutput('010735', output_loc, encounter_type)

    def test_add_procedure(self):
        pass

    def test_add_diagnosis(self):
        pass

    def test_modify_row(self):
        pass

    def test_get_procedure_list(self):
        self.assertEqual(len(format.get_procedure_list()), 48)

    def test_get_diagnosis_list(self):
        self.assertEqual(len(format.get_diagnosis_list()), 46)


if __name__ == '__main__':
    unittest.main()