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
    
    print("Running 'git pull' in {}...".format(script_dir))
    
    try:
        # Run git pull
        process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            print(stdout)
        else:
            print("Error running git pull:")
            print(stderr)

    except Exception as e:
        print("An unexpected error occurred: {}".format(e))

if __name__ == "__main__":
    git_pull()
