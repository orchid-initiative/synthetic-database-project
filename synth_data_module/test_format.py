import unittest
from format import FormatOutput

class FormatTest(unittest.TestCase):
    def setUp(self):
        output_loc = 'output/'
        encounter_type = 'inpatient'
        self.format = FormatOutput('010735', output_loc, encounter_type)

    def test_add_procedure(self):
        pass

    def test_add_diagnosis(self):
        pass

    def test_get_procedure_list(self):
        self.assertEqual(len(self.format.get_procedure_list()), 24)

    def test_get_diagnosis_list(self):
        pass


if __name__ == '__main__':
    unittest.main()