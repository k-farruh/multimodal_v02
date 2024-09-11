import os
import dashscope

dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY")
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

def call_with_local_file():
    """Sample of use local file.
       linux&mac file schema: file:///home/images/test.png
       windows file schema: file://D:/images/abc.png
    """
    local_file_path = 'file:///root/multimodal/images/input_image_20240906_120427.jpeg'
    prompt = "Please answer me in English. what is this image?"

    messages = [
        {
            "role": "user",
            "content": [
                {"image": local_file_path},
                {"text": prompt}
            ]
        }
    ]
    response = dashscope.MultiModalConversation.call(model='qwen-vl-plus', messages=messages)
    print(response)


def simple_multimodal_conversation_call():
    """Simple single round multimodal conversation call.
    """
    messages = [
        {
            "role": "user",
            "content": [
                {"image": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"},
                # {"image": 'http://farruh-singapore-oss.oss-ap-southeast-1.aliyuncs.com/multimodal_images/input_image_20240911_112408.jpeg'},
                {"text": "这是什么?"}
            ]
        }
    ]
    responses = dashscope.MultiModalConversation.call(model='qwen-vl-plus',
                                           messages=messages,
                                           stream=True)
    for response in responses:
        print(response)



if __name__ == '__main__':
    # call_with_local_file()
    simple_multimodal_conversation_call()
