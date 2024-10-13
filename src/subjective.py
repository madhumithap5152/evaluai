import logging
from typing import Tuple
import nltk as nlp
import numpy as np
import cv2
import speech_recognition as sr
import time

# Ensure necessary NLTK data is available
try:
    nlp.data.find('tokenizers/punkt')
except LookupError:
    nlp.download('punkt')

class ProctoringSystem:
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = sr.Recognizer()
    
    def monitor_microphone(self):
        mic = sr.Microphone()
        with mic as source:
            print("Calibrating microphone for ambient noise, please be silent...")
            self.recognizer.adjust_for_ambient_noise(source)
            print("Monitoring microphone...")
            audio = self.recognizer.listen(source, timeout=5)
        
        try:
            transcript = self.recognizer.recognize_google(audio)
            print(f"Transcript: {transcript}")
            if len(transcript.split()) > 10:  # Simple heuristic: too many words
                print("Warning: Multiple voices detected!")
                return True
            else:
                print("Microphone input is clear.")
                return False
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
        return False
    
    def monitor_camera(self):
        cap = cv2.VideoCapture(0)  # Open the webcam
        face_detected = False
        start_time = time.time()
        
        print("Monitoring camera...")
        while time.time() - start_time < 10:  # Monitor for 10 seconds
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            if len(faces) == 0:
                print("Warning: No face detected!")
            elif len(faces) > 1:
                print("Warning: Multiple faces detected!")
            else:
                face_detected = True
            
            cv2.imshow('Proctoring Camera', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return face_detected

    def proctor(self):
        camera_warning = self.monitor_camera()
        mic_warning = self.monitor_microphone()

        if mic_warning or not camera_warning:
            print("Proctoring Warning: Suspicious activity detected!")
        else:
            print("Proctoring passed: No suspicious activity detected.")


class SubjectiveTest:
    
    def __init__(self, filepath: str):
        self.question_pattern = [
            "Explain in detail ",
            "Define ",
            "Write a short note on ",
            "What do you mean by "
        ]

        self.grammar = r"""
            CHUNK: {<NN>+<IN|DT>*<NN>+}
            {<NN>+<IN|DT>*<NNP>+}
            {<NNP>+<NNS>*}
        """

        try:
            with open(filepath, mode="r") as fp:
                self.summary = fp.read()
        except FileNotFoundError:
            logging.exception("Corpus file not found.", exc_info=True)
            self.summary = ""

        # Initialize the proctoring system
        self.proctoring_system = ProctoringSystem()

    @staticmethod
    def word_tokenizer(sequence: str) -> list:
        word_tokens = []
        try:
            for sent in nlp.sent_tokenize(sequence):
                for w in nlp.word_tokenize(sent):
                    word_tokens.append(w)
        except Exception:
            logging.exception("Word tokenization failed.", exc_info=True)
        return word_tokens

    @staticmethod
    def create_vector(answer_tokens: list, tokens: list) -> np.array:
        return np.array([1 if tok in answer_tokens else 0 for tok in tokens])

    @staticmethod
    def cosine_similarity_score(vector1: np.array, vector2: np.array) -> float:
        def vector_value(vector):
            return np.sqrt(np.sum(np.square(vector)))

        v1 = vector_value(vector1)
        v2 = vector_value(vector2)

        if v1 == 0 or v2 == 0:
            logging.warning("One or both vectors are zero vectors. Returning 0 similarity.")
            return 0.0

        v1_v2 = np.dot(vector1, vector2)
        return (v1_v2 / (v1 * v2)) * 100

    def generate_test(self, num_questions: int = 5) -> Tuple[list, list]:
        if not self.summary:
            logging.error("No summary available to generate tests.")
            return [], []

        try:
            sentences = nlp.sent_tokenize(self.summary)
        except Exception:
            logging.exception("Sentence tokenization failed.", exc_info=True)
            return [], []

        try:
            cp = nlp.RegexpParser(self.grammar)
        except Exception:
            logging.exception("Regex grammar train failed.", exc_info=True)
            return [], []

        question_answer_dict = {}
        for sentence in sentences:
            try:
                tagged_words = nlp.pos_tag(nlp.word_tokenize(sentence))
            except Exception:
                logging.exception("Word tokenization failed.", exc_info=True)
                continue

            tree = cp.parse(tagged_words)
            for subtree in tree.subtrees():
                if subtree.label() == "CHUNK":
                    temp = " ".join([sub[0] for sub in subtree]).strip().upper()
                    if temp not in question_answer_dict:
                        if len(nlp.word_tokenize(sentence)) > 20:
                            question_answer_dict[temp] = sentence
                    else:
                        question_answer_dict[temp] += sentence

        keyword_list = list(question_answer_dict.keys())
        question_answer = []

        for _ in range(10):
            rand_num = np.random.randint(0, len(keyword_list))
            selected_key = keyword_list[rand_num]
            answer = question_answer_dict[selected_key]
            rand_num %= 4
            question = self.question_pattern[rand_num] + selected_key + "."
            question_answer.append({"Question": question, "Answer": answer})

        que, ans = [], []
        while len(que) < num_questions:
            rand_num = np.random.randint(0, len(question_answer))
            if question_answer[rand_num]["Question"] not in que:
                que.append(question_answer[rand_num]["Question"])
                ans.append(question_answer[rand_num]["Answer"])
            else:
                continue
        return que, ans

    def evaluate_subjective_answer(self, original_answer: str, user_answer: str) -> float:
        original_ans_list = self.word_tokenizer(original_answer)
        user_ans_list = self.word_tokenizer(user_answer)

        overall_list = original_ans_list + user_ans_list

        vector1 = self.create_vector(original_ans_list, overall_list)
        vector2 = self.create_vector(user_ans_list, overall_list)

        score_obt = self.cosine_similarity_score(vector1, vector2)
        return score_obt
    
    def start_proctoring(self):
        """Start the proctoring system during the test."""
        self.proctoring_system.proctor()

# Example usage
if __name__ == "__main__": 
    test = SubjectiveTest(filepath='path_to_summary.txt')
    
    # Start proctoring before or during the test
    test.start_proctoring()
    
    # Proceed with other testing logic
    questions, answers = test.generate_test()
    print(questions)
    print(answers)
