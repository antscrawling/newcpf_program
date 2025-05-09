import json
import pandas as pd

def cleanup_the_logs():
    # Load the JSON file
    with open("cpf_logs.json", "r") as file:
        logs = json.load(file)
    
    # Convert to DataFrame
    df = pd.DataFrame(logs)
    
    # Print the first few rows
    print(df.head())
    
    # Optional: Save to CSV
    df.to_csv("cpf_logs_parsed.csv", index=False)