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

    # Configuración mejorada de MongoDB con manejo de errores
    def get_mongo_client():
        try:
            username = quote_plus(os.getenv('MONGO_USER', 'Roberto'))
            password = quote_plus(os.getenv('MONGO_PASS', '12345'))
            MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.vkow89i.mongodb.net/conferencia_joven?retryWrites=true&w=majority&authSource=admin"
            
            client = MongoClient(
                MONGO_URI,
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=30000,
                retryWrites=True,
                retryReads=True
            )
            # Solo verificar conexión en desarrollo
            if os.getenv('FLASK_ENV') == 'development':
                client.admin.command('ping')
            return client
        except Exception as e:
            app.logger.error(f"Error de conexión a MongoDB: {str(e)}")
            return None

    # Conexión inicial (lazy loading)
    mongo_client = None
    feedback_collection = None

    def get_feedback_collection():
        nonlocal mongo_client, feedback_collection
        if not mongo_client:
            mongo_client = get_mongo_client()
        if mongo_client and not feedback_collection:
            feedback_collection = mongo_client["conferencia_joven"]["feedback"]
        return feedback_collection

    # Ruta para manejar el feedback
    @app.route('/submit-feedback', methods=['POST'])
    def submit_feedback():
        collection = get_feedback_collection()
        if not collection:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 503
            
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Datos no proporcionados'}), 400
                
            feedback_data = {
                'nombre': data.get('nombre', 'Anónimo'),
                'email': data.get('email', ''),
                'valoracion': int(data.get('valoracion', 3)),
                'mensaje': data.get('mensaje', ''),
                'fecha': datetime.utcnow()
            }
            
            result = collection.insert_one(feedback_data)
            return jsonify({
                'success': True,
                'message': 'Feedback guardado exitosamente',
                'id': str(result.inserted_id)
            }), 201
            
        except ValueError:
            return jsonify({'error': 'Valoración inválida'}), 400
        except Exception as e:
            app.logger.error(f"Error al guardar feedback: {str(e)}")
            return jsonify({'error': 'Error interno del servidor'}), 500

    # Rutas estáticas
    @app.route('/')
    def index():
        return render_template('index.html')

    # Sistema de rutas dinámicas
    topic_pages = {
        'buen-uso-de-las-redes-sociales': 'Uso de redes sociales.html',
        'relaciones-toxicas': 'Relaciones toxicas.html',
        # ... (todas tus otras rutas)
    }

    for route, template in topic_pages.items():
        @app.route(f'/{route}')
        def view(template=template):
            return render_template(template)

    # Panel de administración
    @app.route('/admin-comentarios')
    def admin_comentarios():
        collection = get_feedback_collection()
        if not collection:
            return "Error de conexión a la base de datos", 503
                
        try:
            page = int(request.args.get('page', 1))
            per_page = 10
            skip = (page-1)*per_page
            
            total = collection.count_documents({})
            comentarios = list(collection.find().sort('fecha', -1).skip(skip).limit(per_page))
            
            for comentario in comentarios:
                comentario['_id'] = str(comentario.get('_id', ''))
            
            return render_template(
                'admin comentarios.html',
                comentarios=comentarios,
                pagination={
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total // per_page) + (1 if total % per_page else 0)
                }
            )
        except Exception as e:
            app.logger.error(f"Error en admin: {str(e)}")
            return "Error interno del servidor", 500

    return app

# Creación de la aplicación (para wsgi.py)
application = create_app()

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
