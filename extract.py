import mailbox
import os
from pathlib import Path

def extract_attachments(mbox_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    allowed_extensions = {'.mp3', '.wav', '.flac'}
    
    mbox = mailbox.mbox(mbox_path)
    for message in mbox:
        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
                
            filename = part.get_filename()
            if filename:
                # Check file extensions and remove tags
                file_path = Path(filename)
                if (file_path.suffix.lower() in allowed_extensions and 
                    'tag' not in file_path.stem.lower()):
                    
                    filepath = Path(output_dir) / Path(filename).name
                    
                    # Handle duplicate filenames
                    counter = 1
                    while filepath.exists():
                        stem = filepath.stem
                        filepath = Path(output_dir) / f"{stem}_{counter}{filepath.suffix}"
                        counter += 1
                    
                    # Extract and save attachment
                    payload = part.get_payload(decode=True)
                    if payload:
                        with open(filepath, 'wb') as f:
                            f.write(payload)
    
    return output_dir

if __name__ == "__main__":
    input_file = input('Input the .mbox file').strip("'\"")
    output_folder = input('Input the output directory path: ').strip("'\"")
    
    extract_attachments(input_file, output_directory)
