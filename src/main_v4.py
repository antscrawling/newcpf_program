import streamlit as st
import subprocess
import json
from cpf_config_loader_v8 import ConfigLoader
import os
from datetime import datetime, date

PATH = os.path.dirname(os.path.abspath(__file__))  # Dynamically determine the src directory
SRC_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to the src directory
CONFIG_FILENAME = os.path.join(SRC_DIR, 'cpf_config.json')  # Full path to the config file
FLAT_FILENAME = os.path.join(SRC_DIR, 'cpf_config_flat.json')  # Full path to the flat config file
#DATABASE_NAME = os.path.join(SRC_DIR, 'cpf_simulation.db')  # Full path to the database file


st.set_page_config(page_title="CPF Simulation Setup", layout="wide")
st.title("🧾 CPF Simulation Configurator")

# Load the configuration
flat_config = ConfigLoader(FLAT_FILENAME)
#
# Display the flat dictionary in the Streamlit app
st.subheader("🔧 Edit Parameters")
updated_config = {}

for key, value in flat_config._config_data.items():
    if isinstance(value, (int, float)):
        updated_value = st.number_input(key, value=value)
    elif isinstance(value, str):
        updated_value = st.text_input(key, value=value)
    else:
        updated_value = st.text_area(key, value=json.dumps(value))
    updated_config[key] = updated_value



# Save the updated configuration
col1, col2, col3, col4, col5, col6  = st.columns(6)

with col1:
    if st.button("💾 Save"):
        # Convert updated_config back to a nested dictionary
        def unflatten_dict(d, sep="."):
            result = {}
            for k, v in d.items():
                keys = k.split(sep)
                current = result
                for key in keys[:-1]:
                    current = current.setdefault(key, {})
                current[keys[-1]] = v
            return result

        nested_config = unflatten_dict(updated_config)

        # Save the updated configuration back to the file
        for k, v in nested_config.items():
            if isinstance(v,(datetime, date)):
                flat_config._config_data[k] = v.strftime("%Y-%m-%d")
            else:  
                flat_config._config_data[k]  = v
        st.success("Configuration saved successfully!")
        


        # Save the updated configuration to a file
        with open(CONFIG_FILENAME, "w") as f:
            json.dump(nested_config, f, indent=4)
        st.success("Configuration saved successfully!")
    
with col2:
    if st.button("Run Simulation"):
        result = subprocess.run(["python", os.path.join(PATH, "cpf_run_simulation_v8.py")], check=True, capture_output=True, text=True)
    with open(os.path.join(PATH, "cpf_config_flat_updated.json"), "w") as f:
        json.dump(updated_config, f, indent=4)
    st.success("Configuration saved successfully!")
    
    
with col3:
   if st.button("🚀 Run CSV report"):
       # Run the simulation script
       try:
           result = subprocess.run(["python", os.path.join(PATH, "ccpf_build_reports_v1.py")], check=True, capture_output=True, text=True)
           st.success("Simulation completed!")
           st.code(result.stdout)
       except subprocess.CalledProcessError as e:
           st.error("Simulation failed:")
           st.code(e.stderr or str(e))
           
with col4:
    if st.button("🧹 Clear"):
        st.experimental_rerun()
        
with col5:
    import dicttoxml
    xml = dicttoxml.dicttoxml(flat_config._config_data)
    st.download_button(
        label="Download XML",
        data=xml,
        file_name="cpf_config.xml",
        mime="application/xml",
        )
    
with col6:
    if st.button(" EXIT "):
        # Export the updated configuration as a CSV file
        st.stop()






