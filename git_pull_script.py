"""
To add this script to a Rhino toolbar button:
1. Right-click toolbar area > Show Toolbar > New (or select existing).
2. Shift + Right-Click a button to edit.
3. Set Command to: ! _-RunPythonScript "c:\\git\\grasshopper\\git_pull_script.py"
4. Click OK.
"""
import os
import subprocess

def git_pull():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to that directory
    os.chdir(script_dir)
    
    print(f"Running 'git pull' in {script_dir}...")
    
    try:
        # Run git pull
        result = subprocess.run(["git", "pull"], check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error running git pull:")
        print(e.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    git_pull()
