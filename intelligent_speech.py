# -*- coding: UTF-8 -*-
import http.client
import json

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

from audio_convert import convert_audio_to_wav

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()



class IntelligentSpeech:
    def __init__(self):
        self.app_key = os.getenv('ALIBABA_NLS_APP_KEY')
        self.token = self.obtain_token()
        self.host = 'nls-gateway-ap-southeast-1.aliyuncs.com'
        self.url = 'http://nls-gateway-ap-southeast-1.aliyuncs.com/stream/v1/asr'

    def obtain_token(self):
        # Create an AcsClient instance.
        client = AcsClient(
            os.getenv('ALIBABA_ACCESS_KEY_ID'),
            os.getenv('ALIBABA_ACCESS_KEY_SECRET'),
            # "cn-shanghai"
            "ap-southeast-1"
        )

        # Create a request and configure request parameters. 
        request = CommonRequest()
        request.set_method('POST')
        # request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
        request.set_domain("nlsmeta.ap-southeast-1.aliyuncs.com")
        request.set_version('2019-07-17')
        request.set_action_name('CreateToken')

        try : 
            response = client.do_action_with_exception(request)
            # print(response)

            jss = json.loads(response)
            if 'Token' in jss and 'Id' in jss['Token']:
                token = jss['Token']['Id']
                # expireTime = jss['Token']['ExpireTime']
                # print("token = " + token)
                # print("expireTime = " + str(expireTime))
                return token
        except Exception as e:
            return f"An error occurred: {str(e)}"

        
    def audio_transcription(self, audio_file, format='wav', sample_rate=16000,
                            enable_punctuation_prediction=True,
                            enable_inverse_text_normalization=True,
                            enable_voice_detection=False):
        
        # Specify the audio file.
        format = 'pcm'

        # Configure the RESTful request parameters.
        request = self.url + '?appkey=' + self.app_key
        request = request + '&format=' + format
        request = request + '&sample_rate=' + str(sample_rate)

        if enable_punctuation_prediction :
            request = request + '&enable_punctuation_prediction=' + 'true'
        if enable_inverse_text_normalization :
            request = request + '&enable_inverse_text_normalization=' + 'true'
        if enable_voice_detection :
            request = request + '&enable_voice_detection=' + 'true'

        print('Request: ' + request)

        pcm_1_wav_content = convert_audio_to_wav(audio_file)


        # Configure the HTTP request header.
        httpHeaders = {
            'X-NLS-Token': self.token,
            'Content-type': 'application/octet-stream',
            'Content-Length': len(pcm_1_wav_content)
            }


        # Use the http.client module for Python 3.x.
        conn = http.client.HTTPConnection(self.host)

        conn.request(method='POST', url=request, body=pcm_1_wav_content, headers=httpHeaders)

        response = conn.getresponse()
        print('Response status and response reason:')
        print(response.status ,response.reason)

        body = response.read()
        try:
            print('Recognize response is:')
            body = json.loads(body)
            print(body)

            status = body['status']
            if status == 20000000 :
                result = body['result']
                print('Recognize result: ' + result)
            else :
                print('Recognizer failed!')

        except ValueError:
            print('The response is not json format string')

        conn.close()
        
        return result


if __name__ == "__main__":
    # Example usage
    client = IntelligentSpeech()
    audio_file = 'audio/question-Alibaba-Cloud.wav'
    transcription_result = client.audio_transcription(audio_file=audio_file)
    print(f"Transcription Result: {transcription_result}")
