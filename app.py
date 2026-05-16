import os
import uuid
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from parser import PDFProcessor
from ai_engine import ESGAIAgent

# .env faylını mütləq yükləyirik
load_dotenv()

# Qovluq yollarını dinamik təyin edirik
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Fayl həcmi limiti: 20MB
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

# Uploads qovluğunun mövcudluğuna əmin oluruq
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. Fayl yoxlanışı
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF is supported.'}), 400

    # 2. Təhlükəsiz yadda saxlama
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    try:
        file.save(file_path)

        # 3. PDF Parsing
        processor = PDFProcessor(file_path)
        document_text = processor.extract_text()

        if not document_text or document_text.startswith('Parsing Error:'):
            return jsonify({'status': 'error', 'error': 'Could not extract text from PDF. The file might be scanned, encrypted, or empty.'}), 400

        # 4. DeepSeek AI Analizi
        # Agent hər sorğuda yenidən yaradılır (API key-in təzə qalması üçün)
        ai_agent = ESGAIAgent()
        analysis_result = ai_agent.analyze_document_text(document_text)

        if isinstance(analysis_result, str) and analysis_result.startswith('DeepSeek Analysis Error:'):
            return jsonify({'status': 'error', 'error': analysis_result}), 502

        # 5. Uğurlu Nəticə
        return jsonify({
            'status': 'success', 
            'analysis': analysis_result,
            'filename': filename
        })

    except Exception as exc:
        # Xəta mesajını konsola çap edirik (debugging üçün)
        print(f"🔥 Server Error: {exc}")
        return jsonify({'status': 'error', 'error': str(exc)}), 500

    finally:
        # Faylı analizdən dərhal sonra silirik (Server dolmasın)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"⚠️ Could not delete temp file: {e}")

if __name__ == '__main__':
    # .env-dən gələn debug və port tənzimləmələri
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in {'1', 'true'}
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)