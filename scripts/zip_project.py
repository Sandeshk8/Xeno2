import zipfile
import os
import datetime

def zip_project():
    # Get the current directory (project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Generate a timestamped filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"wordchain_bot_backup_{timestamp}.zip"
    
    # Files/Directories to exclude
    EXCLUDES = {
        '.venv', 
        '.git', 
        '__pycache__', 
        '.vscode', 
        '.idea',
        'nohup.out',
        zip_filename # Don't zip the zip file itself if it exists
    }

    print(f"Zipping project to {zip_filename}...")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_root):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDES]
            
            for file in files:
                if file in EXCLUDES or file.endswith('.pyc'):
                    continue
                
                file_path = os.path.join(root, file)
                # Create a relative path for the archive
                arcname = os.path.relpath(file_path, project_root)
                
                print(f"Adding {arcname}")
                zipf.write(file_path, arcname)
                
    print(f"\n✅ Project successfully zipped to: {zip_filename}")

if __name__ == "__main__":
    zip_project()
