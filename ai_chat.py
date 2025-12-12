try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
    import urllib.error
import json
import os
import sys

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
# In Rhino, __file__ might not be defined if running from a component, 
# but usually works in EditPythonScript
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    load_env(env_path)
except:
    # Fallback: try current directory if __file__ fails
    try:
        load_env(".env")
    except:
        pass

API_KEY = os.getenv("OPENAI_API_KEY")

def get_chat_response(user_message):
    """
    Makes an API call to OpenAI's chat completion endpoint using standard libraries.
    Compatible with IronPython 2.7 (Rhino 6/7).
    """
    if not API_KEY:
        return "Error: OPENAI_API_KEY not found. Please ensure .env file exists and is loaded."

    url = "https://api.openai.com/v1/chat/completions"
    
    # Construct the data payload
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    if IS_IRONPYTHON:
        try:
            # .NET implementation for Rhino/IronPython
            request = WebRequest.Create(url)
            request.Method = "POST"
            request.ContentType = "application/json"
            request.Headers.Add("Authorization", "Bearer " + API_KEY)
            
            # Write body
            json_str = json.dumps(data)
            bytes_data = Encoding.UTF8.GetBytes(json_str)
            request.ContentLength = bytes_data.Length
            
            req_stream = request.GetRequestStream()
            req_stream.Write(bytes_data, 0, bytes_data.Length)
            req_stream.Close()
            
            # Get response
            try:
                response = request.GetResponse()
                stream = response.GetResponseStream()
                reader = StreamReader(stream)
                response_text = reader.ReadToEnd()
                
                # Cleanup
                reader.Close()
                stream.Close()
                response.Close()
                
                response_json = json.loads(response_text)
                return response_json['choices'][0]['message']['content']
            except Exception as e:
                # Handle WebException (HTTP errors)
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
        # Standard Python implementation
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_KEY
        }
        
        # Encode data to JSON and convert to bytes
        json_data = json.dumps(data).encode('utf-8')
        
        try:
            # Create the request
            req = urllib2.Request(url, json_data, headers)
            
            # Open the URL (send request)
            response = urllib2.urlopen(req)
            
            # Read and parse the response
            response_text = response.read().decode('utf-8')
            response_json = json.loads(response_text)
            
            return response_json['choices'][0]['message']['content']
            
        except urllib2.HTTPError as e:
            return "HTTP Error: " + str(e.code) + " " + str(e.read())
        except urllib2.URLError as e:
            return "URL Error: " + str(e.reason)
        except Exception as e:
            return "Error: " + str(e)

# Example usage
if __name__ == "__main__":
    user_input = "what is the main function of mitochondria in cells?"
    print("Sending request...")
    answer = get_chat_response(user_input)
    print(answer)