import subprocess
import time
import datetime as dt

class Synthea():
    def __init__(self, jar_file, config_file):
        self.java_command =f'java -jar {jar_file} -c {config_file}'

    def specify_popSize(self, size):
        self.java_command = self.java_command + f' -p {size}'

    def specify_gender(self, gender):
        self.java_command = self.java_command + f' -g {gender}'

    def specify_age(self, min, max):
        self.java_command = self.java_command + f' -a {min}-{max}'
        
    def run_synthea(self):
        java_command_list = self.java_command.split(' ')
        child = subprocess.Popen(java_command_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output_str = child.stdout.read().decode() #decode converts from bytes to string object
        timestamp = time.time()
        date_time = dt.datetime.fromtimestamp(timestamp)
        with open(f'full_synthea_stdout_{date_time.strftime("%d-%m-%Y_%H%M%S")}.txt', 'w') as output:
            output.write(output_str)
        run_options = output_str[output_str.index('Running with options'):output_str.index(' -- ')-2]
        total_records = output_str[output_str.index('Records: '):output_str.index('RNG')]
        print(run_options, total_records, sep = '\n\n')
        
        

        