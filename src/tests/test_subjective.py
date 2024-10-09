import unittest
import numpy as np
from unittest.mock import patch, mock_open
from src.subjective import SubjectiveTest

class TestSubjective(unittest.TestCase):

    def setUp(self):
        print("\nSetting up test environment...")
        # Mock file content
        self.mock_file_data = "This is a mock corpus text."
        self.patcher = patch("builtins.open", mock_open(read_data=self.mock_file_data))
        self.mock_open = self.patcher.start()
        self.test_obj = SubjectiveTest("test_corpus.txt")

    def tearDown(self):
        print("Tearing down test environment...\n")
        self.patcher.stop()

    def test_create_vector(self):
        print("Running test_create_vector...")
        tokens = ["this", "is", "a", "test"]
        answer_tokens = ["this", "is", "a", "different", "test"]
        expected_vector = np.array([1, 1, 1, 1])
        result_vector = self.test_obj.create_vector(answer_tokens, tokens)
        print(f"Expected vector: {expected_vector}")
        print(f"Result vector: {result_vector}")
        np.testing.assert_array_equal(result_vector, expected_vector, 
            err_msg="Vector creation failed: Expected {}, got {}".format(expected_vector, result_vector))

    def test_cosine_similarity_score(self):
        print("Running test_cosine_similarity_score...")
        # Test with orthogonal vectors
        v1 = np.array([1, 0, 0])
        v2 = np.array([0, 1, 0])
        score = self.test_obj.cosine_similarity_score(v1, v2)
        print(f"Score for orthogonal vectors (expected 0.0): {score}")
        self.assertAlmostEqual(score, 0.0, msg="Expected 0% similarity for orthogonal vectors, got {}".format(score))

        # Test with identical vectors
        v3 = np.array([1, 1, 0])
        score_identical = self.test_obj.cosine_similarity_score(v3, v3)
        print(f"Score for identical vectors (expected 100.0): {score_identical}")
        self.assertAlmostEqual(score_identical, 100.0, msg="Expected 100% similarity for identical vectors, got {}".format(score_identical))

        # Test with vectors having a small angle
        v4 = np.array([1, 1])
        v5 = np.array([1, 0.9])
        score_small_angle = self.test_obj.cosine_similarity_score(v4, v5)
        print(f"Score for vectors with a small angle (expected > 90): {score_small_angle}")
        self.assertGreater(score_small_angle, 90, msg="Expected similarity > 90% for small angle vectors, got {}".format(score_small_angle))

    def test_evaluate_subjective_answer(self):
        print("Running test_evaluate_subjective_answer...")

        def simple_tokenizer(text):
            return text.lower().split()

        self.test_obj.word_tokenizer = simple_tokenizer

        original_answer = (
            "The core components of a DBMS include the Database Engine, the Database Schema, "
            "the Query Processor, and the Transaction Manager. The Database Engine is responsible "
            "for storing, retrieving, and updating data. It is the heart of the DBMS where the actual "
            "data resides. The Database Schema defines the structure of the data within the database, "
            "outlining how data is organized, including tables, fields, relationships, and constraints. "
            "The Query Processor interprets and executes database queries, allowing users to interact "
            "with the database using SQL or other query languages. Lastly, the Transaction Manager ensures "
            "that all database transactions are processed reliably by maintaining the ACID properties, "
            "which stand for Atomicity, Consistency, Isolation, and Durability."
        )

        user_answer = (
            "DBMS components include the Database Engine, Schema, Query Processor, and Transaction Manager. "
            "The Database Engine stores and retrieves data. The Schema defines the database structure. The Query "
            "Processor handles SQL queries, and the Transaction Manager ensures transactions are reliable."
        )

        score = self.test_obj.evaluate_subjective_answer(original_answer, user_answer)
        print(f"Evaluation score: {score}%")
        self.assertGreaterEqual(score, 50, msg="Expected score >= 50%, got {}".format(score))

if __name__ == '__main__':
    unittest.main(verbosity=2)
