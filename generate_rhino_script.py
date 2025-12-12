try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
    import urllib.error
import json
import re
import os
import sys
import datetime
import time

# Check for IronPython/Rhino environment and setup .NET imports
try:
    import System
    from System.Net import WebRequest, ServicePointManager, SecurityProtocolType
    from System.IO import StreamReader
    from System.Text import Encoding
    # Ensure TLS 1.2 is enabled for OpenAI API
    try:
        ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12
    except:
        pass
    IS_IRONPYTHON = True
except ImportError:
    IS_IRONPYTHON = False

# Function to manually load .env file since python-dotenv is not standard in IronPython
def load_env(filepath):
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value
    except Exception as e:
        print("Could not load .env file: " + str(e))

# Try to locate .env file
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    load_env(env_path)
except:
    try:
        load_env(".env")
    except:
        pass

API_KEY = os.getenv("OPENAI_API_KEY")

def get_sessions_dir():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except:
        script_dir = os.getcwd()
    sessions_dir = os.path.join(script_dir, "sessions")
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir)
    return sessions_dir

def get_latest_session_folder():
    sessions_dir = get_sessions_dir()
    subdirs = [os.path.join(sessions_dir, d) for d in os.listdir(sessions_dir) if os.path.isdir(os.path.join(sessions_dir, d))]
    if not subdirs:
        return None
    subdirs.sort()
    return subdirs[-1]

def create_new_session_folder():
    sessions_dir = get_sessions_dir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_folder = os.path.join(sessions_dir, timestamp)
    os.makedirs(session_folder)
    return session_folder

def get_next_index(session_folder):
    files = os.listdir(session_folder)
    count = 0
    for f in files:
        if f.startswith("script_") and f.endswith(".py"):
            count += 1
    return count

def build_chat_history(session_folder, system_prompt):
    messages = [{"role": "system", "content": system_prompt}]
    
    index = 0
    while True:
        prompt_file = os.path.join(session_folder, "prompt_{}.txt".format(index))
        script_file = os.path.join(session_folder, "script_{}.py".format(index))
        error_file = os.path.join(session_folder, "error_{}.txt".format(index))
        
        if not os.path.exists(prompt_file):
            break
            
        with open(prompt_file, 'r') as f:
            prompt_text = f.read()
        messages.append({"role": "user", "content": prompt_text})
        
        if os.path.exists(script_file):
            with open(script_file, 'r') as f:
                script_code = f.read()
            messages.append({"role": "assistant", "content": script_code})
            
        if os.path.exists(error_file):
            with open(error_file, 'r') as f:
                error_text = f.read()
            messages.append({"role": "user", "content": "The previous script caused an error: " + error_text})
            
        index += 1
        
    return messages

def generate_script_content(messages):
    if not API_KEY:
        return "Error: OPENAI_API_KEY not found. Please ensure .env file exists and is loaded."

    url = "https://api.openai.com/v1/chat/completions"
    
    data = {
        "model": "gpt-4o",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }

    if IS_IRONPYTHON:
        try:
            request = WebRequest.Create(url)
            request.Method = "POST"
            request.ContentType = "application/json"
            request.Headers.Add("Authorization", "Bearer " + API_KEY)
            
            json_str = json.dumps(data)
            bytes_data = Encoding.UTF8.GetBytes(json_str)
            request.ContentLength = bytes_data.Length
            
            req_stream = request.GetRequestStream()
            req_stream.Write(bytes_data, 0, bytes_data.Length)
            req_stream.Close()
            
            try:
                response = request.GetResponse()
                stream = response.GetResponseStream()
                reader = StreamReader(stream)
                response_text = reader.ReadToEnd()
                reader.Close()
                stream.Close()
                response.Close()
                
                response_json = json.loads(response_text)
                return response_json['choices'][0]['message']['content']
            except Exception as e:
                if hasattr(e, 'Response') and e.Response:
                    stream = e.Response.GetResponseStream()
                    reader = StreamReader(stream)
                    err_text = reader.ReadToEnd()
                    reader.Close()
                    stream.Close()
                    e.Response.Close()
                    return "API Error: " + err_text
                return "Error getting response: " + str(e)
        except Exception as e:
            return "Error (.NET): " + str(e)
    else:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_KEY
        }
        json_data = json.dumps(data).encode('utf-8')
        try:
            req = urllib2.Request(url, json_data, headers)
            response = urllib2.urlopen(req)
            response_text = response.read().decode('utf-8')
            response_json = json.loads(response_text)
            return response_json['choices'][0]['message']['content']
        except urllib2.HTTPError as e:
            return "HTTP Error: " + str(e.code) + " " + str(e.read())
        except urllib2.URLError as e:
            return "URL Error: " + str(e.reason)
        except Exception as e:
            return "Error: " + str(e)

