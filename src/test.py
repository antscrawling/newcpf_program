
import json
from dotmap import DotMap
from cpf_config_loader_v8 import ConfigLoader

file = 'test_config.json'
mydict = {}
myconfig = ConfigLoader(file)

#create a copy
mydict = myconfig._config_data.copy()
#print(mydict)

salary_cap = mydict.get('salary_cap')
employee = mydict.get('below_55').get('employee')
employer = mydict.get('below_55').get('employer')
#formula = mydict.get('below_55').get('total_contribution').get('formula')
formula = mydict.get('below_55').get('total_contribution').get('formula')

print(f'before change = {formula}')


for item in formula.split():
    if item == 'employee':
        formula = formula.replace(item, str(employee))
    elif item == 'employer':
        formula = formula.replace(item, str(employer))
    elif item == 'salary_cap':
        formula = formula.replace(item, str(salary_cap))

formula = eval(formula)

print(f'after change = {formula}')




#print(myconfig._config_data)



