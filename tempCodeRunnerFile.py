from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_bootstrap import Bootstrap
import torch
from transformers import BertTokenizer, BertForMaskedLM
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
import random
from io import BytesIO

app = Flask(__name__)
app.secret_key = "secret"
Bootstrap(app)

# Load BERT model and tokenizer
model_name = "bert-base-uncased"
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertForMaskedLM.from_pretrained(model_name)

def generate_mcqs(text, num_questions=5):
    sentences = text.split(". ")  # Simple sentence split
    num_questions = min(num_questions, len(sentences))
    selected_sentences = random.sample(sentences, num_questions)
    mcqs = []
    
    for sentence in selected_sentences:
        words = sentence.split()
        if len(words) < 3:
            continue
        masked_index = random.randint(0, len(words) - 1)
        original_word = words[masked_index]
        words[masked_index] = "[MASK]"
        masked_sentence = " ".join(words)

        inputs = tokenizer(masked_sentence, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        predictions = torch.topk(outputs.logits[0, masked_index], 4).indices
        answer_choices = [original_word] + [tokenizer.decode([pred.item()]) for pred in predictions]
        random.shuffle(answer_choices)
        correct_answer = chr(65 + answer_choices.index(original_word))  # A, B, C, D
        
        mcqs.append((masked_sentence.replace("[MASK]", "____"), answer_choices, correct_answer))
    
    return mcqs

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = ""
        if "file" in request.files:
            file = request.files["file"]
            if file.filename.endswith(".pdf"):
                text = process_pdf(file)
            else:
                text = file.read().decode("utf-8")
        else:
            text = request.form["text"]

        num_questions = int(request.form["num_questions"])
        session["mcqs"] = generate_mcqs(text, num_questions)
        session["quiz_mode"] = request.form["mode"]
        
        if session["quiz_mode"] == "only_mcqs":
            return redirect(url_for("download_pdf"))
        else:
            return redirect(url_for("quiz"))
    
    return render_template("index.html")

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "mcqs" not in session:
        return redirect(url_for("index"))
    
    if request.method == "POST":
        user_answers = request.form.getlist("answer")
        score = sum(1 for i, ans in enumerate(user_answers) if ans == session["mcqs"][i][2])
        session["score"] = score
        return redirect(url_for("result"))
    
    return render_template("quiz.html", mcqs=session["mcqs"])

@app.route("/result")
def result():
    return render_template("result.html", score=session.get("score", 0))

@app.route("/download_pdf")
def download_pdf():
    mcqs = session.get("mcqs", [])
    pdf_buffer = BytesIO()
    pdf_writer = PdfWriter()
    for i, (question, choices, _) in enumerate(mcqs, 1):
        page = f"Q{i}: {question}\n"
        for j, choice in enumerate(choices, 1):
            page += f"{chr(64+j)}. {choice}\n"
        pdf_writer.add_blank_page(width=500, height=800)
    pdf_writer.write(pdf_buffer)
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, as_attachment=True, download_name="mcqs.pdf")

def process_pdf(file):
    text = ""
    pdf_reader = PdfReader(file)
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

if __name__ == "__main__":
    app.run(debug=True)