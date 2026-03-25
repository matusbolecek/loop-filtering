# Automated Loop Filtering

# The Problem
Many music instrumental producers share their e-mails under their YouTube type-beats. This leads to large amounts of loops / samples arriving into their inboxes. While this is often nice, as many of the samples are useful for further production, the inboxes eventually fill up and this causes problems. Moreover, with large quantities of samples coming to one's inbox, it is not time well spent manually sorting hundreds of loops every day.

What people usually do is start ignoring these e-mails and only using loops from some creators, that the producer knows will deliver quality. However, this leaves possibly hundreds of high-quality loops lost in inboxes...

# The solution
A machine-learning model that learns what the producer wants to use and saving this profile as a numpy array. The provided tracks are converted into a set of high-dimension vector embeddings. Afterwards, these sets are compared against new loops from the mailbox. If a loop matches some of the loops in the profile with a high-enough threshold (a value between 0-1, that determines how strict the model is and how similar must the loops be to be considered a match), it will be moved into the set directory. This way, it is an entirely passive process that can be often more accurate in delivering similar loops (since during longer sorting sessions, one's ears eventually get tired and this leads to worse picks).

# Installation
It is required to have python 3.10+ installed on the system. A virtual environment is recommended for this, as many packages will be pulled. Then, run pip install -r requirements.txt to download all the required packages - namely PyTorch, librosa, transformers. Afterwards, you are ready to use the filtering tool.

# Usage
Everything is done using a command line tool that resides in main.py. The interface is simple and should be understandable. One must first train a profile on a folder of loops. It is recommended to be as precise with these choices, as this will determine the quality of the filtering process. A minimum of 5 loops is required, though it is well recommended to not go under 20-30. It is well worth it to have a bigger number of loops in the profile - one only has to train it once and it will improve the precision greatly. The loops are trimmed and therefore the layout of the loop itself does not matter, as long as it starts with the main part right at the beginning (by default, the first 10 seconds are taken into account). After training a profile, one can run the main filter. 

## Multiple profiles
If a producer wants to have multiple profiles with different loop styles, this can be achieved by training multiple profiles and then setting them in filtering. Keep in mind the order matters for priority. This feature is mainly useful for producers with multiple channels in different styles. This way, it is not necessary to run filtering multiple times on the same folder - all can be done in one run. 

## Linking folders
It is recommended to link a folder to the profiles, so that the loops that match the profiles can be immediately moved to the designated folder and be ready to use. 

## Extracting .mbox
For mailbox functionality, the main process is requesting a Google data export of the entire mailbox (Go to Google Takeout → select Gmail → export as .mbox) and then using the provided tool to extract this file. Afterwards, one can delete the mails with attachments. Some faster and more automated approach might be coming in the future, though this solution is far simpler and less limited. 

# Other notes:
- The supported formats of audio are .wav, .mp3, .flac, .aiff, .ogg. 
- Files under 10 seconds are automatically ommited, so one does not have to bother with filtering out producer tags in the emails.


