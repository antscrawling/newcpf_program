import streamlit as st
import subprocess
from cpf_config_loader_v5 import ConfigLoader

st.set_page_config(page_title="CPF Simulation Setup", layout="wide")
st.title("🧾 CPF Simulation Configurator")

USER = st.secrets["credentials"]["username"]
PASS = st.secrets["credentials"]["password"]

if "authenticated" not in st.session_state:
    with st.sidebar:
        st.title("🔐 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login = st.button("Login")

    if login:
        if username == USER and password == PASS:
            st.session_state["authenticated"] = True
        else:
            st.error("Invalid login")

if not st.session_state.get("authenticated"):
    st.stop()

# Load the configuration
CONFIG_PATH = "cpf_config.json"
config_loader = ConfigLoader(CONFIG_PATH)

# Get keys and values from the configuration
keys, values = config_loader.get_keys_and_values()

st.subheader("🔧 Edit Parameters")

# Create input fields dynamically based on keys and values
updated_config = {}
for key, value in zip(keys, values):
    updated_value = st.text_input(key, str(value))
    updated_config[key] = updated_value

if st.button("💾 Save and Run Simulation"):
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

    # Run the simulation script
    try:
        result = subprocess.run(["python", "run_cpf_simulation_v7.py"], check=True, capture_output=True, text=True)
        st.success("Simulation completed!")
        st.code(result.stdout)
    except subprocess.CalledProcessError as e:
        st.error("Simulation failed:")
        st.code(e.stderr or str(e))