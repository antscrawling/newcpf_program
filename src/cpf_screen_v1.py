import streamlit as st
import json
import subprocess
import os

CONFIG_PATH = "cpf_config.json"

st.set_page_config(page_title="CPF Simulation Setup", layout="wide")
st.title("🧾 CPF Simulation Configurator")

# Load config
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
else:
    st.error("Config file not found.")
    st.stop()

# Flatten nested config into a single-level dict
def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, ','.join(map(str, v))))
        else:
            items.append((new_key, v))
    return dict(items)

# Unflatten back to nested dict
def unflatten_dict(d, sep='.'):
    result = {}
    for k, v in d.items():
        keys = k.split(sep)
        current = result
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        try:
            current[keys[-1]] = json.loads(v)
        except:
            current[keys[-1]] = v
    return result

flat_config = flatten_dict(config)

st.subheader("🔧 Edit Parameters")
updated_config = {}
for key, value in flat_config.items():
    updated_value = st.text_input(key, str(value))
    updated_config[key] = updated_value

if st.button("💾 Save and Run Simulation"):
    nested_config = unflatten_dict(updated_config)
    with open(CONFIG_PATH, "w") as f:
        json.dump(nested_config, f, indent=4)

    try:
        result = subprocess.run(["python", "run_cpf_simulation_v7.py"], check=True, capture_output=True, text=True)
        st.success("Simulation completed!")
        st.code(result.stdout)
    except subprocess.CalledProcessError as e:
        st.error("Simulation failed:")
        st.code(e.stderr or str(e))