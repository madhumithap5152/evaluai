import unittest
import tkinter as tk
from tkinter import ttk, messagebox
from src.tests.test_subjective import TestSubjective
import io
import sys

class TestRunnerWithGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Test Runner")
        self.geometry("600x400")
        self.configure(bg='white')

        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(self, text="Test Results", font=("Helvetica", 16), bg='white')
        self.label.pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("Test", "Result", "Details"), show="headings")
        self.tree.heading("Test", text="Test")
        self.tree.heading("Result", text="Result")
        self.tree.heading("Details", text="Details")
        self.tree.column("Details", width=300)
        self.tree.pack(pady=20, fill=tk.BOTH, expand=True)

        self.run_button = tk.Button(self, text="Run Tests", command=self.run_tests)
        self.run_button.pack(pady=10)

    def run_tests(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(TestSubjective)
        result = unittest.TestResult()

        # Redirect stdout to capture the test details
        buffer = io.StringIO()
        sys.stdout = buffer

        suite.run(result)

        sys.stdout = sys.__stdout__

        output = buffer.getvalue()

        test_names = [str(test) for test in suite]
        results = []

        # Handling the cases for errors and failures
        for test, traceback in result.errors:
            test_name = str(test)
            details = f"Error: {traceback}"
            results.append((test_name, "Error", details))
        
        for test, traceback in result.failures:
            test_name = str(test)
            details = f"Failure: {traceback}"
            results.append((test_name, "Fail", details))

        # Handling successful tests
        for test_name in test_names:
            if test_name not in [x[0] for x in results]:
                lines = output.splitlines()
                detail_lines = [line for line in lines if test_name.split()[0] in line]
                details = "\n".join(detail_lines)
                results.append((test_name, "Pass", details))

        # Displaying results in the Treeview
        for result_item in results:
            self.tree.insert("", "end", values=result_item)

        messagebox.showinfo("Test Run", f"Ran {result.testsRun} tests with {len(result.failures)} failures and {len(result.errors)} errors.")

if __name__ == "__main__":
    app = TestRunnerWithGUI()
    app.mainloop()
