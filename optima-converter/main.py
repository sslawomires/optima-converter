from flask import Flask, request, send_file, render_template, redirect, url_for, flash
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'tajny_klucz'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def convert_xlsx_to_ini(xlsx_file_path, ini_path):
    df = pd.read_excel(xlsx_file_path)

    with open(ini_path, 'w', encoding='cp1250', newline='\r\n') as ini:
        for _, row in df.iterrows():
            ini.write(f"[{row['Numer FV']}]\r\n")
            ini.write("TYP=Dokument księgowy\r\n")
            ini.write(f"NUMER={row['Numer FV']}\r\n")
            ini.write(f"DATA={row['Data']}\r\n")
            ini.write(f"KONTRAHENT={row['Kontrahent']}\r\n")
            ini.write(f"NIP={row['NIP']}\r\n")
            ini.write(f"NETTO={row['Netto']}\r\n")
            ini.write(f"VAT={row['VAT']}\r\n")
            ini.write(f"BRUTTO={row['Brutto']}\r\n\r\n")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash("Nie załączono pliku", "error")
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash("Nie wybrano pliku", "error")
        return redirect(url_for('index'))

    try:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        ini_filename = os.path.splitext(file.filename)[0] + '.ini'
        ini_path = os.path.join(UPLOAD_FOLDER, ini_filename)

        convert_xlsx_to_ini(filepath, ini_path)

        return redirect(url_for('success', filename=ini_filename))
    except Exception as e:
        flash(f"Błąd konwersji: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/success/<filename>')
def success(filename):
    return render_template('success.html', filename=filename)

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        flash("Plik nie istnieje", "error")
        return redirect(url_for('index'))

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
