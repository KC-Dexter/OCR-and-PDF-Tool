import os
from flask import Flask,render_template,request,flash,send_file,make_response,redirect,url_for
from werkzeug.utils import secure_filename
from ocr_ import *
from pdf2docx import parse
from typing import Tuple
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
from io import BytesIO
import io
from fpdf import FPDF

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


app = Flask(__name__,template_folder='Template')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/team')
def team():
    return render_template('team.html')    
@app.route('/pdfff')
def pdfff():
    return render_template('pdfff.html') 
@app.route('/ocr_text', methods=['GET'])
def ocr_text():
    return render_template('ocr_text.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            print("h1")
            return render_template('upload.html')
        file = request.files['file']
    
        if file.filename == '':
            flash('No selected file')
            print("h2")
            return render_template('upload.html')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            answer1,answer2,answer3 = ocr_driver(filename)
            print(answer3)
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return render_template('result.html',answer1=answer1,answer2=answer2,answer3=answer3)
        else:
            flash('Incorrect image format.....SUPPORTED FORMATS = {png, jpg, jpeg}')
            return render_template('upload.html')
    else:
        return render_template('upload.html')
    return 

@app.route('/ocr_text', methods=['GET', 'POST'])
def generate_pdf():
    if request.method == 'POST':
        text = request.form.get('text')
        # Create the PDF object
        pdf = FPDF()
        # Add a page to the PDF
        pdf.add_page()
        # Set font and font size
        pdf.set_font("Arial", size=12)
        # Write the text to the PDF
        cell_width = 190
        cell_height = 10
        # Write the text to the PDF
        pdf.multi_cell(cell_width, cell_height, txt=text, align='L')
        # Save the PDF to a byte string
        buffer = pdf.output(dest='S').encode('latin-1')
        # File name for the PDF.
        file_name = "generated.pdf"
        # Create a response object.
        response = make_response(buffer)
        # Set the response MIME type to PDF.
        response.headers['Content-Type'] = 'application/pdf'
        # Set the filename in the Content-Disposition header.
        response.headers['Content-Disposition'] = f'attachment; filename={file_name}'
        return response
        
    return render_template('ocr_text.html')

@app.route('/merge')
def merge():
    return render_template('merge.html')

@app.route('/merge', methods=['GET', 'POST'])
def merge_pdf():
    if request.method == 'POST':
        pdf_files = request.files.getlist('pdf_files')
        merger = PdfFileMerger()
        for file in pdf_files:
            merger.append(file)
        output = BytesIO()
        merger.write(output)
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers.set('Content-Disposition', 'attachment', filename='merged.pdf')
        response.headers.set('Content-Type', 'application/pdf')
        return response
    else:
        return render_template('merge.html')
    

@app.route('/convert',methods=['GET','POST'])
def index():
    if request.method=="POST":
        def convert_pdf2docx(input_file:str,output_file:str,pages:Tuple=None):
           if pages:
               pages = [int(i) for i in list(pages) if i.isnumeric()]

           res = parse(pdf_file=input_file,docx_with_path=output_file, pages=pages)
           summary = {
               "File": input_file, "Pages": str(pages), "Output File": output_file
            }

           print("\n".join("{}:{}".format(i, j) for i, j in summary.items()))
           return res
        file=request.files['filename']
        if file.filename!='':
           filename = secure_filename(file.filename)
           file.save(file.filename)
           input_file=file.filename
           output_file=r"hello.docx"
           convert_pdf2docx(input_file,output_file)
           doc=input_file.split(".")[0]+".docx"
           print(doc)
           lis=doc.replace(" ","=")
           return render_template("docc.html",variable=lis)
    return render_template("convert.html")


@app.route('/docc',methods=['GET','POST'])
def docx():
    if request.method=="POST":
        lis=request.form.get('filename',None)
        lis=lis.replace("="," ")
        return send_file(lis,as_attachment=True)
    return  render_template("convert.html")


@app.route('/page_dele', methods=['GET', 'POST'])
def delete_page():
    if request.method == 'POST':
        # get the uploaded file
        file = request.files['file']
        pdf_reader = PdfFileReader(io.BytesIO(file.read()))
        pdf_writer = PdfFileWriter()
        numbers = request.form['pages']
        pages_to_remove = [int(num) for num in numbers.split(',')]
        for page_num in range(pdf_reader.getNumPages()):
            if page_num not in pages_to_remove:
                pdf_writer.addPage(pdf_reader.getPage(page_num))
        output = io.BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=Modified(Page Removed).pdf'
        response.headers['Content-Type'] = 'application/pdf'
        return response
    return render_template('page_dele.html')



@app.route('/reorder', methods=['GET', 'POST'])
def reorder_pdf():
    if request.method == 'POST':
        # Get the selected page numbers from the form
        selected_pages = request.form.get('pages').split(',')

        # Get the uploaded PDF file
        pdf_file = request.files['pdf']
        pdf_data = pdf_file.read()

        # Load the PDF file
        pdf = PdfFileReader(io.BytesIO(pdf_data))

        # Create a new PDF writer
        output_pdf = PdfFileWriter()

        # Reorder the selected pages
        for page_number in selected_pages:
            # Convert page_number to int and subtract 1 to match PDF page indices (starting from 0)
            page_index = int(page_number) - 1

            # Add the selected page to the new PDF writer
            output_pdf.addPage(pdf.getPage(page_index))

        # Add the remaining pages to the new PDF writer
        for page_index in range(pdf.getNumPages()):
            if str(page_index + 1) not in selected_pages:
                output_pdf.addPage(pdf.getPage(page_index))

        # Save the reordered PDF to a new in-memory file
        output_file = io.BytesIO()
        output_pdf.write(output_file)
        output_file.seek(0)
        # Provide the reordered PDF for download
        response = make_response(output_file.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=Reordered.pdf'
        response.headers['Content-Type'] = 'application/pdf'
        return response
    return render_template('reorder.html')







# @app.route('/reorder', methods=['GET', 'POST'])
# def reorder_pdf():
#     if request.method == 'POST':
#         pdf_file = request.files['file']
#         pdf_reader = PdfFileReader(pdf_file)
        
#         pdf_writer = PdfFileWriter()
        
#         numbers = request.form['page_order[]']
#         page_order = [int(num) for num in numbers.split(',')]
#         for page_num in page_order:
#             page = pdf_reader.getPage(page_num)
#             pdf_writer.addPage(page)
    #     output_file = BytesIO()
    #     pdf_writer.write(output_file)
    #     output_file.seek(0)
        # response = make_response(output_file.getvalue())
        # response.headers['Content-Disposition'] = f'attachment; filename=Reordered.pdf'
        # response.headers['Content-Type'] = 'application/pdf'
        # return response
    # return render_template('reorder.html')











if __name__ == '__main__':
    app.debug=True
    app.run()


# 1, 0, 2, 3, 5, 4, 6, 7, 8, 9, 10, 11, 12, 13