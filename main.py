from pathlib import Path
import json
import shutil

from extract import extract_attachments
from engine import Model, Compare


class EmptyDirError(Exception):
    pass


class FileProcessing:
    def _verify_folder(self, user_path, dircheck=True, emptycheck=True):
        if not user_path.exists():
            raise FileNotFoundError("The path does not exist.")

        if dircheck and not user_path.is_dir():
            raise NotADirectoryError("The path is not a folder.")

        if emptycheck and user_path.is_dir():
            files = list(user_path.iterdir())
            if not files:
                raise EmptyDirError("The provided directory is empty")


class DefConfig:
    def __init__(self):
        self.defaults = {"threshold": 0.85}


class Config(FileProcessing, DefConfig):
    def __init__(self):
        self.profiles_path = Path("profiles.json")
        self.profile_dict = self._load(self.profiles_path)

        self.conf_path = Path("config.json")
        self.conf_dict = self._load(self.conf_path)

        self.threshold = self.conf_dict.get("threshold", self.defaults.get("threshold"))

        self.profile_list = list(self.profile_dict.keys())

        super().__init__()

    def _load(self, dpath):
        if dpath.is_file():
            with open(dpath, "r") as f:
                content = f.read().strip()

            if content:
                return json.loads(content)

        return {}

    def _save(self, d, dpath):
        with open(dpath, "w") as f:
            json.dump(d, f, indent=2)

    def save_profiles(self):
        self._save(self.profile_dict, self.profiles_path)

    def save_opts(self):
        self._save(self.conf_dict, self.conf_path)

    def add_profile(self, name):
        self.profile_dict[name] = ""  # empty = use default at runtime
        self.keys_list = list(self.profile_dict.keys())
        self.save_profiles()

    def _handle_default_profile(self, name):
        folder = Path("output") / name
        folder.mkdir(parents=True, exist_ok=True)

        return folder

    def get_folder(self, name):
        folder = self.profile_dict.get(name, None)
        if folder:
            try:
                self._verify_folder(folder, emptycheck=False)
                return Path(folder)

            except FileNotFoundError:
                print(
                    "Folder defined in config does not exist. Falling back to default..."
                )
                return self._handle_default_profile(name)

        else:
            return self._handle_default_profile(name)

    def user_to_names(self):
        print("Pick profiles by their number: ")
        for i, profile in enumerate(self.keys_list):
            print(f"{i} - {profile}")

        while True:
            user_choice = input(
                'Write your chosen profiles (e.g. "0 1 2"). Press enter = 0: '
            )
            user_choice = user_choice.strip() or "0"

            try:
                choices = user_choice.split(" ")
                choices_int = [int(x) for x in choices]
                break

            except:
                print("Invalid input! Try again...")

        return [self.keys_list[i] for i in choices_int]


class ThresholdError(Exception):
    pass


class ConfigUpdater(Config):
    def __init__(self):
        super().__init__()

    def update_threshold(self):
        print("Updating the model threshold. Input a number (0.00 - 1.00)")
        print("0.00 = all loops are accepted, 1.00 = only an exact match goes through")
        choice = input("Your choice: ")

        try:
            choice = float(choice)

            if choice < 0.00 or choice > 1.00:
                raise ThresholdError

            self.conf_dict["threshold"] = choice

            self.save_opts()

        except ThresholdError:
            print("Invalid Threshold! No changes have been made")

        except Exception as e:
            print(f"An error has occurred: {e}. No changes have been made")

    def delete_profile(self, names):
        for name in names:
            del self.profile_dict[name]
            self.profile_list = list(self.profile_dict.keys())

        self.save_profiles()

    def update_profile_folder(self, name, new_folder):
        folder_path = Path(new_folder)

        try:
            self._verify_folder(folder_path, emptycheck=False)
            self.profile_dict[name] = str(folder_path)
            self.save_profiles()

        except (FileNotFoundError, NotADirectoryError) as e:
            print(e)


class UserInput(FileProcessing):
    def __init__(self):
        self.input_folder = None
        self.profile_name = None
        super().__init__()

    def read_input(self, profile=True, what="directory", dircheck=True):
        if profile:
            while True:
                self.profile_name = input("Insert the name for the new profile: ")
                if self.profile_name:
                    break
                else:
                    print("Wrong input! Try again")

        input_folder = input(f"Drag the input {what} path: ").strip("'\"")
        input_path = Path(input_folder)

        try:
            self._verify_folder(input_path, dircheck=dircheck)
            self.input_folder = Path(input_path)

            return True

        except (FileNotFoundError, NotADirectoryError, EmptyDirError) as e:
            print(e)


if __name__ == "__main__":
    print("Welcome to loop-filtering")
    print("1 - Filter new loops: ")
    print("2 - Train a new profile: ")
    print("3 - Modify existing profiles: ")
    print("4 - Extract loops from a .mbox file: ")
    choice = input("Your choice (enter = 1): ")

    # Enter
    if not choice:
        choice = "1"

    match choice:
        case "1":  # Filter new
            user = UserInput()

            if user.read_input(profile=False):
                cfg = Config()

                if cfg.profile_dict:
                    selected_profiles = cfg.user_to_names()

                    profile_paths = [
                        Path("profiles") / (p + ".npy") for p in selected_profiles
                    ]

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

        case "2":  # Train new profile
            user = UserInput()

            if user.read_input():
                model = Model()
                model.process_all(user.input_folder)
                model.save(user.profile_name)

                cfg = Config()
                cfg.add_profile(user.profile_name)
                print(f"Profile '{user.profile_name}' saved.")

        case "3":  # Modify existing
            cfg = ConfigUpdater()

            if cfg.profile_dict:
                print("1 - Delete profiles")
                print("2 - Update output folder")
                sub_choice = input("Your choice: ")

                match sub_choice:
                    case "1":
                        selected_profiles = cfg.user_to_names()
                        confirm = input(f"Delete {selected_profiles}? (y/n): ")
                        if confirm.lower() == "y":
                            cfg.delete_profile(selected_profiles)
                            print("Profiles deleted.")

                    case "2":
                        selected_profiles = cfg.user_to_names()
                        name = selected_profiles[0]
                        new_folder = input(
                            f"Drag the new output folder path for '{name}': "
                        ).strip("'\"")
                        cfg.update_profile_folder(name, new_folder)
                        print(f"Profile '{name}' updated.")

                    case _:
                        print("Wrong input! Exiting...")

            else:
                print("No profiles found.")

        case "4":  # Extract .mbox
            user = UserInput()

            if user.read_input(profile=False, what=".mbox file", dircheck=False):
                out_dir = user.input_folder.parent / "out"
                extract_attachments(user.input_folder, out_dir)

        case _:
            print("Wrong input! Exiting...")
