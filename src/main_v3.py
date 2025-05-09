import streamlit as st
import subprocess
import pandas as pd
from cpf_config_loader_v5 import ConfigLoader
from cpf_manage_authentication import authenticate

# Set page configuration
st.set_page_config(page_title="CPF Simulation Setup", layout="wide")
st.markdown("<h1 style='color:blue;'>🧾 <b>CPF Simulation Configurator</b></h1>", unsafe_allow_html=True)

# Authenticate the user
if not authenticate(st):
    st.stop()

# Load the configuration
CONFIG_PATH = "cpf_config.json"
config_loader = ConfigLoader(CONFIG_PATH)

# Get keys and values from the configuration
keys, values = config_loader.get_keys_and_values()

st.markdown("<h2 style='color:purple;'>🔧 <b>Edit Parameters</b></h2>", unsafe_allow_html=True)

# Create input fields dynamically based on keys and values
updated_config = {}
for key, value in zip(keys, values):
    updated_value = st.text_input(f"<b>{key}</b>", str(value), key=key, unsafe_allow_html=True)
    updated_config[key] = updated_value

# Buttons for additional functionality
col1, col2, col3, col4, col5 = st.columns(5)

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
        config_loader.data = nested_config
        config_loader.save()
        st.success("Configuration saved successfully!")

with col2:
    if st.button("🚀 Submit"):
        # Run the simulation script
        try:
            result = subprocess.run(["python", "run_cpf_simulation_v7.py"], check=True, capture_output=True, text=True)
            st.success("Simulation completed!")
            st.code(result.stdout)
        except subprocess.CalledProcessError as e:
            st.error("Simulation failed:")
            st.code(e.stderr or str(e))

with col3:
    if st.button("🧹 Clear"):
        st.experimental_rerun()

with col4:
    if st.button("📤 Export as CSV"):
        # Export the updated configuration as a CSV file
        df = pd.DataFrame({"Key": keys, "Value": values})
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="cpf_config.csv",
            mime="text/csv",
        )

with col5:
    if st.button("📤 Export as XML"):
        # Export the updated configuration as an XML file
        import dicttoxml
        xml = dicttoxml.dicttoxml(config_loader.data)
        st.download_button(
            label="Download XML",
            data=xml,
            file_name="cpf_config.xml",
            mime="application/xml",
        )

# Exit button
if st.button("❌ Exit"):
    st.stop()