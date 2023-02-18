##############################################
# read_sample.py   Reads sample synthetic data
#
# RTullis, 4/7/2023
##############################################
#from log_helpers import log_helpers as log
import time
import datetime as dt
import pandas as pd

start = time.time()
#log.setSysOut(f'{__file__}_{dt.date.today()}.log')
output_loc = 'output'


#log.printSectionHeader('Reading in sample synthetic data')
infile = "/home/rtullis/starling/synthetic-database-project/data/sample_data.csv"
df = pd.read_csv(infile, sep = ",")
pd.set_option("display.width",115)
pd.set_option("display.precision",10)
pd.set_option("display.max_columns",11)
print(df.describe(include='all',percentiles=[]).transpose())
print(df['Patient Address - Zip Code'].value_counts())
print(df['Patient Address - City'].value_counts())
print(df.loc[df['Patient Address - Zip Code']=='XXXXX', 'Patient Address - City'])

"""
Type of Care,Facility Identification Number,Date of Birth,Sex,Ethnicity,Race,Not in Use,Admission Date,Point of Origin,Route of Admission,Type of Admission,Discharge Date,Principal Diagnosis,Present on Admission for Principal Diagnosis,Other Diagnosis and Present on Admission,Principal Procedure Code,Principal Procedure Date,Other Procedure Codes and Other Procedure Dates,External Casues of Morbidity and Present on Admission,Patient SSN,Disposition of Patient,Total Charges,Abstract Record Number (Optional),Prehospital Care & Resuscitation - DNR Order,Payer Category,Type of Covereage,Plan Code Number,Preferred Spoken Language,Patient Address - Address Number and Street Name,Patient Address - City,Patient Address - State,Patient Address - Zip Code,Patient Address - Country Code,Patient Address - Homeless Indicator
"""
#log.printSectionSubHeader('Total Elapsed Time')
#log.printElapsedTime(start)

