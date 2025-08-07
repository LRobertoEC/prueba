from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import quote_plus
import os

def create_app():
    # Cargar variables de entorno
    load_dotenv()

    app = Flask(__name__)

    # Configuración de MongoDB
    username = quote_plus(os.getenv('MONGO_USER', 'Roberto'))
    password = quote_plus(os.getenv('MONGO_PASS', '12345'))
    MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.vkow89i.mongodb.net/conferencia_joven?retryWrites=true&w=majority&authSource=admin"
    DB_NAME = "conferencia_joven"

    # Conexión a MongoDB
    try:
        client = MongoClient(
            MONGO_URI,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        db = client[DB_NAME]
        feedback_collection = db['feedback']
        print("✅ Conexión exitosa a MongoDB Atlas")
    except Exception as e:
        print(f"❌ Error de conexión a MongoDB: {str(e)}")
        feedback_collection = None

    # Ruta para manejar el feedback
    @app.route('/submit-feedback', methods=['POST'])
    def submit_feedback():
        if feedback_collection is None:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
            
        try:
            data = request.get_json()
            
            feedback_data = {
                'nombre': data['nombre'],
                'email': data['email'],
                'valoracion': int(data['valoracion']),
                'mensaje': data['mensaje'],
                'fecha': datetime.now()
            }
            
            result = feedback_collection.insert_one(feedback_data)
            return jsonify({'success': True, 'message': 'Feedback guardado exitosamente'}), 200
                
        except Exception as e:
            print(f"Error al guardar feedback: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # Ruta principal
    @app.route('/')
    def index():
        return render_template('index.html')

    # Rutas para páginas temáticas
    @app.route('/buen-uso-de-las-redes-sociales')
    def redes_sociales():
        return render_template('Uso de redes sociales.html')

    @app.route('/relaciones-toxicas')
    def relaciones_toxicas():
        return render_template('Relaciones toxicas.html')

    @app.route('/efecto-de-las-redes-sociales-en-mi-autoestima')
    def redes_sociales_autoestima():
        return render_template('Efecto de las redes sociales en mi autoestima.html')

    @app.route('/amor-propio')
    def amor_propio():
        return render_template('Amor propio.html')

    @app.route('/rompiendo-cadenas')
    def rompiendo_cadenas():
        return render_template('Rompiendo cadenas.html')

    @app.route('/violencia-digital-y-ley-olimpia')
    def violencia_digital():
        return render_template('Violencia digital y Ley Olimpia.html')

    @app.route('/resiliencia-tu-fuerza-interior')
    def resiliencia():
        return render_template('Resilencia.html')

    @app.route('/feminismo-la-lucha-por-la-igualdad')
    def feminismo():
        return render_template('Feminismo.html')

    @app.route('/cero-violencia-escolar')
    def cero_violencia_escolar():
        return render_template('Cero violencia escolar.html')

    @app.route('/educacion-ambiental')
    def educacion_ambiental():
        return render_template('Educación ambiental.html')

    @app.route('/fortalecimiento-y-empoderamiento-juvenil')
    def empoderamiento_juvenil():
        return render_template('Fortalecimiento y empoderamiento juvenil.html')

    @app.route('/comer-para-vivir')
    def alimentacion_saludable():
        return render_template('Comer para vivir.html')

    # Panel de administración
    @app.route('/admin-comentarios')
    def admin_comentarios():
        if feedback_collection is None:
            return "Error de conexión a la base de datos", 500
            
        try:
            comentarios = list(feedback_collection.find().sort('fecha', -1))
            
            for comentario in comentarios:
                comentario['_id'] = str(comentario['_id'])
            
            distribucion_estrellas = [0, 0, 0, 0, 0]
            total_comentarios = len(comentarios)
            suma_valoraciones = sum(c['valoracion'] for c in comentarios if 1 <= c['valoracion'] <= 5)
            
            for comentario in comentarios:
                valoracion = comentario['valoracion']
                if 1 <= valoracion <= 5:
                    distribucion_estrellas[valoracion-1] += 1
            
            promedio_general = round(suma_valoraciones / total_comentarios, 1) if total_comentarios > 0 else 0
            
            return render_template(
                'admin comentarios.html',
                comentarios=comentarios,
                distribucion_estrellas=distribucion_estrellas,
                promedio_general=promedio_general,
                total_comentarios=total_comentarios
            )
                                
        except Exception as e:
            print(f"Error inesperado: {e}")
            return f"Error inesperado: {str(e)}", 500

    return app

# Crear la aplicación
app = create_app()

# Configuración para ejecución local
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)