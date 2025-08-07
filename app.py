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
                socketTimeoutMS=30000,  # Aumentado para operaciones
                retryWrites=True,
                retryReads=True
            )
            client.admin.command('ping')  # Test de conexión
            return client
        except Exception as e:
            app.logger.error(f"Error de conexión a MongoDB: {str(e)}")
            return None

    # Conexión inicial
    mongo_client = get_mongo_client()
    feedback_collection = mongo_client["conferencia_joven"]["feedback"] if mongo_client else None

    # Ruta para manejar el feedback
    @app.route('/submit-feedback', methods=['POST'])
    def submit_feedback():
        nonlocal feedback_collection
        if not feedback_collection:
            feedback_collection = get_mongo_client()["conferencia_joven"]["feedback"] if get_mongo_client() else None
            if not feedback_collection:
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
                'fecha': datetime.utcnow()  # Usamos UTC para consistencia
            }
            
            result = feedback_collection.insert_one(feedback_data)
            return jsonify({
                'success': True,
                'message': 'Feedback guardado exitosamente',
                'id': str(result.inserted_id)
            }), 201
            
        except ValueError as e:
            return jsonify({'error': 'Valoración inválida'}), 400
        except Exception as e:
            app.logger.error(f"Error al guardar feedback: {str(e)}")
            return jsonify({'error': 'Error interno del servidor'}), 500

    # Rutas estáticas mejoradas con manejo de caché
    @app.route('/')
    def index():
        return render_template('index.html'), 200, {
            'Cache-Control': 'public, max-age=300'
        }

    # Sistema de rutas dinámicas para páginas temáticas
    topic_pages = {
        'buen-uso-de-las-redes-sociales': 'Uso de redes sociales.html',
        'relaciones-toxicas': 'Relaciones toxicas.html',
        'efecto-de-las-redes-sociales-en-mi-autoestima': 'Efecto de las redes sociales en mi autoestima.html',
        'amor-propio': 'Amor propio.html',
        'rompiendo-cadenas': 'Rompiendo cadenas.html',
        'violencia-digital-y-ley-olimpia': 'Violencia digital y Ley Olimpia.html',
        'resiliencia-tu-fuerza-interior': 'Resilencia.html',
        'feminismo-la-lucha-por-la-igualdad': 'Feminismo.html',
        'cero-violencia-escolar': 'Cero violencia escolar.html',
        'educacion-ambiental': 'Educación ambiental.html',
        'fortalecimiento-y-empoderamiento-juvenil': 'Fortalecimiento y empoderamiento juvenil.html',
        'comer-para-vivir': 'Comer para vivir.html'
    }

    for route, template in topic_pages.items():
        @app.route(f'/{route}')
        def view(template=template):  # Capturamos el template en el closure
            return render_template(template), 200, {
                'Cache-Control': 'public, max-age=3600'
            }

    # Panel de administración con paginación
    @app.route('/admin-comentarios')
    def admin_comentarios():
        nonlocal feedback_collection
        if not feedback_collection:
            feedback_collection = get_mongo_client()["conferencia_joven"]["feedback"] if get_mongo_client() else None
            if not feedback_collection:
                return "Error de conexión a la base de datos", 503
                
        try:
            page = int(request.args.get('page', 1))
            per_page = 10
            
            # Consulta con paginación
            total = feedback_collection.count_documents({})
            comentarios = list(feedback_collection.find()
                             .sort('fecha', -1)
                             .skip((page-1)*per_page)
                             .limit(per_page))
            
            # Procesamiento seguro de datos
            comentarios_serializados = []
            for comentario in comentarios:
                comentario['_id'] = str(comentario.get('_id', ''))
                comentarios_serializados.append(comentario)
            
            # Estadísticas con agregación de MongoDB
            pipeline = [
                {'$group': {
                    '_id': None,
                    'total': {'$sum': 1},
                    'avg_rating': {'$avg': '$valoracion'},
                    'rating_dist': {
                        '$push': {
                            'rating': '$valoracion'
                        }
                    }
                }}
            ]
            stats = next(feedback_collection.aggregate(pipeline), {})
            
            return render_template(
                'admin comentarios.html',
                comentarios=comentarios_serializados,
                distribucion_estrellas=get_rating_distribution(stats.get('rating_dist', [])),
                promedio_general=round(stats.get('avg_rating', 0), 1),
                total_comentarios=stats.get('total', 0),
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

    def get_rating_distribution(ratings):
        dist = [0, 0, 0, 0, 0]
        for r in ratings:
            rating = r.get('rating', 0)
            if 1 <= rating <= 5:
                dist[rating-1] += 1
        return dist

    return app

# Configuración para producción
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
