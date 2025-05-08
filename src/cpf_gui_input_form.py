import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QScrollArea, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt

class ConfigInputForm(QWidget):
    def __init__(self, config_path):
        super().__init__()
        self.setWindowTitle("CPF Config Setup")
        self.config_path = config_path
        self.form_data = {}
        self.inputs = {}

        with open(config_path, 'r') as f:
            self.raw_config = json.load(f)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        form_layout = QFormLayout()

        self.flatten_dict(self.raw_config)

        for key, value in self.form_data.items():
            label = QLabel(key)
            input_field = QLineEdit(str(value))
            form_layout.addRow(label, input_field)
            self.inputs[key] = input_field

        scroll_widget.setLayout(form_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        layout.addWidget(scroll_area)

        save_button = QPushButton("Run Simulation")
        save_button.clicked.connect(self.save_config_and_run)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def flatten_dict(self, d, parent_key=''):
        for k, v in d.items():
            full_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                self.flatten_dict(v, full_key)
            elif isinstance(v, list):
                self.form_data[full_key] = ",".join(map(str, v))
            else:
                self.form_data[full_key] = v

    def unflatten_dict(self):
        result = {}
        for key, input_field in self.inputs.items():
            keys = key.split('.')
            current = result
            for part in keys[:-1]:
                current = current.setdefault(part, {})
            value = input_field.text()
            try:
                current[keys[-1]] = json.loads(value)
            except json.JSONDecodeError:
                current[keys[-1]] = value
        return result

    def save_config_and_run(self):
        new_config = self.unflatten_dict()
        with open(self.config_path, 'w') as f:
            json.dump(new_config, f, indent=4)

        try:
            import subprocess
            subprocess.run([sys.executable, 'run_cpf_simulation_v7.py'], check=True)
            QMessageBox.information(self, "Success", "Simulation completed!")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Simulation failed: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    file_dialog = QFileDialog()
    config_file, _ = file_dialog.getOpenFileName(None, "Select Config JSON", "", "JSON Files (*.json)")
    if not config_file:
        sys.exit()

    form = ConfigInputForm(config_file)
    form.resize(800, 600)
    form.show()

    sys.exit(app.exec_())
