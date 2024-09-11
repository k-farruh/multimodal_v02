import gradio as gr
import os
import datetime
import shutil

import dashscope

import gradio as gr
from http import HTTPStatus
from llm_service import LLMService
from oss_url import upload_image_to_oss
from intelligent_speech import IntelligentSpeech

from dotenv import load_dotenv

load_dotenv()

dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY")
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'


def get_file_extension(file_path: str) -> str:
    _, file_extension = os.path.splitext(file_path)
    return file_extension.lower()

# Initialize the LLMService object with the configuration
solver = LLMService()

nls_client = IntelligentSpeech()

def transcribe_and_process_audio(audio_file_path):
    transcription = nls_client.audio_transcription(audio_file_path)
    return process_text(transcription)

def process_text(text_content, history=[]):
    # history_langchain_format = []
    # for human, ai in history:
    #     history_langchain_format.append(HumanMessage(content=human))
    #     history_langchain_format.append(AIMessage(content=ai))

    # # Now we need to handle the case when there are no files provided:
    # # Convert the list of messages to a single string because llm.invoke expects a string prompt.
    # prompt = "\n".join([message.content for message in history_langchain_format])
    # prompt += "\n" + text_content  # Add the latest message from the user
    # prompt = prompt.strip()  # Remove any leading/trailing whitespace
    
    # Use the invoke method instead of __call__
    try:
        llm_response = solver.content_query(text_content, history)  # Assuming the prompt is correctly formatted as a string
        return llm_response  # You may need to adjust this based on how llm.invoke returns the response
    except Exception as e:
        return f"An error occurred: {str(e)}"    

def upload_knowledge(file_path: str) -> str:
    if file_path is None:
        return "No file was uploaded."


    supported_extensions = ['.pdf', '.txt', '.csv', '.doc', '.docx', '.xls', '.xlsx']
    file_extension = get_file_extension(file_path)
    
    if file_extension not in supported_extensions:
        return f"Unsupported file format: {file_extension}"
    
    # Use a unique timestamp to save the uploaded file to prevent overwriting
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_file_name = f"uploaded_{timestamp}{file_extension}"
    save_path = os.path.join("uploads", safe_file_name)
    
    # Ensure uploads directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Copy the original image file to the new location
    shutil.copy(file_path, save_path)
        
    # Custom knowledge uploading logic here (adjust as needed)
    solver.upload_file_knowledge(save_path)
    
    return "Successfully uploaded and processed the knowledge document."



def process_file(file_path: str, caption: str, history) -> str:
    """Determines file format and delegates to specific processing functions."""
    _, file_extension = os.path.splitext(file_path)
    # Lists of supported audio and image formats
    audio_formats = ['.mp3', '.wav', '.m4a', '.flac']
    image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    
    if file_extension in audio_formats:
        return process_audio_file(file_path, history)
    elif file_extension in image_formats:
        return process_image_file(file_path, caption)
    else:
        return "Unsupported file format."

def process_audio_file(audio_file_path: str, history) -> str:
    transcription = nls_client.audio_transcription(audio_file_path)
    return process_text(transcription, history)

