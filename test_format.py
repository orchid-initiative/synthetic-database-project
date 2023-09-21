import unittest
from synth_data_module import FormatOutput

class FormatTest(unittest.TestCase):

    output_loc = 'output/'
    encounter_type = 'inpatient'
    fmt = FormatOutput('010735', output_loc, encounter_type)

    def test_add_procedure(self):
        pass

    def test_add_diagnosis(self):
        pass

    def test_modify_row(self):
        testdict = [{'a': 1, 'b': 2, 'c': 3},
                  {'a': 100, 'b': 200, 'c': 300},
                  {'a': 1000, 'b': 2000, 'c': 3000}]

    def test_get_procedure_list(self):
        self.assertEqual(len(self.fmt.get_procedure_list()), 48)

    def test_get_diagnosis_list(self):
        self.assertEqual(len(self.fmt.get_diagnosis_list()), 46)


if __name__ == '__main__':
    unittest.main()