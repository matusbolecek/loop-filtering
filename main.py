from pathlib import Path
from engine import Model, Compare
import json
import shutil

class EmptyDirError(Exception):
    pass

class FileProcessing:
    def _verify_folder(self, user_path, dircheck=True, emptycheck=True):
        if not user_path.exists():
            raise FileNotFoundError('The path does not exist.')
        
        if dircheck and not user_path.is_dir():
            raise NotADirectoryError('The path is not a folder.')
        
        files = list(user_path.iterdir())
        if emptycheck and not files:
            raise EmptyDirError('The provided directory is empty')

class Config(FileProcessing):
    def __init__(self):
        self.dict = {} 
        self.path = Path('config.json') 

        if self.path.is_file():
            with open(self.path, "r") as f:
                json.dump(self.dict, f)
    
            self.keys_list = list(self.dict.keys())
        else:
            print('No config.json found. Aborting')

        super().__init__()

    def _handle_default(self, name):
        folder = Path('output') / name
        folder.mkdir(parents=True, exist_ok=True)

        return folder

    def get_folder(self, name):
        folder = self.dict.get(name, None)
        if folder:
            try:
                self._verify_folder(folder, emptycheck=False) 
                return Path(folder)

            except FileNotFoundError:
                print('Folder defined in config does not exist. Falling back to default...') 
                return self._handle_default(name)

        else:
            return self._handle_default(name)

    def user_to_names(self):
        print('Pick profiles by their number: ')
        for i, profile in enumerate(self.keys_list):
            print(f'{i} - {profile}')

        while True:
            user_choice = input('Write your chosen profiles (e.g. "0 1 2"). Press enter = 0: ') 
            user_choice = user_choice.strip() or "0"
            
            try:
                choices = user_choice.split(' ')
                choices_int = [int(x) for x in choices] 
                break

            except:
                print('Invalid input! Try again...')

        return [self.keys_list[i] for i in choices_int]

class UserInput(FileProcessing):
    def __init__(self):
        self.input_folder = None
        self.profile_name = None
        super().__init__()
        
    def read_input(self, profile=True):
        if profile:
            while True: 
                self.profile_name = input('Insert the name for the new profile: ')
                if self.profile_name:
                    break
                else:
                    print('Wrong input! Try again')

        input_folder = input('Drag the input directory path: ').strip("'\"")
        input_path = Path(input_folder)

        try:
            self._verify_folder(input_path)
            self.input_folder = Path(input_path)

            return True

        except (FileNotFoundError, NotADirectoryError, EmptyDirError) as e:
            print(e)
        
if __name__ == "__main__":
    print('Welcome to loop-filtering')
    print('1 - Filter new loops: ')
    print('2 - Train a new profile: ')
    print('3 - Modify existing profiles: ')
    print('4 - Extract loops from a .mbox file: ')
    choice = input('Your choice (enter = 1): ') 

    # Enter
    if not choice:
        choice = "1" 

    match choice: 
        case "1": # Filter new
            user = UserInput()

            if user.read_input():
                cfg = Config()

                if cfg.dict:
                    selected_profiles = cfg.user_to_names()
                    
                    profile_paths = [Path('profiles') / (p + '.npy') for p in selected_profiles]

                    # This should not happen unless some file moving bullshit...
                    missing = [p for p in profile_paths if not p.exists()]
                    if missing:
                        print(f"Missing profile files: {[p.name for p in missing]}")

                    else:
                        output_paths = [cfg.get_folder(p) for p in selected_profiles]
                    
                        comp = Compare(profile_paths)
                        pairs = comp.compare_all(user.input_folder)
                    
                        for loop, i in pairs:
                            if i is not None:
                                out_path = output_paths[i] / loop.name
                                shutil.move(loop, out_path)         

        case "2": # Train new profile
            user = UserInput() 
            if user.read_input():
                model = Model()
                model.process_all(user.input_folder)
                model.save(user.profile_name)

        case "3": # Modify existing
            pass

        case "4": # Extract .mbox 
            pass

        case _:
            print('Wrong input! Exiting...')
