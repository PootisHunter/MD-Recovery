from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Directory to store backups
BACKUP_STORAGE_DIR = "backups"
if not os.path.exists(BACKUP_STORAGE_DIR):
    os.makedirs(BACKUP_STORAGE_DIR)

@app.route('/api/backup', methods=['POST'])
def receive_backup():
    """Receives and stores backup files."""
    client_id = request.form.get("client_id")
    if not client_id:
        return jsonify({"status": "error", "error": "No client ID provided"}), 400

    # Create a directory for the client if it doesn't exist
    client_dir = os.path.join(BACKUP_STORAGE_DIR, client_id)
    if not os.path.exists(client_dir):
        os.makedirs(client_dir)

    timestamp = request.form.get("timestamp", "unknown")
    filename = request.form.get("filename", "backup.zip")
    file = request.files.get("file")
    
    if not file:
        return jsonify({"status": "error", "error": "No file provided"}), 400

    # Generate a unique filename for the backup
    save_filename = f"{timestamp}_{filename}"
    save_path = os.path.join(client_dir, save_filename)
    
    try:
        # Save the backup file
        file.save(save_path)
        print(f"Saved backup to {save_path}")
        return jsonify({"status": "success", "message": f"Backup stored as {save_filename}"}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint for the backup node."""
    return jsonify({"status": "Backup node healthy"}), 200

if __name__ == '__main__':
    # Start the backup node server
    app.run(host='0.0.0.0', port=8003, debug=True)
