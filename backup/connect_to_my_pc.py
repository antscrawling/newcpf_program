
import paramiko

portno = 22
myipaddress = "192.168.50.31"
server_name = "JOSEIBAYMAC"
username = "joseibay"  # Replace with your username
password = "6640"  # Replace with your password

try:
    # Create an SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect to the server
    ssh_client.connect(hostname=myipaddress, port=portno, username=username, password=password)
    print(f"Connected to {server_name} at {myipaddress}:{portno}")

    # Execute a command (example: list files in the home directory)
    stdin, stdout, stderr = ssh_client.exec_command("ls -la")
    print(stdout.read().decode())

    # Close the connection
    ssh_client.close()
    print("Connection closed.")

except Exception as e:
    print(f"Failed to connect: {e}")



