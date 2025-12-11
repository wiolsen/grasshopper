import os
import sys
import uuid
from openai import OpenAI

def generate_python_script(prompt_text):
    # Initialize the OpenAI client
    # Assumes OPENAI_API_KEY is set in environment variables
    client = OpenAI()

    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a Python code generator. Output only valid Python code. Do not output markdown formatting, backticks, or explanations."},
                {"role": "user", "content": prompt_text}
            ]
        )

        generated_code = response.choices[0].message.content

        # Define the output directory
        output_dir = "generatedScripts"
        
        # Create the directory if it does not exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Generate a unique filename
        unique_filename = f"script_{uuid.uuid4().hex}.py"
        file_path = os.path.join(output_dir, unique_filename)

        # Write the generated code to the file
        with open(file_path, "w") as f:
            f.write(generated_code)

        print(f"Successfully generated script: {file_path}")
        return file_path

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        user_prompt = input("Enter the prompt for the Python script: ")
    
    generate_python_script(user_prompt)
