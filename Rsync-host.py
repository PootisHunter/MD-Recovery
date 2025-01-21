import os
import paramiko
import socket
from paramiko import RSAKey
from paramiko import SFTPServer, SFTPHandle

def start_ssh_server(host="0.0.0.0", port=22, host_key_path="host_key"):
    """
    Start the SSH server to handle client connections.

    Args:
        host (str): Host IP to bind the server to. Default is "0.0.0.0" (all interfaces).
        port (int): Port to bind the SSH server. Default is 22.
        host_key_path (str): Path to the host's private key for SSH authentication.
    """
    # Load the host private key
    if not os.path.exists(host_key_path):
        print(f"Host key file not found: {host_key_path}")
        return

    host_key = RSAKey(filename=host_key_path)

    # Create an SSH server
    ssh_server = paramiko.ServerInterface()

    class CustomServer(paramiko.ServerInterface):
        def __init__(self):
            self.event = paramiko.Event()

        def check_auth_password(self, username, password):
            """
            Authenticate user credentials.
            """
            if username == "admin" and password == "password123":
                return paramiko.AUTH_SUCCESSFUL
            return paramiko.AUTH_FAILED

        def get_allowed_auths(self, username):
            """
            Specify allowed authentication methods.
            """
            return "password"

        def check_channel_request(self, kind, chanid):
            """
            Allow "session" type channels.
            """
            if kind == "session":
                return paramiko.OPEN_SUCCEEDED
            return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

        def check_channel_exec_request(self, channel, command):
            """
            Handle execution of commands.
            """
            print(f"Executing command: {command}")
            if command == "get_logs":
                channel.send("Log data: [Sample log message 1, Sample log message 2]")
                channel.close()
                return True
            else:
                channel.send(f"Unknown command: {command}")
                channel.close()
                return False

    # Create a socket to listen for connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(100)

    print(f"SSH server started on {host}:{port}")

    try:
        while True:
            # Accept a new connection
            client_socket, client_addr = server_socket.accept()
            print(f"Connection from {client_addr}")

            # Establish the SSH transport
            ssh_transport = paramiko.Transport(client_socket)
            ssh_transport.add_server_key(host_key)
            ssh_transport.set_subsystem_handler("sftp", CustomSFTPServer)

            # Start the SSH server
            server = CustomServer()
            ssh_transport.start_server(server=server)

            # Open a session channel
            channel = ssh_transport.accept(timeout=20)
            if channel is None:
                print("Channel timeout!")
                continue

            # Read messages from the client (if needed)
            while True:
                try:
                    data = channel.recv(1024)
                    if not data:
                        break
                    print(f"Received from client: {data.decode('utf-8')}")
                    channel.send(f"Echo: {data.decode('utf-8')}")
                except Exception as e:
                    print(f"Error: {e}")
                    break

            channel.close()

    except KeyboardInterrupt:
        print("Shutting down the server.")
    finally:
        server_socket.close()

# Example usage
if __name__ == "__main__":
    start_ssh_server(host="0.0.0.0", port=2222, host_key_path="host_key")