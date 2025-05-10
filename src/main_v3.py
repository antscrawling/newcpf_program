import streamlit as st
import json
from cpf_config_loader_v5 import ConfigLoader

st.set_page_config(page_title="CPF Simulation Setup", layout="wide")
st.title("🧾 CPF Simulation Configurator")

# Load the configuration
config_loader = ConfigLoader("cpf_config_flat.json")
flat_config = config_loader.config

# Display the flat dictionary in the Streamlit app
st.subheader("🔧 Edit Parameters")
updated_config = {}

for key, value in flat_config.items():
    if isinstance(value, (int, float)):
        updated_value = st.number_input(key, value=value)
    elif isinstance(value, str):
        updated_value = st.text_input(key, value=value)
    else:
        updated_value = st.text_area(key, value=json.dumps(value))
    updated_config[key] = updated_value

# Save the updated configuration
if st.button("Save Configuration"):
    with open("cpf_config_flat_updated.json", "w") as f:
        json.dump(updated_config, f, indent=4)
    st.success("Configuration saved successfully!")