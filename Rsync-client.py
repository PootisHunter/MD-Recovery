import subprocess
import os

def backup_with_rsync(source, destination, ssh_user, ssh_host, ssh_port=22):
    """
    Perform a backup using rsync over SSH.

    Args:
        source (str): Path to the source directory (local).
        destination (str): Path to the destination directory (on the remote server).
        ssh_user (str): SSH username for the remote server.
        ssh_host (str): Hostname or IP address of the remote server.
        ssh_port (int): SSH port (default is 22).
    """
    try:
        # Construct the rsync command
        rsync_command = [
            "rsync",
            "-avz",
            "--progress",  
            "-e", f"ssh -p {ssh_port}",  # Use SSH with a custom port
            source,
            f"{ssh_user}@{ssh_host}:{destination}"  # Remote destination
        ]

        print("Executing command:", " ".join(rsync_command))
        
        # Run the rsync command
        result = subprocess.run(rsync_command, check=True, text=True, capture_output=True)

        # Print success message
        print("Backup completed successfully.")
        print("Output:", result.stdout)

    except subprocess.CalledProcessError as e:
        # Handle rsync errors
        print("Error occurred during backup.")
        print("Command output:", e.stderr)

# Example usage
if __name__ == "__main__":
    # Define parameters
    SOURCE_DIR = "/path/to/local/source/"
    DESTINATION_DIR = "/path/to/remote/backup/"
    SSH_USER = "username"
    SSH_HOST = "backup-server.com"
    SSH_PORT = 22  # Default SSH port

    # Perform the backup
    backup_with_rsync(SOURCE_DIR, DESTINATION_DIR, SSH_USER, SSH_HOST, SSH_PORT)