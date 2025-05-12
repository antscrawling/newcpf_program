# newcpf_program
New CPF program that calculates Singapore retirement funds.

## Installation Steps

### Windows
1. **Install Python**:
   - Download and install Python from the [official Python website](https://www.python.org/downloads/).
   - Ensure you check the box to add Python to your system's PATH during installation.

2. **Install Required Libraries**:
   - Open Command Prompt and navigate to the project directory:
     ```cmd
     cd path\to\newcpf_program
     ```
   - Install the required Python libraries:
     ```cmd
     pip install -r requirements.txt
     ```

3. **Run the Program**:
   - Run the Streamlit app:
     ```cmd
     streamlit run src/main_v4.py
     ```

---

### Mac
1. **Install Python**:
   - macOS comes with Python pre-installed. However, it is recommended to install the latest version using [Homebrew](https://brew.sh/):
     ```bash
     brew install python
     ```

2. **Install Required Libraries**:
   - Open Terminal and navigate to the project directory:
     ```bash
     cd /path/to/newcpf_program
     ```
   - Install the required Python libraries:
     ```bash
     pip3 install -r requirements.txt
     ```

3. **Run the Program**:
   - Run the Streamlit app:
     ```bash
     streamlit run src/main_v4.py
     ```

---

### Docker
1. **Install Docker**:
   - Download and install Docker from the [official Docker website](https://www.docker.com/).

2. **Build the Docker Image**:
   - Open a terminal or command prompt and navigate to the project directory:
     ```bash
     cd /path/to/newcpf_program
     ```
   - Build the Docker image:
     ```bash
     docker build -t newcpf_program .
     ```

3. **Run the Docker Container**:
   - Run the container and expose the Streamlit app on port 8501:
     ```bash
     docker run -p 8501:8501 newcpf_program
     ```

4. **Access the Application**:
   - Open a web browser and go to:
     ```
     http://localhost:8501
     ```

---

### Notes
- Ensure you have the `requirements.txt` file in the project directory with all the necessary dependencies listed.
- For Docker, ensure the `Dockerfile` is properly configured to install dependencies and run the Streamlit app.

Let me know if you need further assistance!
