from flask import Flask, abort, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os
from werkzeug.utils import secure_filename
from collections import Counter
from nltk.corpus import stopwords, wordnet
from nltk.tokenize import word_tokenize
import pdfplumber
import language_tool_python
import textstat
from flask_cors import CORS, cross_origin


app = Flask(__name__)
CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:8gf5eXNZvJVNMkCvcXD6@localhost:3306/edutext'
db = SQLAlchemy(app)
ma = Marshmallow(app)


def analizador_de_texto(texto):
    stop_words = set(stopwords.words('spanish')) 
    palabras = word_tokenize(texto.lower())
    palabras = [palabra for palabra in palabras if palabra.isalnum() and palabra not in stop_words]
    frecuencia_de_palabras = Counter(palabras)
    return len(palabras), frecuencia_de_palabras

def encontrar_sinonimos(palabra):
    sinonimos = []
    for syn in wordnet.synsets(palabra):
        for lemma in syn.lemmas():
            sinonimos.append(lemma.name())
    return sinonimos

def resaltar_palabras(texto, palabras_resaltar):
    palabras = word_tokenize(texto)
    texto_resaltado = ""
    for palabra in palabras:
        if palabra.lower() in palabras_resaltar:
            texto_resaltado += palabra
        else:
            texto_resaltado += palabra
    return texto_resaltado

def calcular_calificacion(indice_flesch, cantidad_de_palabras, cantidad_errores):
    # Esta es solo una propuesta para calcular la calificación, puedes ajustar la fórmula según tus necesidades.
    calificacion = (indice_flesch / 100) * (1 - (cantidad_errores / cantidad_de_palabras))
    return round(calificacion * 100, 2)  # Devuelve la calificación como un porcentaje con dos decimales.

def generar_explicacion_calificacion(calificacion):
    if calificacion >= 80:
        return "El documento tiene un buen nivel de legibilidad y pocos errores gramaticales."
    elif calificacion >= 60:
        return "El documento tiene un nivel de legibilidad adecuado pero tiene varios errores gramaticales."
    else:
        return "El documento tiene un nivel de legibilidad bajo y muchos errores gramaticales."


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80))



class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80))

    def __init__(self, name, description):
        self.name = name
        self.description = description



class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    group = db.relationship('Group', backref=db.backref('students', lazy=True))


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)


class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80))
    grade = db.Column(db.Integer)


class CourseGroup(db.Model):
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), primary_key=True)
    course = db.relationship('Course', backref=db.backref('course_groups', lazy=True))
    group = db.relationship('Group', backref=db.backref('course_groups', lazy=True))


class TeacherCourse(db.Model):
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key=True)
    teacher = db.relationship('Teacher', backref=db.backref('teacher_courses', lazy=True))
    course = db.relationship('Course', backref=db.backref('teacher_courses', lazy=True))


class AssignmentStudent(db.Model):
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), primary_key=True)
    assignment = db.relationship('Assignment', backref=db.backref('assignment_students', lazy=True))
    student = db.relationship('Student', backref=db.backref('assignment_students', lazy=True))


# A continuación, vamos a definir los esquemas de Marshmallow para cada tabla:
class CourseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Course


class GroupSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Group


class StudentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Student


class TeacherSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Teacher


class AssignmentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Assignment


class CourseGroupSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CourseGroup


class TeacherCourseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TeacherCourse


class AssignmentStudentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AssignmentStudent
        
course_schema = CourseSchema()


@app.route('/analizar', methods=['POST'])
@cross_origin()  
def analizar():
    archivo = request.files['archivo']
    nombre_archivo = secure_filename(archivo.filename)
    archivo.save(nombre_archivo)
    texto = ""
    with pdfplumber.open(nombre_archivo) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text()

    cantidad_de_palabras, frecuencia_de_palabras = analizador_de_texto(texto)
    num_palabras_resaltar = 10
    texto_resaltado = resaltar_palabras(texto, [palabra for palabra, _ in frecuencia_de_palabras.most_common(num_palabras_resaltar)])

    resultado = []
    for palabra, frecuencia in frecuencia_de_palabras.most_common():
        sinonimos = encontrar_sinonimos(palabra)
        resultado.append({
            'palabra': palabra,
            'frecuencia': frecuencia,
            'sinonimos': sinonimos,
            'porcentaje': 100 * frecuencia / cantidad_de_palabras,
        })
    
    # Agregamos la detección de errores gramaticales
    tool = language_tool_python.LanguageTool('es')
    errores_gramaticales = tool.check(texto)

    # Agregamos el índice de legibilidad Flesch
    indice_flesch = textstat.flesch_reading_ease(texto)
    
    # Calculamos la calificación
    calificacion = calcular_calificacion(indice_flesch, cantidad_de_palabras, len(errores_gramaticales))
    
    # Generamos la explicación de la calificación
    explicacion_calificacion = generar_explicacion_calificacion(calificacion)
    
    resultado_json = {
        'cantidad_de_palabras': cantidad_de_palabras,
        'resultado': resultado,
        'texto_resaltado': texto_resaltado,
        'errores_gramaticales': len(errores_gramaticales),  # Supongamos que sólo quieres la cantidad de errores
        'indice_flesch': indice_flesch,
        'calificacion': calificacion,
        'explicacion_calificacion': explicacion_calificacion
    }
    # Devuelve el objeto como un JSON
    return jsonify(resultado_json)



