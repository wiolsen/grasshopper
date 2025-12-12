import os
import datetime

def get_sessions_dir():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except:
        script_dir = os.getcwd()
    sessions_dir = os.path.join(script_dir, "sessions")
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir)
    return sessions_dir

def create_new_session_folder():
    sessions_dir = get_sessions_dir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_folder = os.path.join(sessions_dir, timestamp)
    os.makedirs(session_folder)
    return session_folder

if __name__ == "__main__":
    session_folder = create_new_session_folder()
    print("Created new session folder: " + session_folder)
