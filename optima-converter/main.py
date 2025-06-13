from flask import Flask, request, send_file, render_template, redirect, url_for, flash
import xml.etree.ElementTree as ET
import io
import os

app = Flask(__name__)
app.secret_key = 'zmien_tajny_klucz_na_inny'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def convert_optima_xml_to_ini(xml_content, ini_path):
    root = ET.fromstring(xml_content)

    with open(ini_path, 'w', encoding='cp1250', newline='\r\n') as ini:
        for faktura in root.findall('.//Faktura'):
            nr = faktura.findtext('Numer') or 'BRAK_NUMERU'
            data = faktura.findtext('DataWystawienia') or ''
            kontr = faktura.findtext('Kontrahent/Nazwa') or 'BRAK_KONTRAHENTA'
            net = faktura.findtext('Podsumowanie/Netto') or '0'
            vat = faktura.findtext('Podsumowanie/Vat') or '0'

            ini.write(f'[{nr}]\r\n')
            ini.write('TYP=Dokument księgowy\r\n')
            ini.write(f'NUMER DOKUMENTU={nr}\r\n')
            ini.write(f'DATA={data}\r\n')
            ini.write(f'KONTRAHENT={kontr}\r\n')
            ini.write(f'NETTO-23={net}\r\n')
            ini.write(f'VAT-23={vat}\r\n\r\n')

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
        xml_bytes = file.read()
        ini_filename = os.path.splitext(file.filename)[0] + '.ini'
        ini_path = os.path.join(UPLOAD_FOLDER, ini_filename)

        convert_optima_xml_to_ini(xml_bytes, ini_path)

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
    app.run(host='0.0.0.0', port=8080)