@app.route("/course", methods=["POST"])
def add_course():
    name = request.json['name']
    description = request.json['description']
    new_course = Course(name=name, description=description)
    db.session.add(new_course)
    db.session.commit()
    return jsonify(course_schema.dump(new_course))


@app.route("/course", methods=["GET"])
def get_courses():
    all_courses = Course.query.all()
    return jsonify(course_schema.dump(all_courses))


@app.route("/course/<id>", methods=["GET"])
def get_course(id):
    course = Course.query.get(id)
    return jsonify(course_schema.dump(course))


@app.route("/course/<id>", methods=["PUT"])
def update_course(id):
    course = Course.query.get(id)
    name = request.json['name']
    description = request.json['description']
    course.name = name
    course.description = description
    db.session.commit()
    return jsonify(course_schema.dump(course))


@app.route("/course/<id>", methods=["DELETE"])
def delete_course(id):
    course = Course.query.get(id)
    db.session.delete(course)
    db.session.commit()
    return course_schema.jsonify(course)

# Endpoint para crear un nuevo grupo
@app.route('/grupo', methods=['POST'])
def add_grupo():
    name = request.json['name']
    description = request.json['description']
    new_grupo = Group(name, description)
    db.session.add(new_grupo)
    db.session.commit()
    return jsonify(GroupSchema().dump(new_grupo))


# Endpoint para mostrar todos los grupos
@app.route('/grupo', methods=['GET'])
def get_grupos():
    grupos = Group.query.all()
    return jsonify(GroupSchema(many=True).dump(grupos))



# Endpoint para mostrar un grupo por id
@app.route('/grupo/<id>', methods=['GET'])
def get_grupo(id):
    grupo = Group.query.get(id)
    return jsonify(GroupSchema().dump(grupo))


# Endpoint para actualizar un grupo
@app.route('/grupo/<id>', methods=['PUT'])
def update_grupo(id):
    grupo = Group.query.get(id)

    name = request.json['name']
    description = request.json['description']

    grupo.name = name
    grupo.description = description

    db.session.commit()

    return jsonify(GroupSchema.dump(grupo))


# Endpoint para eliminar un grupo
@app.route('/grupo/<id>', methods=['DELETE'])
def delete_grupo(id):
    grupo = Group.query.get(id)
    db.session.delete(grupo)
    db.session.commit()
    return jsonify(GroupSchema.dump(grupo))

@app.route('/assignments/', methods=['GET'])
def get_all_assignments():
    assignments = Assignment.query.all()
    assignments_schema = AssignmentSchema(many=True)
    return jsonify(assignments_schema.dump(assignments))


@app.route('/assignments/<int:id>', methods=['GET'])
def get_assignment(id):
    assignment = Assignment.query.get(id)
    if assignment is None:
        abort(404)
    return jsonify(AssignmentSchema.dump(assignment))

@app.route('/assignments/', methods=['POST'])
def create_assignment():
    assignment_data = request.get_json()
    new_assignment = Assignment(assignment_data)
    db.session.add(new_assignment)
    db.session.commit()
    return jsonify(AssignmentSchema.dump(new_assignment)), 201

@app.route('/assignments/<int:id>', methods=['PUT'])
def update_assignment(id):
    assignment_data = request.get_json()
    assignment = Assignment.query.get(id)
    if assignment is None:
        abort(404)
    for key, value in assignment_data.items():
        setattr(assignment, key, value)
    db.session.commit()
    return jsonify(AssignmentSchema.dump(assignment))

@app.route('/assignments/<int:id>', methods=['DELETE'])
def delete_assignment(id):
    assignment = Assignment.query.get(id)
    if assignment is None:
        abort(404)
    db.session.delete(assignment)
    db.session.commit()
    return '', 204

@app.route('/teachers/', methods=['POST'])
def create_teacher():
    data = request.get_json()
    new_teacher = Teacher(**data)
    db.session.add(new_teacher)
    db.session.commit()
    return jsonify(TeacherSchema.dump(new_teacher)), 201


@app.route('/teachers/', methods=['GET'])
def get_all_teachers():
    teachers = Teacher.query.all()
    return jsonify(TeacherSchema(many=True).dump(teachers))

@app.route('/teachers/<id>/', methods=['GET'])
def get_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    return TeacherSchema().dump(teacher)

@app.route('/teachers/<id>/', methods=['PUT', 'PATCH'])
def update_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        setattr(teacher, key, value)
    db.session.commit()
    return TeacherSchema().dump(teacher)

@app.route('/teachers/<id>/', methods=['DELETE'])
def delete_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    db.session.delete(teacher)
    db.session.commit()
    return '', 204




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
