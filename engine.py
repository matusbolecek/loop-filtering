import torch
import librosa
import numpy as np
from transformers import Wav2Vec2FeatureExtractor, AutoModel
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from typing import Sequence


class Params:
    def __init__(self):
        self.sample_rate = 24000
        self.duration = 10


class FileShort(Exception):
    pass


class Audio(Params):
    def __init__(self):
        self.audio = None
        super().__init__()

    def process(self, audio_path: Path) -> None:
        audio, sr = librosa.load(audio_path, sr=self.sample_rate)
        trimmed, _ = librosa.effects.trim(audio)

        duration = librosa.get_duration(y=trimmed, sr=self.sample_rate)
        if duration < self.duration:
            raise FileShort

        length = sr * self.duration
        audio_cut = trimmed[:length]

        self.audio = audio_cut


class FileProcessing:
    def _process_folder(self, loops_dir) -> list[Path]:
        formats = {".wav", ".mp3", ".flac", ".aiff", ".ogg"}
        p = Path(loops_dir)

        if not p.exists():
            raise FileNotFoundError(f"Directory not found: {p}")
        if not p.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {p}")

        loops = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() in formats]

        if not loops:
            raise ValueError(
                f"No supported audio files found in: {p} (supported: {formats})"
            )

        return sorted(loops)


class Model(Params, FileProcessing):
    def __init__(self):
        self.model_name = "m-a-p/MERT-v1-95M"
        self.processor = Wav2Vec2FeatureExtractor.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name, trust_remote_code=True)
        self.embeddings = []
        self.processed_loops = []
        super().__init__()

    def get_embedding(self, audio) -> np.ndarray:
        inputs = self.processor(
            audio, sampling_rate=self.sample_rate, return_tensors="pt"
        )
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)

            last_layer = outputs.last_hidden_state
            embedding = torch.mean(last_layer, dim=1)

        return embedding.numpy().flatten()

    def process_all(self, loops_dir) -> None:
        loops = self._process_folder(loops_dir)

        n_loops = len(loops)
        for i, loop in enumerate(loops):
            try:
                print(f"{i + 1}/{n_loops}: Processing {loop.name}")
                loop_obj = Audio()
                loop_obj.process(loop)
                embedding = self.get_embedding(loop_obj.audio)
                self.embeddings.append(embedding)
                self.processed_loops.append(loop)

            except FileShort:
                print(f"Skipping {loop}: Loop is too short")

    def save(self, name) -> None:
        if self.embeddings:
            if len(self.embeddings) < 5:
                print(
                    "Warning! There is <5 embeddings generated. This is generally not recommended for best accuracy"
                )
            profile_folder = Path("profiles")
            if not profile_folder.exists():
                profile_folder.mkdir(parents=True, exist_ok=True)

            save_path = profile_folder / name
            np.save(save_path, np.array(self.embeddings))

        else:
            print("There are no embeddings generated! Skipping.")


class Compare(FileProcessing):
    def __init__(self, profile_paths: Sequence, threshold: float = 0.85):
        # profiles should be pathlib objects
        self.profile_names = [profile.stem for profile in profile_paths]
        self.base_vectors = [np.load(arr) for arr in profile_paths]
        self.threshold = threshold
        self.embedder = Model()
        super().__init__()

    def _compare(self, base_vectors, new_vector, k=5) -> np.float64:
        similarities = cosine_similarity([new_vector], base_vectors)[0]
        k_indices = np.argsort(similarities)[-k:]
        top_scores = similarities[k_indices]

        return np.mean(top_scores)

    def compare_all(self, loops_dir) -> list:
        loops = self._process_folder(loops_dir)

        n_loops = len(loops)
        output = []

        print("Processing embeddings for all loops:")
        print("Matching to profiles:")
        for i, profile in enumerate(self.profile_names):
            print(f"{i} - {profile}")

        for i, loop in enumerate(loops):
            try:
                print(f"{i + 1}/{n_loops}: Processing {loop.name}")
                loop_obj = Audio()
                loop_obj.process(loop)
                embedding = self.embedder.get_embedding(loop_obj.audio)

                matched = None
                for j, vec in enumerate(self.base_vectors):
                    score = self._compare(vec, embedding)

                    if score >= self.threshold:
                        matched = j
                        print(f"Found match in choice nr. {j}")
                        break

                output.append((loop, matched))

            except FileShort:
                print(f"No match for loop {loop}: Loop is too short")
                output.append((loop, None))

        return output
