
import json

mydict = {}

with open('xcpf_config.json', 'r') as f:
    mydict = json.load(f)
    
with open('cpf_config.json', 'w') as f:
    json.dump(mydict, f, indent=4)
 