



from flask import Flask, render_template, request, session, redirect, url_for, send_file
from flask_bootstrap import Bootstrap
import spacy
from transformers import BertTokenizer, BertForMaskedLM
import torch
from collections import Counter
import random
from io import BytesIO
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from spacy.lang.en.stop_words import STOP_WORDS

# Initialize Flask app and configure it
app = Flask(__name__, template_folder="templates")
app.secret_key = "secret"
Bootstrap(app)

# Load spaCy and BERT models
nlp = spacy.load("en_core_web_sm")
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertForMaskedLM.from_pretrained("bert-base-uncased")



# def process_pdf(file):
#     """
#     Extracts text from a PDF file.
    
#     Args:
#         file: The uploaded PDF file.

#     Returns:
#         The extracted text as a string.
#     """
#     # text = ""
#     # pdf_reader = PdfReader(file)
#     # for page in pdf_reader.pages:
#     #     text += page.extract_text() + "\n"
#     # return text
#     text = ""
#     pdf_reader = PdfReader(file)
#     for page in pdf_reader.pages:
#         text += page.extract_text() + "\n"
#     return text
import pytesseract
from PIL import Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_path

def process_pdf(file):
    """
    Extracts text from a PDF file.
    
    Args:
        file: The uploaded PDF file.

    Returns:
        The extracted text as a string.
    """
    text = ""
    pdf_reader = PdfReader(file)
    

    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    

    if not text.strip():
        try:
            
            images = convert_from_path(file)
            for image in images:
                
                text += pytesseract.image_to_string(image) + "\n"
        except Exception as e:
            print(f"Error during OCR: {e}")
    
    return text.strip()

def get_important_sentences(doc, num_questions):
    context_dependent_starters = [
        "in", "from", "however", "although", "but", "as", "because", 
        "while", "since", "when", "if", "though", "therefore", 
        "thus", "moreover", "furthermore", "besides", "on", "due to"
    ]
    
    def is_good_sentence(sent):
        words = sent.text.strip().split()
        if len(words) <= 6:
            return False
        first_word = words[0].lower()
        if first_word in context_dependent_starters:
            return False
        has_entity = any(ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EVENT", "WORK_OF_ART"] for ent in sent.ents)
        has_nouns_or_verbs = any(token.pos_ in ["NOUN", "PROPN", "VERB"] for token in sent)
        return has_entity or has_nouns_or_verbs

    filtered_sents = [sent for sent in doc.sents if is_good_sentence(sent)]
    return random.sample(filtered_sents, min(num_questions, len(filtered_sents)))

# Function to generate distractors using BERT
def generate_distractors_with_bert(correct_answer, context_text, num_distractors=3):
    try:
        
        masked_text = str(context_text).replace(correct_answer, "[MASK]")  
        
        
        inputs = tokenizer(masked_text, return_tensors="pt")
        outputs = model(**inputs)
        predictions = torch.topk(
            outputs.logits[0][inputs["input_ids"][0] == tokenizer.mask_token_id],
            num_distractors + 10  # Generate more predictions for filtering
        ).indices

        distractors = []
        for predicted_index in predictions[0]:
            predicted_word = tokenizer.decode([predicted_index]).strip()
            if (
                predicted_word.lower() != correct_answer.lower()
                and predicted_word not in distractors
                and predicted_word.isalpha()
                and predicted_word not in STOP_WORDS
            ):
                distractors.append(predicted_word)
            if len(distractors) == num_distractors:
                break
        return distractors if distractors else ["Option 1", "Option 2", "Option 3"]
    except Exception as e:
        print(f"Error in generating distractors: {e}")
        return ["Option 1", "Option 2", "Option 3"]  # Fallback distractors

# Function to generate MCQs
def generate_mcqs(text, num_questions=5):
    if not text.strip():
        print("No valid input text provided!")
        return []

    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents if len(sent.text.strip()) > 0]
    if not sentences:
        print("No sentences were extracted from the input text!")
        return []

    num_questions = min(num_questions, len(sentences))
    selected_sentences = get_important_sentences(doc, num_questions)


    mcqs = []
    for sentence in selected_sentences:
        sent_doc = nlp(str(sentence))
        stop_words = {"is", "am", "are", "was", "were", "be", "being", "been", "it"}
        nouns = [token.text for token in sent_doc if token.pos_ in {"NOUN", "PROPN"} and token.text.lower() not in stop_words]
        if len(nouns) < 1:
            continue

        subject = Counter(nouns).most_common(1)[0][0]
        question_stem = str(sentence).replace(subject, "______")
        distractors = generate_distractors_with_bert(subject, sentence)
        answer_choices = [subject] + distractors
        random.shuffle(answer_choices)
        # correct_answer = chr(64 + answer_choices.index(subject) + 1)  # A, B, C, etc.
        correct_answer = subject
        mcqs.append((question_stem, answer_choices, correct_answer))

    return mcqs

