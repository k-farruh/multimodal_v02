import os
from pydub import AudioSegment
from datetime import datetime
import io

def convert_audio_to_wav(input_file_path, save_to_file=False, sample_rate=16000):
    """Convert audio file to PCM WAV format. Save or return the audio data."""
    
    # Check if the input file exists
    if not os.path.isfile(input_file_path):
        raise FileNotFoundError(f"The file '{input_file_path}' does not exist.")

    # Load the audio file
    audio = AudioSegment.from_file(input_file_path)

    # Convert to mono and set the sample rate
    audio = audio.set_channels(1).set_frame_rate(sample_rate)

    # Create the output filename with datetime
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_name = f"audio_{current_time}.wav"
    output_file_path = os.path.join('audio', output_file_name)

    if save_to_file:
        # Create audio directory if it doesn't exist
        os.makedirs('audio', exist_ok=True)

        # Export as WAV file, ensuring PCM 16-bit mono
        audio.export(output_file_path, format='wav', codec='pcm_s16le')
        print(f"Converted audio saved as: {output_file_path}")

    # Save to memory and return as byte stream
    byte_io = io.BytesIO()
    audio.export(byte_io, format='wav', codec='pcm_s16le')
    byte_io.seek(0)  # Rewind the byte stream
    return byte_io.read()  # Return the byte content

if __name__ == "__main__":
    # Example usage: Change these variables as needed
    input_file = 'audio/question-Alibaba-Cloud.wav'  # Replace with your actual audio file path
    save_flag = True  # Set to True to save the file, False to return it

    try:
        if save_flag:
            convert_audio_to_wav(input_file, save_to_file=False)
        else:
            audio_data = convert_audio_to_wav(input_file, save_to_file=False)
            with open('converted_audio.wav', 'wb') as f:  # Example of saving the returned audio data
                f.write(audio_data)
                print("Audio data written to converted_audio.wav")
    except FileNotFoundError as e:
        print(e)
