import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from logging.handlers import RotatingFileHandler
from question_answer import get_qa_result

app = Flask(__name__)
CORS(app)

# Configuración de los logs
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

# Configurar el logger para almacenar logs en un archivo
file_handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)

@app.route('/question-answer', methods=["POST"])
def question_answer():
    try:
        app.logger.info('Se recibió una solicitud POST en /question-answer')
        question = request.json['question']
        app.logger.info('Pregunta recibida: %s', question)
        answer = get_qa_result(question)
        app.logger.info('Respuesta generada: %s', answer)
        return jsonify(answer=answer)
    except Exception as e:
        app.logger.error('Error HTTP: %s', str(e))
        return jsonify(error='Ocurrió un error en la solicitud'+str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0')
