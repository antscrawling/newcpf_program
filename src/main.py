import sys
from cpf_gui_input_form import ConfigInputForm
from PyQt5.QtWidgets import QApplication, QFileDialog

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
