from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Directory to store backups
BACKUP_STORAGE_DIR = "backups"
if not os.path.exists(BACKUP_STORAGE_DIR):
    os.makedirs(BACKUP_STORAGE_DIR)

@app.route('/api/backup', methods=['POST'])
def receive_backup():
    timestamp = request.form.get("timestamp", "unknown")
    filename = request.form.get("filename", "backup.zip")
    file = request.files.get("file")
    
    if not file:
        return jsonify({"status": "error", "error": "No file provided"}), 400

    save_filename = f"{timestamp}_{filename}"
    save_path = os.path.join(BACKUP_STORAGE_DIR, save_filename)
    
    try:
        file.save(save_path)
        print(f"Saved backup to {save_path}")
        return jsonify({"status": "success", "message": f"Backup stored as {save_filename}"}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "Backup node healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)
