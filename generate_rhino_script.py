try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
    import urllib.error
import json
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

def generate_script_content(user_message):
    if not API_KEY:
        return "Error: OPENAI_API_KEY not found. Please ensure .env file exists and is loaded."

    url = "https://api.openai.com/v1/chat/completions"
    
    system_prompt = (
        "You are an expert Rhino Python scripter. "
        "You write scripts using 'import rhinoscriptsyntax as rs'. "
        "Return ONLY the python code required to perform the user's request. "
        "Do not include markdown formatting like ```python or ```. "
        "Do not include explanations unless they are comments in the code."
        " Make sure that the generated script has the necessary imports because it will be running on its own."
    )

    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
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

if __name__ == "__main__":
    user_request = ""
    
    # Try to get input from Rhino if available
    try:
        import Rhino
        gs = Rhino.Input.Custom.GetString()
        gs.SetCommandPrompt("What do you want Rhino to do?")
        gs.AcceptNothing(True)
        gs.GetLiteralString()
        if gs.CommandResult() == Rhino.Commands.Result.Success:
            rhino_input = gs.StringResult()
            if rhino_input:
                user_request = rhino_input
    except ImportError:
        user_request = get_input_compat("What do you want Rhino to do? ")

    if not user_request:
        print("No request provided. Exiting.")
        sys.exit(0)

    print("Generating script for: " + user_request)
    generated_code = generate_script_content(user_request)
    
    # Clean up code (remove markdown blocks if the AI ignored instructions)
    if generated_code.startswith("```python"):
        generated_code = generated_code[9:]
    if generated_code.startswith("```"):
        generated_code = generated_code[3:]
    if generated_code.endswith("```"):
        generated_code = generated_code[:-3]
    
    generated_code = generated_code.strip()

    # Generate filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "script_" + timestamp + ".py"
    
    # Determine path (same directory as this script)
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    except:
        current_dir = os.getcwd()
        
    full_path = os.path.join(current_dir, filename)
    
    # Write file
    with open(full_path, "w") as f:
        f.write(generated_code)
        
    print("\n--- Generated Script (" + filename + ") ---")
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
        # In Rhino/IronPython, we can use execfile or exec
        # We need to make sure the script runs in the global context or similar
        
        try:
            # Add the directory to sys.path so imports work if needed
            if current_dir not in sys.path:
                sys.path.append(current_dir)
                
            if sys.version_info[0] < 3:
                execfile(full_path)
            else:
                with open(full_path) as f:
                    code = compile(f.read(), full_path, 'exec')
                    exec(code)
            print("Script execution finished.")
        except Exception as e:
            print("Error running script: " + str(e))
    else:
        print("Script saved but not run.")
