from src.cpf_program_v7 import CPFAccount

if __name__ == "__main__":
    # Entry point for CPF simulation using correct logic
    print("Running CPF simulation using cpf_program_v7...")
    cpf_account = CPFAccount(config_file='new_config.json')
    cpf_account.run_simulation()
