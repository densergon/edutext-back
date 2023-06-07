-- Tabla para almacenar los cursos
CREATE TABLE courses (
  id INTEGER PRIMARY KEY,
  name TEXT(80) NOT NULL,
  description TEXT(80)
);

-- Tabla para almacenar los grupos
CREATE TABLE grupos (
  id INTEGER PRIMARY KEY,
  name TEXT(80) NOT NULL,
  description TEXT(80)
);

-- Tabla para almacenar los estudiantes
CREATE TABLE students (
  id INTEGER PRIMARY KEY,
  name TEXT(80) NOT NULL,
  group_id INTEGER,
  FOREIGN KEY (group_id) REFERENCES grupos(id)
);

-- Tabla para almacenar los profesores
CREATE TABLE teachers (
  id INTEGER PRIMARY KEY,
  name TEXT(80) NOT NULL
);

-- Tabla para almacenar las asignaciones
CREATE TABLE assignments (
  id INTEGER PRIMARY KEY,
  course_id INTEGER,
  teacher_id INTEGER,
  name TEXT(80) NOT NULL,
  description TEXT(80),
  grade INTEGER,
  FOREIGN KEY (course_id) REFERENCES courses(id),
  FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);

-- Tabla de asociación entre cursos y grupos (relación muchos a muchos)
CREATE TABLE course_group (
  course_id INTEGER,
  group_id INTEGER,
  PRIMARY KEY (course_id, group_id),
  FOREIGN KEY (course_id) REFERENCES courses(id),
  FOREIGN KEY (group_id) REFERENCES grupos(id)
);

-- Tabla de asociación entre profesores y cursos (relación muchos a muchos)
CREATE TABLE teacher_course (
  teacher_id INTEGER,
  course_id INTEGER,
  PRIMARY KEY (teacher_id, course_id),
  FOREIGN KEY (teacher_id) REFERENCES teachers(id),
  FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- Tabla de asociación entre asignaciones y estudiantes (relación uno a muchos)
CREATE TABLE assignment_student (
  assignment_id INTEGER,
  student_id INTEGER,
  PRIMARY KEY (assignment_id, student_id),
  FOREIGN KEY (assignment_id) REFERENCES assignments(id),
  FOREIGN KEY (student_id) REFERENCES students(id)
);