# Function to process PDF files
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = ""

        # Check if files were uploaded
        # if "files[]" in request.files and request.files["files[]"].filename != "":
        #     files = request.files.getlist("files[]")
        #     for file in files:
        #         if file.filename.endswith(".pdf"):
        #             text = process_pdf(file)  # Process PDF file
        #         elif file.filename.endswith(".txt"):
        #             text += file.read().decode("utf-8")  # Process text file
         # Check if a file is uploaded
        if "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            if file.filename.endswith(".pdf"):
                text = process_pdf(file)  # Extract text from PDF
                if not text.strip():  # If no text was extracted, show an error
                    return "Error: No text extracted from the PDF.", 400
            else:
                return "Error: Please upload a valid PDF file.", 400
        else:
            text = request.form.get("text", "").strip()  # Get text input from form
        # Process manual text input if no files are uploaded
        # if not text.strip():
        #     text = request.form.get("text", "").strip()
        
        # Validate input text
        if not text:
            return "Please enter valid text or upload a valid file."

        # Get the selected number of questions and mode
        num_questions = int(request.form.get("num_questions", 5))
        mode = request.form.get("mode", "quiz")  # Default to quiz mode

        # Generate MCQs
        mcqs = generate_mcqs(text, num_questions=num_questions)
        if not mcqs:
            return "No MCQs could be generated. Please provide a richer text input."

        session["mcqs"] = mcqs  # Store MCQs in session for reuse

        if mode == "pdf":
            return redirect(url_for("download_pdf"))
        elif mode == "quiz":
            session["current_question"] = 0  # Initialize the quiz with the first question
            return redirect(url_for("quiz"))

    return render_template("index.html")





@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    mcqs = session.get("mcqs", [])
    current_question = session.get("current_question", 0)

    # Redirect to home if no MCQs are generated
    if not mcqs:
        return redirect(url_for("index"))
     # Ensure user_answers is properly initialized
    user_answers = session.get("user_answers", [None] * len(mcqs))
    if len(user_answers) != len(mcqs):
        user_answers = [None] * len(mcqs)
        session["user_answers"] = user_answers

    if request.method == "POST":
        # Handle navigation between questions
        answer = request.form.get("answer")


        # Save the user's answer for the current question
        if answer is not None:
            user_answers[current_question] = answer
            session["user_answers"] = user_answers

        if "next" in request.form:
            session["current_question"] = min(current_question + 1, len(mcqs) - 1)
        elif "previous" in request.form:
            session["current_question"] = max(current_question - 1, 0)
        elif "submit" in request.form:
            return redirect(url_for("result"))

        return redirect(url_for("quiz"))

     # Ensure the current question index is valid
    if current_question < 0 or current_question >= len(mcqs):
        return redirect(url_for("index"))
    # Render the quiz template with the current question
    return render_template(
        "quiz.html",
        question=mcqs[current_question][0],  # Pass the question text
        choices=mcqs[current_question][1],  # Pass the answer choices
        current_question=current_question + 1,  # Adjust for 1-based indexing
        total_questions=len(mcqs),
        user_answer=session.get("user_answers", [None] * len(mcqs))[current_question], 
        enumerate=enumerate # Pre-fill selected answer if any
    )

@app.route("/result")
def result():
    if "user_answers" not in session or "mcqs" not in session:
        return redirect(url_for("index"))  # Redirect to home if the quiz session is missing

    mcqs = session["mcqs"]
    user_answers = session.get("user_answers", [None] * len(mcqs))

    # Calculate results
    correct = 0
    incorrect = 0
    unattempted = 0

    for i, answer in enumerate(user_answers):
        if answer is None:
            unattempted += 1
        elif answer == mcqs[i][2]:

            correct += 1
        else:
            incorrect += 1

    total_score = correct
    total_questions = len(mcqs)

    # Pass results to the template
    return render_template(
        "result.html",
        total_score=total_score,
        total_questions=total_questions,
        correct=correct,
        incorrect=incorrect,
        unattempted=unattempted,
    )

# Route: Generate and download PDF


from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit



@app.route("/download_pdf")
def download_pdf():
    mcqs = session.get("mcqs", [])
    if not mcqs:
        return "No MCQs available to generate PDF. Please ensure you upload valid text or files."

    # Create a PDF buffer
    pdf_buffer = BytesIO()
    pdf_canvas = canvas.Canvas(pdf_buffer, pagesize=letter)
    pdf_canvas.setFont("Helvetica", 12)

    # Page and text settings
    page_width, page_height = letter
    left_margin = 50
    right_margin = 50
    line_height = 20
    y_position = page_height - 50  # Starting Y position (top margin)

    # Maximum width for text
    max_width = page_width - left_margin - right_margin

    # Loop through MCQs and write them to the PDF
    for i, mcq in enumerate(mcqs, 1):
        question_stem, answer_choices, _ = mcq

        # Split and wrap the question stem to fit within the page width
        wrapped_question = simpleSplit(question_stem, "Helvetica", 12, max_width)
        pdf_canvas.drawString(left_margin, y_position, f"Q{i}: {wrapped_question[0]}")  # Print the first line with Q1:
        y_position -= line_height

        # Print subsequent lines of the wrapped question without Q1:
        for line in wrapped_question[1:]:
            pdf_canvas.drawString(left_margin + 20, y_position, line)  # Indent subsequent lines
            y_position -= line_height

        y_position -= 10  # Extra space between question and options

        # Loop through answer choices and wrap them if necessary
        for j, choice in enumerate(answer_choices, 1):
            wrapped_choice = simpleSplit(f"{chr(64 + j)}. {choice}", "Helvetica", 12, max_width)
            for line in wrapped_choice:
                pdf_canvas.drawString(left_margin + 20, y_position, line)  # Indent options
                y_position -= line_height

        y_position -= 20  # Extra space after each question

        # Check if the Y position is too low for more text; if so, create a new page
        if y_position < 50:  # Bottom margin
            pdf_canvas.showPage()
            pdf_canvas.setFont("Helvetica", 12)  # Reset font for the new page
            y_position = page_height - 50  # Reset Y position for the new page

    # Save the PDF and return it
    pdf_canvas.save()
    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="mcqs.pdf",
        mimetype="application/pdf",
    )

# Main function
if __name__ == "__main__":
    app.run(debug=True)