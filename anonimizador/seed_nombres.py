"""Datos semilla para la base de nombres falsos.

Mezcla de herencia mexicana, inglesa, germánica, francesa y libanesa para
realismo. Los nombres de empresas y escuelas son inventados/chuscos.
"""

# (nombre, genero)  genero: 'H' hombre, 'M' mujer
FIRST_NAMES = [
    ("Juan", "H"), ("Carlos", "H"), ("Miguel", "H"), ("José", "H"),
    ("Luis", "H"), ("Jorge", "H"), ("Roberto", "H"), ("Fernando", "H"),
    ("Ricardo", "H"), ("Eduardo", "H"), ("Alejandro", "H"), ("Antonio", "H"),
    ("Francisco", "H"), ("Sergio", "H"), ("Raúl", "H"), ("Arturo", "H"),
    ("Guillermo", "H"), ("Héctor", "H"), ("Emilio", "H"), ("Mateo", "H"),
    ("William", "H"), ("Henry", "H"), ("Klaus", "H"), ("Pierre", "H"),
    ("Karim", "H"), ("Nabil", "H"), ("Andreas", "H"), ("Maximilian", "H"),
    ("Bruno", "H"), ("Iván", "H"),
    ("María", "M"), ("Guadalupe", "M"), ("Ana", "M"), ("Patricia", "M"),
    ("Laura", "M"), ("Verónica", "M"), ("Rosa", "M"), ("Gabriela", "M"),
    ("Adriana", "M"), ("Claudia", "M"), ("Mónica", "M"), ("Alejandra", "M"),
    ("Fernanda", "M"), ("Daniela", "M"), ("Sofía", "M"), ("Valeria", "M"),
    ("Regina", "M"), ("Ximena", "M"), ("Elena", "M"), ("Carmen", "M"),
    ("Emily", "M"), ("Charlotte", "M"), ("Greta", "M"), ("Brigitte", "M"),
    ("Amira", "M"), ("Yasmin", "M"), ("Ingrid", "M"), ("Helene", "M"),
    ("Renata", "M"), ("Camila", "M"),
]

LAST_NAMES = [
    # Mexicanos / hispanos comunes
    "García", "Hernández", "López", "Martínez", "González", "Rodríguez",
    "Pérez", "Sánchez", "Ramírez", "Cruz", "Flores", "Gómez", "Morales",
    "Vázquez", "Jiménez", "Reyes", "Torres", "Domínguez", "Aguilar",
    "Mendoza", "Ortiz", "Castillo", "Romero", "Álvarez", "Ruiz", "Guzmán",
    "Núñez", "Cervantes", "Buendía", "Salazar",
    # Ingleses
    "Smith", "Johnson", "Williams", "Brown", "Taylor", "Anderson", "Clark",
    "Wright", "Parker",
    # Germánicos
    "Müller", "Schmidt", "Weber", "Fischer", "Wagner", "Becker", "Hoffmann",
    "Bauer",
    # Franceses
    "Dubois", "Lefebvre", "Moreau", "Laurent", "Girard", "Rousseau",
    # Libaneses
    "Hayek", "Nader", "Saba", "Hanna", "Khalil", "Aboumrad", "Tannous",
    "Karam", "Sleiman",
]

# Bases chuscas para razón social (se les añade un régimen de capital).
COMPANY_BASES = [
    "Sal Si Puedes", "Tacos El Mareado", "Tornillos Que Vuelan",
    "El Buen Fin del Mundo", "Refacciones Don Nadie", "Aguas con el Perro",
    "La Vaca Voladora", "Pollos Sin Frontera", "Café Punto y Coma",
    "Maderas El Astillado", "Plomería Gota a Gota", "Zapatos del Olvido",
    "Pinturas Mil Colores", "Hielo Seco y Húmedo", "Carnitas El Tragón",
    "Llantas Que Ruedan", "Vidrios Transparentes", "Cemento Más Duro",
    "Dulces El Empacho", "Lácteos La Becerra", "Ferretería El Martillazo",
    "Cómputo Pantalla Azul", "Logística El Caracol", "Textiles Mil Hilos",
    "Bebidas El Resacón", "Muebles Se Mueve", "Jardines El Pasto Seco",
    "Panadería El Bolillo Duro", "Electrónica Chispa Loca",
    "Construcciones El Derrumbe",
]

# Régimen de capital con su peso relativo (más S.A. de C.V. por realismo).
REGIMENES = [
    ("S.A. de C.V.", 50),
    ("S. de R.L. de C.V.", 20),
    ("S.C.", 10),
    ("S.A.", 8),
    ("A.C.", 5),
    ("S.A.P.I. de C.V.", 4),
    ("S.A.B. de C.V.", 3),
]

# Escuelas chuscas/genéricas para IEDU.
SCHOOLS = [
    "Colegio El Coscorrón", "Instituto Cero Faltas", "Escuela La Regla y el Compás",
    "Centro Educativo El Recreo Eterno", "Colegio Sir Isaac Despistado",
    "Instituto Las Tres Erres", "Escuela Activa El Pupitre",
    "Colegio Bilingüe Ni Modo", "Academia El Diez de Panzazo",
    "Instituto Tecnológico La Goma de Borrar", "Colegio Marie Cúrate",
    "Escuela Primaria El Timbre", "Liceo Franco-Tamal",
    "Colegio Alemán Sin Acento", "Universidad del Conocimiento Difuso",
]
