from fastapi import FastAPI, File, UploadFile
import shutil
import os
import pymupdf #If any ununderstandable error occoured, then replace "pymupdf" by "pymupdf" in all places.
from nbclient import NotebookClient
from nbformat import read,write
import json

app = FastAPI()

# Creating "ContextUploads" & "ExtractedText" & more.. named folders
upload_DIR = "ContextUploads"
storing_DIR = "ExtractedText"

# Ensuring the folders are made
os.makedirs(upload_DIR, exist_ok=True)
os.makedirs(storing_DIR, exist_ok=True)

# Post request
@app.post("/upload", summary="Upload a PDF and extract text", description="Uploads a PDF file, extracts text, and saves it as 'qns.txt'.")
async def uploadContext(file: UploadFile = File(...)): 
    """
    **Upload a PDF file.**
    - The file will be stored in `ContextUploads/`
    - The extracted text will be saved as `qns.txt` in `ExtractedText/`
    - Returns the paths of the uploaded PDF and extracted text file.
    """
    # Save the uploaded PDF
    file_path = os.path.join(upload_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text from the PDF
    text = extract_text_from_pdf(file_path)

    # Save the extracted text as "qns.txt"
    txt_filename = "qns.txt"
    txt_path = os.path.join(storing_DIR, txt_filename)

    with open(txt_path, "w", encoding="utf-8") as txt_file:
        txt_file.write(text)

    return {
        "original_pdf": file.filename,
        "pdf_path": file_path,
        "txt_path": txt_path
    }

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF file."""
    with pymupdf.open(pdf_path) as doc:
        text = ""
        for page in doc:
            text += page.get_text("text")  # Extract text from each page
    return text

@app.post("/studentUpload")
async def uploadAns(file: UploadFile = File(...)):
    file_path = os.path.join(upload_DIR, file.filename) # Constructs a filepath inside ContextUploads

    # Opening the file in binary write mode and sending to the server
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extracting text from PDF
    text = extract_text_from_pdf(file_path)

    # Storing as txt
    txt_filename = "ans.txt"
    txt_path = os.path.join(storing_DIR, txt_filename)

    with open(txt_path, "w", encoding="utf-8") as txt_file:
        txt_file.write(text)

    return {"filename": file.filename, "file_path": file_path, "txt_path": txt_path}

def delete_files():
    for folder in [upload_DIR, storing_DIR,OUTPUT_DIR]:
        if os.path.exists(folder):  # Check if folder exists
            for file_name in os.listdir(folder):  # List all files
                file_path = os.path.join(folder, file_name)
                try:
                    if os.path.isfile(file_path):  # Ensure it's a file
                        os.remove(file_path)  # Delete file
                        print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        else:
            print(f"Folder not found: {folder}")

book_path = os.path.join( "D:", "\LangChain", "hack_rag", "ans.ipynb")
OUTPUT_DIR = "Op"
OP_FILENAME = "op.txt"
OP_PATH = os.path.join(OUTPUT_DIR, OP_FILENAME)


@app.get("/getOp")

def run_notebook(notebook_path: str=book_path):
    """Executes a Jupyter Notebook and returns the classification output from op.txt."""
    try:
        # Read the notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = read(f, as_version=4)

        # Execute the notebook with a timeout of 600 seconds
        client = NotebookClient(nb, timeout=600)
        client.execute()
        

        # Save the executed notebook with output
        with open(notebook_path, "w", encoding="utf-8") as f:
            write(nb, f)

        # Check if op.txt file exists and read the output
        if os.path.exists(OP_PATH):
            with open(OP_PATH, "r", encoding="utf-8") as op_file:
                classification_output = op_file.read()  # Read raw text content
        else:
            classification_output = "No classification output found in op.txt"

        print("✅ Notebook executed successfully!")
        delete_files() 
        # Return the result from op.txt as raw text
        return {
            "message": "Notebook executed successfully!",
            "classification_output": classification_output
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            "message": "Error while executing notebook.",
            "error": str(e)
        }