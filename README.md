MCQ Generation Project:-
This project is a Multiple Choice Question (MCQ) Generator built using Flask and Natural Language Processing (NLP) techniques.
It allows users to input content either as text or PDF, and generates relevant MCQs as output, with the ability to download them as a PDF.


1)Project Overview:-
The MCQ Generation project enables users to generate multiple-choice questions from two types of inputs:
  Text Input: A user can enter a passage of text, and the application will generate MCQs based on the content.
  PDF Input: Users can upload a PDF file, and the application will extract the text to generate MCQs.

After the user inputs the content, they can click on Generate to receive the following outputs:
  Quiz Output: Displaying the generated questions on the webpage.
  PDF Output: Allowing users to download the generated questions as a PDF file.

2)Technologies Used:-
  Flask: A Python web framework to handle the server-side of the application.
  spaCy: An NLP library for processing and extracting relevant information from text.
  BERT: A pre-trained transformer model used for natural language understanding to generate MCQs.
  Python: The primary language for the backend logic.
  PDF Export: Conversion of MCQs into a downloadable PDF format.
  HTML/CSS: For structuring and styling the frontend of the web application.

3)Installation Instructions
1. Clone the Repository
bash
Copy
Edit
git clone https://github.com/your-username/mcq_generation.git
cd mcq_generation
2. Set up the Virtual Environment
Create and activate a virtual environment:

bash
Copy
Edit
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

3. Run the Flask Application
Start the Flask server:
  In terminal :- python app.py
This will run the server at http://127.0.0.1:5000/.

4) Open the web application in your browser at http://127.0.0.1:5000/.

You will see two options for user input:
  Text Input: Type or paste your text into the provided text box.
  PDF Input: Upload a PDF file.

After entering your content, click on Generate to receive the generated MCQs.
The application will display:
  Quiz Output: The MCQs will be displayed on the web page.
  PDF Output: You will be able to download the generated MCQs as a PDF.

5)Project Structure
Here's an overview of the project structure:

mcq_generation/
│
├── app.py                  # Main Python file for the backend logic
├── venv/                   # Virtual environment folder
│
├── static/                 # Folder for static files (CSS, JS, images)
├── templates/              # Folder for HTML files
│   ├── index.html          # Homepage with text and PDF input
│   ├── result.html         # Page to display generated MCQs (quiz output)
│   └── quiz.html           # Template for Quiz
└── .gitignore              # List of files and folders to ignore (e.g., venv/)
Explanation of Files
app.py: The main file where the Flask app is defined. It handles text and PDF input, generates MCQs, and renders HTML templates.
index.html: The homepage where users can provide text or PDF input.
result.html: Displays the result of a quiz.
quiz.html: Displays a generated mcqs in quiz format with the timer and next and previous options
.gitignore: Prevents certain files (like the virtual environment) from being pushed to GitHub.

Contributing:-
We welcome contributions! To help improve the project, follow these steps:
Fork the repository.
Create a new branch (git checkout -b feature-name).
Make your changes and commit them (git commit -am 'Add new feature').
Push to the branch (git push origin feature-name).

Open a Pull Request with a clear description of your changes.

