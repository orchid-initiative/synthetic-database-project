import unittest
from synth_data_module import FormatOutput

class FormatTest(unittest.TestCase):

    output_loc = 'output/'
    encounter_type = 'inpatient'
    fmt = FormatOutput('010735', output_loc, encounter_type)

    def test_add_procedure(self):
        pass
        #For this test try testing without modifying the original function in format

    def test_add_diagnosis(self):
        pass
        #For this test, first try separating the function into separate functions based on functionality. Ex: pulling data from csv vs. merging data
    def test_modify_row(self):
        testdict = [{'a': 1, 'b': 2, 'c': 3},
                  {'a': 100, 'b': 200, 'c': 300},
                  {'a': 1000, 'b': 2000, 'c': 3000}]

    def test_get_procedure_list(self):
        procedure_list = self.fmt.get_procedure_list()
        self.assertEqual(len(procedure_list), 48)

        for i in range(48):
            if i == 0 or i == 1:
                self.assertTrue(procedure_list[i]['name'].startswith('Principal'))
            elif i % 2 == 0:
                self.assertTrue(procedure_list[i]['name'].startswith('Procedure Code'))
            else:
                self.assertTrue(procedure_list[i]['name'].startswith('Procedure Date'))

    def test_get_diagnosis_list(self):
        diagnosis_list = self.fmt.get_diagnosis_list()
        self.assertEqual(len(diagnosis_list), 46)

        for i in range(46):
            if i % 2 == 0:
                self.assertTrue(diagnosis_list[i]['name'].startswith('Diagnosis'))
            else:
                self.assertTrue(diagnosis_list[i]['name'].startswith('Present on Admission'))


if __name__ == '__main__':
    unittest.main()