def get_input_compat(prompt):
    if sys.version_info[0] < 3:
        return raw_input(prompt)
    else:
        return input(prompt)

SYSTEM_PROMPT = (
    "You are an expert Rhino Python scripter. "
    "You write scripts using 'import rhinoscriptsyntax as rs'. "
    "Return ONLY the python code required to perform the user's request. "
    "Do not include markdown formatting like ```python or ```. "
    "Do not include explanations unless they are comments in the code."
    " Make sure that the generated script has the necessary imports because it will be running on its own."
)

if __name__ == "__main__":
    session_folder = get_latest_session_folder()
    if not session_folder:
        print("No existing session found. Starting a new session.")
        session_folder = create_new_session_folder()
    else:
        print("Continuing session: " + os.path.basename(session_folder))

    while True:
        user_request = ""
        
        # Try to get input from Rhino if available
        try:
            import Rhino
            gs = Rhino.Input.Custom.GetString()
            gs.SetCommandPrompt("What do you want Rhino to do? (or type 'quit' to exit)")
            gs.AcceptNothing(True)
            gs.GetLiteralString()
            if gs.CommandResult() == Rhino.Commands.Result.Success:
                rhino_input = gs.StringResult()
                if rhino_input:
                    user_request = rhino_input
        except ImportError:
            user_request = get_input_compat("What do you want Rhino to do? (or type 'quit' to exit) ")

        if not user_request:
            print("No request provided.")
            continue

        if user_request.strip().lower() in ["quit", "exit", "stop"]:
            print("Exiting session.")
            break

        # Build history
        messages = build_chat_history(session_folder, SYSTEM_PROMPT)
        messages.append({"role": "user", "content": user_request})

        print("Generating script for: " + user_request)
        generated_code = generate_script_content(messages)
        
        # Clean up code (extract from markdown block if present)
        code_block_match = re.search(r"```(?:python)?\s*(.*?)```", generated_code, re.DOTALL)
        if code_block_match:
            generated_code = code_block_match.group(1)
        
        generated_code = generated_code.strip()

        # Determine index for filenames
        index = get_next_index(session_folder)
        
        # Save prompt
        prompt_filename = "prompt_{}.txt".format(index)
        with open(os.path.join(session_folder, prompt_filename), "w") as f:
            f.write(user_request)

        # Save script
        script_filename = "script_{}.py".format(index)
        full_path = os.path.join(session_folder, script_filename)
        
        with open(full_path, "w") as f:
            f.write(generated_code)
            
        print("\n--- Generated Script (" + script_filename + ") ---")
        print(generated_code)
        print("------------------------------------------\n")
        
        # Ask to run
        run_it = ""
        try:
            import Rhino
            gs = Rhino.Input.Custom.GetString()
            gs.SetCommandPrompt("Do you want to run this script? (Y/N)")
            gs.AcceptNothing(True)
            gs.GetLiteralString()
            if gs.CommandResult() == Rhino.Commands.Result.Success:
                run_it = gs.StringResult()
        except ImportError:
            run_it = get_input_compat("Do you want to run this script? (Y/N): ")
            
        if run_it and run_it.upper() == "Y":
            print("Running script...")
            # Execute the script
            try:
                # Add the directory to sys.path so imports work if needed
                if session_folder not in sys.path:
                    sys.path.append(session_folder)
                    
                if sys.version_info[0] < 3:
                    execfile(full_path)
                else:
                    with open(full_path) as f:
                        code = compile(f.read(), full_path, 'exec')
                        exec(code)
                print("Script execution finished.")
            except Exception as e:
                error_msg = str(e)
                print("Error running script: " + error_msg)
                # Save error
                error_filename = "error_{}.txt".format(index)
                with open(os.path.join(session_folder, error_filename), "w") as f:
                    f.write(error_msg)
        else:
            print("Script saved but not run.")