def process_image_file(file_path: str, caption: str) -> str:
    # Create images folder if it does not exist
    images_dir = "images"
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
        
    # Get the file extension and construct the new image file name with a timestamp to avoid overwriting
    extension = get_file_extension(file_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    image_file_name = f"input_image_{timestamp}{extension}"
    image_file_path = os.path.join(images_dir, image_file_name)
    
    # Copy the original image file to the new location
    shutil.copy(file_path, image_file_path)
    
    # Construct the prompt and the message payload
    prompt = "Please answer me in English. " + caption
    """Sample of use local file.
       linux&mac file schema: file:///home/images/test.png
       windows file schema: file://D:/images/abc.png
    """
    public_url = upload_image_to_oss(os.path.abspath(image_file_path))
    messages = [
        {
            "role": "user",
            "content": [
                {"image": public_url},
                {"text": prompt}
            ]
        }
    ]
    
    # Call the API with the message
    response = dashscope.MultiModalConversation.call(model='qwen-vl-max',
                                                     messages=messages)
    # Check if the response is OK and extract the text, otherwise return the error code and message
    if response.status_code == HTTPStatus.OK:
        result_text = response["output"]["choices"][0]["message"]["content"][0]["text"]
    else:
        result_text = f"Error {response.code}: {response.message}"
    return result_text

def process_input(message_dict, history):
    files = message_dict.get('files', [])
    text_content = message_dict.get('text')
    if len(files) == 1:
        file_path = files[0]["path"]
        if os.path.isfile(file_path):
            return process_file(file_path, text_content, history)
        else:
            return "The file does not exist."
    elif len(files) > 1:
        return "Please provide only one file."
    else:
        return process_text(text_content, history)
        

# Custom HTML and CSS for the footer
custom_footer_html = """
<style>
.custom-footer {
    background-color: #f8f9fa; /* Light gray background */
    color: #343a40; /* Dark gray text */
    text-align: center;
    padding: 20px 0;
    font-size: 16px;
    border-top: 1px solid #dee2e6; /* Light gray border on top */
}
.custom-footer a {
    color: #007bff; /* Bootstrap's default blue for links */
    text-decoration: none;
}
.custom-footer a:hover {
    text-decoration: underline;
}
</style>
<div class="custom-footer">
    For further information, please contact  <a href="mailto:k.farruh@aliyun-inc.com">Farruh</a>
</div>
"""

# Setup the Gradio interface
with gr.Blocks(
        title="Multimodal LLM",
        theme=gr.themes.Soft(),
        css="footer {visibility: hidden}",
    ) as app:
    with gr.Row():
        with gr.Column(scale=3):
            # Left panel content
            markdown_image = "https://img.alicdn.com/imgextra/i3/O1CN014Z4bMM22j2oWMT4vE_!!6000000007155-0-tps-3840-816.jpg"
            gr.Markdown(f"![]({markdown_image})")
            gr.Markdown("[Alibaba Cloud Intelligence](https://www.alibabacloud.com/)")
            gr.Markdown("The cutting-edge Multimodal LLM from Qwen, interactions by seamlessly integrating text, image, and audio inputs to deliver precise text outputs. Powered by Qwen LLM, Qwen-VL foundation models, and Alibaba Cloud's Intelligent Speech Interaction.")
            gr.Markdown("How to work with tutorial [video link]()")


            file_input = gr.File(file_count="single", 
                             file_types=['pdf', 'txt', 'csv', 'doc', 'docx', 'xls', 'xlsx'], 
                             label="Upload Document")
            submit_button = gr.Button("Upload")

            # Before starting the Blocks context
            output_text = gr.Text(label="Upload Result")

            # Link the file input and button with the upload_knowledge function
            # Correct the use of output component in the .click() function
            submit_button.click(fn=upload_knowledge, inputs=file_input, outputs=output_text)
            
        
        with gr.Column(scale=7):
            demo = gr.ChatInterface(process_input, 
                        title="Alibaba Cloud Multimodal GenAI Smart Assistant Te",
                        description="The test environment for RAG, Vision LLM and Audio capabilities. <br> By Product and Solution Team",
                        examples=[{"text": "Hello", "files": []}, {"text": "Who are you", "files": []}],
                        multimodal=True
                       )
        


    # This is the new line to add the custom footer with CSS
    gr.HTML(custom_footer_html)

app.queue()
# Launch the app with specific server and SSL configurations
app.launch(
    server_name="0.0.0.0",
    server_port=8080,
    allowed_paths=["/"]
    # ssl_certfile="/root/multimodal/keys/cert.pem",
    # ssl_keyfile="/root/multimodal/keys/key.pem",
    # ssl_verify=False
)



# openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes
# nohup python gradio_app.py 
# kill -9 $(lsof -t -i:8080)