import re
from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash, jsonify
import random
import math
import pandas as pd
import mysql.connector
from fpdf import FPDF
import os
import heapq
from collections import Counter
from itertools import combinations


app = Flask(__name__)
app.secret_key = "schimba_cheia_secreta"

def get_mysql_connection():
    return mysql.connector.connect(
        host="yamabiko.proxy.rlwy.net",
        port=20612,
        user="root",
        password="jxuLIryhRMBdojRyAiMMnuUateyxwJnz",
        database="liceu_orar"
    )



    

def rearrange_subjects(subjects):
    """
    Rearanjează lista de subiecte astfel încât să se reducă duplicatele consecutive.
    Dacă nu se poate rearanja, returnează None.
    """
    counts = Counter(subjects)
    heap = [(-cnt, random.random(), subj) for subj, cnt in counts.items()]
    heapq.heapify(heap)
    result = []
    prev_item = None
    while heap:
        count, rnd, subj = heapq.heappop(heap)
        result.append(subj)
        count += 1  # deoarece count este negativ
        if prev_item is not None:
            heapq.heappush(heap, prev_item)
            prev_item = None
        if count < 0:
            prev_item = (count, random.random(), subj)
    for i in range(1, len(result)):
        if result[i] == result[i-1]:
            print(f"[EȘEC] Alocare imposibilă pentru {clasa} în ziua {ziua} cu subiectele: {subject_list}")

            return None
    return result



def validate_timetable(assigned_days):
    # Verifică dacă fiecare zi are între 5 și 6 ore
    for i, day in enumerate(assigned_days):
        if len(day) < 5 or len(day) > 6:
            print(f"[ERROR] Ziua {i+1} are un număr invalid de ore ({len(day)})")
            return False
    return True






from collections import Counter
import random

def assign_subjects_to_days_variable(subjects, lessons_per_day, cls):
    """
    Atribuie materiile la zilele corespunzătoare, respectând condiția de 5-6 lecții pe zi.
    """
    days = len(lessons_per_day)
    counts = Counter(subjects)
    subjects_unique = list(counts.keys())

    # Verificăm dacă vreo materie are prea multe ore pentru distribuție uniformă (maxim 2 ore/zi)
    for subj, cnt in counts.items():
        if cnt > 2 * days:
            raise ValueError(f"Materia '{subj}' are prea multe ore ({cnt}) pentru a putea fi repartizată uniform pe {days} zile.")

    # Inițializăm zilele cu liste goale
    assigned_days = [[] for _ in range(days)]

    # Distribuim materiile, începând cu cele cu cele mai multe ore
    subjects_sorted = sorted(subjects_unique, key=lambda s: -counts[s])

    day_index = 0
    for subj in subjects_sorted:
        ore_ramase = counts[subj]
        while ore_ramase > 0:
            attempts = 0
            while (assigned_days[day_index].count(subj) >= 2) and attempts < days:
                day_index = (day_index + 1) % days
                attempts += 1

            if attempts >= days:
                random.shuffle(assigned_days)
                day_index = 0
                continue

            assigned_days[day_index].append(subj)
            ore_ramase -= 1
            day_index = (day_index + 1) % days

    # Ajustări finale pentru a respecta exact numărul de lecții pe zi
    for idx, day in enumerate(assigned_days):
        while len(day) < lessons_per_day[idx]:
            for other_idx, other_day in enumerate(assigned_days):
                if len(other_day) > lessons_per_day[other_idx]:
                    for subj in other_day:
                        if day.count(subj) < 2:
                            other_day.remove(subj)
                            day.append(subj)
                            break
                    if len(day) == lessons_per_day[idx]:
                        break

    # Shuffle final pentru diversitate
    for day in assigned_days:
        random.shuffle(day)

    # Verificăm dacă distribuția orelor este validă (5-6 ore pe zi)
    for i, day in enumerate(assigned_days):
        if len(day) < 5 or len(day) > 6:
            print(f"[ERROR] Ziua {i + 1} are un număr invalid de lecții ({len(day)})!")
            raise ValueError(f"Ziua {i + 1} din clasa {cls} are un număr invalid de lecții: {len(day)}")

    return assigned_days





def apply_subclass_modifications(cls, dist):
    """
    Modifică distribuția orelor în funcție de sufixul clasei:
      - Pentru clasele cu 'A': Chimie = 3, Fizică = 3, Informatică = 2, Biologie = 2.
      - Pentru clasele cu 'B': Geografie = 3, Istorie = 3, Psihologie = 3, Română = 2.
    """
    if cls.endswith('A'):
        dist["Chimie"] = 3
        dist["Fizică"] = 3
        dist["Informatică"] = 2
        dist["Biologie"] = 2
    elif cls.endswith('B'):
        dist["Geografie"] = 3
        dist["Istorie"] = 3
        dist["Psihologie"] = 3
        dist["Română"] = 2
    return dist

def init_db():
    conn = get_mysql_connection()
    c = conn.cursor()

    
    c.execute("DROP TABLE IF EXISTS timetable")
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS classes")
    c.execute("DROP TABLE IF EXISTS teachers")
    c.execute("DROP TABLE IF EXISTS rooms")
    c.execute("DROP TABLE IF EXISTS overrides")
    

    # Tabelul users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(100) PRIMARY KEY,
            password VARCHAR(100),
            role VARCHAR(50),
            student_class VARCHAR(50)
        )
    ''')




 
    # Inserare utilizatori test
    users = [
        ('admin', 'admin', 'admin'), ('director1', 'parola', 'director'),
        ('elev9a', 'parola', 'student'), ('elev9b', 'parola', 'student'),
        ('elev10a', 'parola', 'student'), ('elev10b', 'parola', 'student'),
        ('elev11a', 'parola', 'student'), ('elev11b', 'parola', 'student'),
        ('elev12a', 'parola', 'student'), ('elev12b', 'parola', 'student'),
        ('Ionescu', 'parola', 'profesor'), ('Matei', 'parola', 'profesor'),
        ('Ciocan', 'parola', 'profesor'), ('Marin', 'parola', 'profesor'),
        ('Georgescu', 'parola', 'profesor'), ('Stanciu', 'parola', 'profesor'),
        ('Tudor', 'parola', 'profesor'), ('Petrescu', 'parola', 'profesor'),
        ('Vasilescu', 'parola', 'profesor'), ('RaduI', 'parola', 'profesor'),
        ('Ciobanu', 'parola', 'profesor'), ('MarinB', 'parola', 'profesor'),
        ('Iacob', 'parola', 'profesor'), ('Voinea', 'parola', 'profesor'),
        ('Nedelcu', 'parola', 'profesor'), ('Marcu', 'parola', 'profesor'),
        ('Stoian', 'parola', 'profesor'), ('Patriciu', 'parola', 'profesor'),
        ('Cozma', 'parola', 'profesor'), ('Cârstea', 'parola', 'profesor'),
        ('Ardeleanu', 'parola', 'profesor'), ('Bărbuceanu', 'parola', 'profesor'),
        ('Enache', 'parola', 'profesor'), ('PopaR', 'parola', 'profesor'),
        ('Apostol', 'parola', 'profesor'), ('Dima', 'parola', 'profesor'),
        ('Alexandru', 'parola', 'profesor'), ('MateiescuT', 'parola', 'profesor'),
        ('GeorgescuP', 'parola', 'profesor')
    ]
    for username, password, role in users:
        if role == "student":
            cls = username.replace("elev", "").upper()  # ex: elev9a → 9A
            c.execute("""
                INSERT IGNORE INTO users (username, password, role, student_class)
                VALUES (%s, %s, %s, %s)
            """, (username, password, role, cls))
        else:
            c.execute("""
                INSERT IGNORE INTO users (username, password, role)
                VALUES (%s, %s, %s)
            """, (username, password, role))

    # Tabel timetable
    c.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INT AUTO_INCREMENT PRIMARY KEY,
            day VARCHAR(20),
            hour INT,
            class VARCHAR(50),
            subject VARCHAR(100),
            teacher VARCHAR(100),
            room VARCHAR(100)
        )
    ''')

    # Tabel classes
    c.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            name VARCHAR(50) PRIMARY KEY
        )
    ''')

    # Tabel teachers
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            name VARCHAR(100) PRIMARY KEY,
            subject VARCHAR(100)
        )
    ''')

    # Tabel rooms
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            name VARCHAR(100) PRIMARY KEY,
            type VARCHAR(50)
        )
    ''')

    # Tabel overrides
    c.execute('''
        CREATE TABLE IF NOT EXISTS overrides (
            id INT AUTO_INCREMENT PRIMARY KEY,
            class VARCHAR(50),
            day VARCHAR(20),
            hour INT,
            new_subject VARCHAR(100),
            new_teacher VARCHAR(100),
            new_room VARCHAR(100),
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(class, day, hour)
        )
    ''')

    # Inserare clase
    # Clasele
    classes = ['9A', '9B', '10A', '10B', '11A', '11B', '12A', '12B']
    for cls in classes:
        c.execute("INSERT IGNORE INTO classes (name) VALUES (%s)", (cls,))


    # Inserare profesori
    teachers = [
        ('Ionescu', 'Matematică'), ('Matei', 'Matematică'), ('Ciocan', 'Matematică'),
        ('Marin', 'Română'), ('Georgescu', 'Română'), ('Stanciu', 'Română'),
        ('Tudor', 'Engleză'), ('Petrescu', 'Engleză'), ('Vasilescu', 'Fizică'),
        ('RaduI', 'Informatică'), ('Ciobanu', 'Biologie'), ('MarinB', 'Biologie'),
        ('Iacob', 'Chimie'), ('Voinea', 'Istorie'), ('Nedelcu', 'Istorie'),
        ('Marcu', 'Geografie'), ('Stoian', 'Psihologie'), ('Patriciu', 'Psihologie'),
        ('Cozma', 'Sport'), ('Cârstea', 'Muzică'), ('Ardeleanu', 'Muzică'),
        ('Bărbuceanu', 'Arte Plastice'), ('Enache', 'Arte Plastice'),
        ('PopaR', 'Religie'), ('Apostol', 'Religie'), ('Dima', 'Desen'),
        ('Alexandru', 'Filosofie'), ('MateiescuT', 'Limba Franceză'),
        ('GeorgescuP', 'Psihologie')
    ]
    for teacher, subj in teachers:
        c.execute("INSERT IGNORE INTO teachers (name, subject) VALUES (%s, %s)", (teacher, subj))

    # Inserare săli
    rooms = [
        ('Sala 1', 'obișnuită'), ('Sala 2', 'obișnuită'), ('Sala 3', 'obișnuită'),
        ('Lab IT', 'laborator'), ('Lab Chimie', 'laborator'),
        ('Sala Sport', 'sport'), ('Sala de Muzică', 'specială'), ('Sala de Arte Plastice', 'specială')
    ]
    for room, rtype in rooms:
        c.execute("INSERT IGNORE INTO rooms (name, type) VALUES (%s, %s)", (room, rtype))

    conn.commit()
    conn.close()







def generate_timetable():
    import mysql.connector
    import random
    from collections import Counter, defaultdict

    def distribute_between_5_and_6_per_day(total):
        """
        Distribuie orele pe zile astfel încât fiecare zi să aibă între 5 și 6 ore, 
        dar fără ca vreo zi să aibă mai puțin de 5 ore.
        """
        if total < 25 or total > 30:
            raise Exception(f"Totalul de ore ({total}) nu se încadrează între 25 și 30.")
        
        # Inițial, alocăm 5 ore pentru fiecare zi
        lessons = [5] * 5  
        leftover = total - 25  # orele rămase pentru a ajunge la totalul dorit

        idx = random.randint(0, 4)  # Alegem aleator punctul de start

        while leftover > 0:
            if lessons[idx] < 6:  # Dacă ziua are mai puțin de 6 ore, mai adăugăm o oră
                lessons[idx] += 1
                leftover -= 1
            idx = (idx + 1) % 5  # Mergem la următoarea zi

        # Verificăm dacă fiecare zi are între 5 și 6 ore
        if any(ore < 5 or ore > 6 for ore in lessons):
            raise Exception(f"Distribuția orelor nu este validă: {lessons}")

        return lessons

    def split_subjects_into_days(subject_counts, lessons_per_day):
        """
        Distribuie materiile în zilele săptămânii fără repetări în aceeași zi.
        Utilizează un algoritm de backtracking pentru a găsi o soluție validă.
        """
        days = [[] for _ in range(5)]
        day_capacities = lessons_per_day.copy()
        
        # Sortăm materiile după numărul de ore (descrescător)
        subjects_by_count = sorted(subject_counts.items(), key=lambda x: x[1], reverse=True)
        
        def can_place(subject, day_idx):
            """Verifică dacă o materie poate fi plasată într-o zi"""
            return subject not in days[day_idx] and len(days[day_idx]) < day_capacities[day_idx]
        
        def backtrack(subject_idx=0, remaining=None):
            """Algoritm de backtracking pentru a distribui materiile"""
            if remaining is None:
                # Inițializăm numărul rămas de ore pentru fiecare materie
                remaining = {subject: count for subject, count in subjects_by_count}
            
            # Verificăm dacă am terminat de plasat toate materiile
            if all(count == 0 for count in remaining.values()):
                return True
            
            # Dacă nu mai avem materii, am terminat
            if subject_idx >= len(subjects_by_count):
                return False
            
            current_subject, _ = subjects_by_count[subject_idx]
            
            # Dacă această materie a fost deja complet distribuită, trecem la următoarea
            if remaining[current_subject] == 0:
                return backtrack(subject_idx + 1, remaining)
            
            # Încercăm să plasăm materia în fiecare zi
            possible_days = list(range(5))
            random.shuffle(possible_days)  # Amestecăm zilele pentru varietate
            
            for day_idx in possible_days:
                if can_place(current_subject, day_idx):
                    # Plasăm materia în această zi
                    days[day_idx].append(current_subject)
                    remaining[current_subject] -= 1
                    
                    # Continuăm recursiv cu distribuția
                    if backtrack(subject_idx, remaining):
                        return True
                    
                    # Dacă nu am găsit o soluție, facem backtracking
                    days[day_idx].remove(current_subject)
                    remaining[current_subject] += 1
            
            return False
        
        # Verificăm dacă putem distribui toate materiile
        success = backtrack()
        
        if not success:
            return None
        
        # Adăugăm materii "dummy" pentru a atinge numărul exact de ore pe zi
        for day_idx, day in enumerate(days):
            while len(day) < day_capacities[day_idx]:
                # Adăugăm o materie care apare în alte zile pentru a completa orarul
                for subject, count in subject_counts.items():
                    if subject not in day and count > 0:
                        day.append(subject)
                        break
        
        # Verificăm dacă fiecare zi are numărul corect de ore
        for day_idx, day in enumerate(days):
            if len(day) != day_capacities[day_idx]:
                return None
        
        return days

    def assign_subjects_to_days_variable(subjects, lessons_per_day, cls):
        """
        Distribuie materiile în zilele săptămânii conform numărului de ore pentru fiecare zi.
        Garantează că nu există materii repetate în aceeași zi.
        """
        if len(subjects) != sum(lessons_per_day):
            print(f"Eroare: Numărul total de materii ({len(subjects)}) nu se potrivește cu suma orelor pe zi ({sum(lessons_per_day)})")
            return None
        
        # Numărăm câte ore are fiecare materie
        subject_counts = Counter(subjects)
        
        # Verificăm dacă există materii cu mai mult de 5 ore (imposibil de distribuit fără repetare)
        problematic_subjects = [subj for subj, count in subject_counts.items() if count > 5]
        if problematic_subjects:
            print(f"Avertisment pentru {cls}: Următoarele materii au mai mult de 5 ore, ceea ce face imposibilă distribuția fără repetare: {problematic_subjects}")
            
            # Redistribuim orele pentru materiile problematice
            new_subjects = []
            for subj in subjects:
                if subj in problematic_subjects:
                    # Generăm un nume de materie modificat pentru a evita repetarea
                    # De exemplu: "Matematică" devine "Matematică (grup 1)", "Matematică (grup 2)", etc.
                    group_id = sum(1 for s in new_subjects if s.startswith(subj))
                    new_subj = f"{subj} (grup {group_id + 1})"
                    new_subjects.append(new_subj)
                else:
                    new_subjects.append(subj)
            
            # Actualizăm lista de materii și recalculăm distribuția
            subjects = new_subjects
            subject_counts = Counter(subjects)
        
        # Încercăm să distribuim materiile fără repetare
        max_attempts = 50
        for attempt in range(max_attempts):
            days = split_subjects_into_days(subject_counts, lessons_per_day)
            if days:
                # Succesul distribuției
                for day in days:
                    random.shuffle(day)  # Amestecăm ordinea materiilor în fiecare zi
                return days
        
        # Dacă nu am reușit după mai multe încercări, revenim la distribuția simplă
        print(f"Nu s-a putut găsi o distribuție validă pentru {cls} după {max_attempts} încercări.")
        day_assignments = []
        start_idx = 0
        
        for day_lessons in lessons_per_day:
            end_idx = start_idx + day_lessons
            day_subjects = subjects[start_idx:end_idx]
            day_assignments.append(day_subjects)
            start_idx = end_idx
            
        return day_assignments

    def normalize_day_slots(assignment):
        """
        Mută toate orele unei zile pe sloturi consecutive începând de la ora 1.
        Găurile sunt eliminate (orele sunt rearanjate).
        """
        items = list(assignment.items())
        items.sort()  # asigură ordinea inițială

        new_assignment = {}
        for new_slot, (_, value) in enumerate(items, start=1):
            new_assignment[new_slot] = value

        return new_assignment

    def rearrange_subjects(subjects):
        counts = Counter(subjects)
        result = []
        for subj, cnt in counts.items():
            result.extend([subj] * cnt)
        random.shuffle(result)
        return result

    def choose_room(subj):
        """ Alegerea camerei în funcție de subiect """
        # Eliminăm partea cu "(grup X)" din numele materiei pentru a alege camera corectă
        base_subject = subj.split(" (grup")[0]
        
        if base_subject in ["Informatică", "TIC"]:
            return "Lab IT"
        elif base_subject == "Chimie":
            return "Lab Chimie"
        elif base_subject == "Sport":
            return "Sala Sport"
        elif base_subject == "Muzică":
            return "Sala de Muzică"
        elif base_subject in ["Desen", "Arte Plastice"]:
            return "Sala de Arte Plastice"
        else:
            return "Sala obișnuită"

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="create_mysql_schema"
        )
        c = conn.cursor()
        c.execute("DELETE FROM timetable")
        c.execute("SELECT MAX(id) FROM timetable")
        result = c.fetchone()
        current_id = result[0] if result and result[0] is not None else 0

        days = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri']
        max_slots = 7
        teacher_schedule = {(day, slot): set() for day in days for slot in range(1, max_slots + 1)}
        
        # Counter pentru numărul de ore alocate fiecărui profesor
        teacher_hours = defaultdict(int)

        c.execute("SELECT name FROM classes")
        class_list = [row[0] for row in c.fetchall()]

        subject_distribution = {
            9: {"Română": 4, "Matematică": 5, "Engleză": 2, "Istorie": 3, "Religie": 1, "Biologie": 3,
                "Fizică": 2, "Chimie": 2, "Geografie": 2, "Informatică": 2, "Sport": 2, "Desen": 1, "Limba Franceză": 1},
            10: {"Română": 3, "Matematică": 5, "Engleză": 2, "Istorie": 3, "Religie": 1, "Biologie": 3,
                "Fizică": 2, "Chimie": 2, "Geografie": 2, "Informatică": 2, "Sport": 2, "Desen": 1, "Limba Franceză": 1},
            11: {"Română": 4, "Matematică": 5, "Engleză": 3, "Istorie": 2, "Religie": 1, "Biologie": 3,
                "Fizică": 2, "Chimie": 2, "Geografie": 2, "Filosofie": 1, "Psihologie": 2, "Informatică": 2, "Limba Franceză": 1},
            12: {"Română": 4, "Matematică": 5, "Engleză": 3, "Istorie": 2, "Religie": 1, "Biologie": 3,
                "Fizică": 2, "Chimie": 2, "Geografie": 2, "Filosofie": 2, "Psihologie": 2, "Informatică": 2}
        }

        # Obține toți profesorii și materiile lor
        c.execute("SELECT name, subject FROM teachers")
        teachers_by_subject = defaultdict(list)
        for teacher_name, subject in c.fetchall():
            teachers_by_subject[subject].append(teacher_name)

        def get_teacher_for_subject(subj, day, slot, fixed_teacher):
            """
            Alege cel mai potrivit profesor pentru o materie, ținând cont de limitele de ore
            și de disponibilitatea în slot-ul respectiv.
            """
            # Eliminăm partea cu "(grup X)" din numele materiei pentru a găsi profesorul corect
            base_subject = subj.split(" (grup")[0]
            
            if base_subject in fixed_teacher:
                return fixed_teacher[base_subject]
            
            c.execute("SELECT name FROM teachers WHERE subject = %s", (base_subject,))
            candidates = [r[0] for r in c.fetchall()]
            
            if not candidates:
                print(f"Niciun profesor pentru {base_subject} găsit în baza de date!")
                return None
            
            # Filtrăm candidații care sunt deja ocupați în acest slot
            free_candidates = [t for t in candidates if t not in teacher_schedule[(day, slot)]]
            
            # Dacă nu avem profesori liberi, folosim orice profesor disponibil
            if not free_candidates:
                free_candidates = candidates
            
            # Sortăm candidații după numărul de ore alocate (prioritate pentru cei cu mai puține ore)
            free_candidates.sort(key=lambda t: teacher_hours[t])
            
            # Verificăm dacă profesorul cu cele mai puține ore nu a depășit limita de 18 ore
            best_teacher = free_candidates[0]
            if teacher_hours[best_teacher] >= 18:
                # Încercăm să găsim un alt profesor care nu a depășit limita
                alternative_teachers = [t for t in free_candidates if teacher_hours[t] < 18]
                if alternative_teachers:
                    best_teacher = alternative_teachers[0]
                else:
                    print(f"Avertisment: Toți profesorii pentru {base_subject} au peste 18 ore!")
            
            return best_teacher

        def schedule_day(subjects, day, fixed_teacher):
            available_slots = list(range(1, len(subjects) + 1))
            assignment = {}

            for slot in available_slots:
                subj = subjects[slot - 1]
                teacher_chosen = get_teacher_for_subject(subj, day, slot, fixed_teacher)
                
                if not teacher_chosen:
                    continue
                
                # Actualizăm dicționarul de profesori fixați pentru materiile de bază
                base_subject = subj.split(" (grup")[0]
                fixed_teacher[base_subject] = teacher_chosen
                
                room = choose_room(subj)
                assignment[slot] = (subj, teacher_chosen, room)
                teacher_schedule[(day, slot)].add(teacher_chosen)
                teacher_hours[teacher_chosen] += 1
            
            return assignment

        for cls in class_list:
            retry = 0
            success = False
            
            while retry < 10 and not success:
                grade_str = ''.join(ch for ch in cls if ch.isdigit())
                if not grade_str:
                    print(f"Nu s-a putut determina clasa pentru {cls}")
                    break
                    
                grade = int(grade_str)
                if grade not in subject_distribution:
                    print(f"Nu există distribuție pentru clasa {grade}")
                    break

                dist = subject_distribution[grade].copy()
                subj_list = []
                for subj, cnt in dist.items():
                    subj_list.extend([subj] * cnt)

                total = len(subj_list)
                if total < 25 or total > 30:
                    print(f"[SKIP] {cls} are {total} ore – trebuie între 25 și 30.")
                    break

                # Nu mai amestecăm aleator materiile pentru a păstra ordinea logică
                # arranged = rearrange_subjects(subj_list)
                arranged = subj_list

                try:
                    lessons_per_day = distribute_between_5_and_6_per_day(len(arranged))
                    assigned_days = assign_subjects_to_days_variable(arranged, lessons_per_day, cls)
                    
                    if not assigned_days:
                        print(f"Nu s-a putut genera un orar valid pentru {cls}")
                        retry += 1
                        continue

                    # Verificăm repetările de materii în fiecare zi
                    has_repeats = False
                    for day_idx, day_subjects in enumerate(assigned_days):
                        # Extragem materia de bază (fără grupuri)
                        base_subjects = [s.split(" (grup")[0] for s in day_subjects]
                        counter = Counter(base_subjects)
                        repeats = [subj for subj, count in counter.items() if count > 1]
                        if repeats:
                            print(f"Ziua {days[day_idx]} pentru {cls} are materii repetate: {repeats}")
                            has_repeats = True
                    
                    if has_repeats:
                        retry += 1
                        continue
                    
                    # Distribuție echilibrată a profesorilor
                    fixed_teacher = {}
                    
                    # Verificăm dacă există suficienți profesori pentru a nu depăși limita de 18 ore
                    base_subjects = [s.split(" (grup")[0] for s in arranged]
                    for subj, count in Counter(base_subjects).items():
                        available_teachers = len(teachers_by_subject.get(subj, []))
                        if available_teachers == 0:
                            print(f"Avertisment: Nu există profesori pentru {subj}!")
                            continue
                            
                        required_teachers = (count + 17) // 18
                        if available_teachers < required_teachers:
                            print(f"Avertisment: Posibil să nu existe suficienți profesori pentru {subj}. Necesar: {required_teachers}, Disponibili: {available_teachers}")
                    
                    timetable_valid = True
                    temp_entries = []

                    for day_idx, day in enumerate(days):
                        assignment = schedule_day(assigned_days[day_idx], day, fixed_teacher)
                        
                        if not assignment:
                            timetable_valid = False
                            break
                            
                        if len(assignment) < 5:
                            print(f"Ziua {day} pentru {cls} are doar {len(assignment)} ore, mai puțin de minimul 5!")
                            timetable_valid = False
                            break

                        assignment = normalize_day_slots(assignment)
                        for slot, (subj, teacher, room) in assignment.items():
                            # Salvăm materia de bază în baza de date (fără partea cu grupul)
                            base_subject = subj.split(" (grup")[0]
                            current_id += 1
                            temp_entries.append((current_id, day, slot, cls, base_subject, teacher, room))
                    
                    if timetable_valid:
                        for entry in temp_entries:
                            c.execute("""
                                INSERT INTO timetable (id, day, hour, class, subject, teacher, room) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, entry)
                        success = True
                        print(f"Orar generat cu succes pentru {cls}!")
                        
                        # Verificăm materiile repetate în aceeași zi
                        c.execute("""
                            SELECT day, subject, COUNT(*) 
                            FROM timetable 
                            WHERE class = %s 
                            GROUP BY day, subject 
                            HAVING COUNT(*) > 1
                        """, (cls,))
                        repeats = c.fetchall()
                        if repeats:
                            print(f"  Materiile repetate în orar pentru {cls}:")
                            for day, subject, count in repeats:
                                print(f"    {day}: {subject} ({count} ore)")
                    else:
                        retry += 1
                        print(f"Încercare {retry} eșuată pentru {cls}, se încearcă din nou...")
                
                except Exception as e:
                    print(f"Eroare la generarea orarului pentru {cls}: {e}")
                    retry += 1

            if not success:
                print(f"Nu s-a putut genera un orar valid pentru {cls} după {retry} încercări!")

        # La final, verificăm profesorii cu ore peste limită
        over_limit = [(teacher, hours) for teacher, hours in teacher_hours.items() if hours > 18]
        if over_limit:
            print("\nATENȚIE! Următorii profesori au depășit limita de 18 ore:")
            for teacher, hours in over_limit:
                print(f"  {teacher}: {hours} ore")
        else:
            print("\nToți profesorii au sub limita de 18 ore.")
            
        # Verificăm și afișăm statistica privind repetările materiilor
        c.execute("""
            SELECT class, day, subject, COUNT(*) as count
            FROM timetable
            GROUP BY class, day, subject
            HAVING COUNT(*) > 1
            ORDER BY class, day
        """)
        repeats = c.fetchall()
        if repeats:
            print("\nStatistica materiilor repetate în aceeași zi:")
            for cls, day, subject, count in repeats:
                print(f"  {cls}, {day}: {subject} ({count} ore)")
        else:
            print("\nNu există materii repetate în aceeași zi pentru nicio clasă!")

        conn.commit()
        conn.close()
        print("[OK] Toate orarele au fost salvate.")
    
    except Exception as e:
        print(f"Eroare globală: {e}")
        if 'conn' in locals() and conn.is_connected():
            conn.close()
    
    
    

    
    
    
    
def analiza_profesori_vs_ore():
    import mysql.connector
    import math

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="create_mysql_schema"
    )
    c = conn.cursor()

    # Ore reale predate (din orar)
    c.execute("SELECT subject, COUNT(*) FROM timetable GROUP BY subject")
    ore_per_materie = dict(c.fetchall())

    # Câți profesori predau acea materie
    c.execute("SELECT subject, COUNT(*) FROM teachers GROUP BY subject")
    prof_per_materie = dict(c.fetchall())

    norma = 18
    print("\n📊 ANALIZĂ PROFESORI VS ORE:")
    for materie, total_ore in ore_per_materie.items():
        prof_existenti = prof_per_materie.get(materie, 0)
        prof_necesari = math.ceil(total_ore / norma)
        surplus = prof_existenti - prof_necesari
        status = f"{surplus} în plus" if surplus > 0 else "OK"
        print(f"▶ {materie}: {total_ore} ore | {prof_existenti} profesori | necesari: {prof_necesari} → {status}")

    conn.close()






@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    # NU mai apelăm generate_timetable automat
    # generate_timetable()

    conn = get_mysql_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT name FROM classes")
    classes = [row[0] for row in c.fetchall()]
    
    def class_sort_key(cls_name):
        match = re.match(r'(\d+)([A-Za-z])', cls_name)
        if match:
            return int(match.group(1)), match.group(2)
        return cls_name

    classes.sort(key=class_sort_key)
    
    days = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri']
    hours = range(1, 7)

    c.execute("SELECT class, day, hour, subject, teacher, room FROM timetable")
    raw_data = c.fetchall()
    timetable = {}
    for (cls, day, hour, subject, teacher, room) in raw_data:
        timetable[(cls, day, int(hour))] = (subject, teacher, room)


    conn.close()

    # DEBUG TIMETABLE
    print("\n--- DEBUG TIMETABLE ---")
    for key, value in timetable.items():
        print(f"{key} -> {value}")
    print("--- END DEBUG ---\n")

    return render_template('index.html',
                        classes=classes,
                        days=days,
                        hours=hours,
                        timetable=timetable)





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_mysql_connection()
        c = conn.cursor()

        # Fără liceu_id
        c.execute("SELECT role FROM users WHERE username=%s AND password=%s", (username, password))
        result = c.fetchone()

        if result:
            role = result[0]
            session['user'] = username
            session['role'] = role

            if role == 'student':
                c.execute("SELECT student_class FROM users WHERE username=%s", (username,))
                class_name = c.fetchone()[0]
                session['class'] = class_name
                conn.close()
                return redirect(url_for('class_timetable', class_name=class_name))

            conn.close()
            return redirect(url_for('index'))

        conn.close()
        flash("Autentificare eșuată!")
    return render_template('login.html')





@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_mysql_connection()
    c = conn.cursor()

    # -----------------------
    # ADĂUGARE PROFESOR
    if request.method == 'POST' and 'submit_prof' in request.form:
        nume = request.form['nume']
        materie = request.form['materie']
        username = request.form['username']
        parola = request.form['parola']

        c.execute("INSERT IGNORE INTO teachers (name, subject) VALUES (%s, %s)", (nume, materie))
        c.execute("INSERT IGNORE INTO users (username, password, role) VALUES (%s, %s, 'profesor')", (username, parola))
        conn.commit()
        return redirect(url_for('admin_panel'))

    # -----------------------
    # ADĂUGARE ELEV
    if request.method == 'POST' and 'submit_elev' in request.form:
        username = request.form['username']
        parola = request.form['parola']
        clasa = request.form['clasa']

        c.execute("INSERT IGNORE INTO users (username, password, role, student_class) VALUES (%s, %s, 'student', %s)", (username, parola, clasa))
        conn.commit()
        return redirect(url_for('admin_panel'))

    # -----------------------
    # ADĂUGARE MATERIE (doar salvăm în tabela teachers cu nume generic)
    if request.method == 'POST' and 'submit_materi' in request.form:
        materie_noua = request.form['materie_noua']
        # adaugăm ca profesor generic doar pentru listare
        c.execute("INSERT IGNORE INTO teachers (name, subject) VALUES (%s, %s)", ('[temporar]', materie_noua))
        conn.commit()
        return redirect(url_for('admin_panel'))

    # -----------------------
    # ADĂUGARE SALĂ
    if request.method == 'POST' and 'submit_sala' in request.form:
        sala = request.form['sala']
        tip = request.form['tip']

        c.execute("INSERT IGNORE INTO rooms (name, type) VALUES (%s, %s)", (sala, tip))
        conn.commit()
        return redirect(url_for('admin_panel'))

    # -----------------------
    # DATE PENTRU AFIȘARE

    # Profesori
    c.execute("SELECT name, subject FROM teachers WHERE name != '[temporar]'")
    existing_teachers = c.fetchall()

    # Elevi
    c.execute("SELECT username, student_class FROM users WHERE role = 'student'")
    elevi_existenti = c.fetchall()

    # Clase (pentru dropdown elev)
    c.execute("SELECT name FROM classes")
    classes = [r[0] for r in c.fetchall()]

    # Materii distincte
    c.execute("SELECT DISTINCT subject FROM teachers WHERE subject != ''")
    materii_existente = [r[0] for r in c.fetchall()]

    # Săli
    c.execute("SELECT name, type FROM rooms")
    sali_existente = c.fetchall()
    
    
        # -----------------------
    # ȘTERGERE ENTITATE
    if request.method == 'POST' and 'delete_type' in request.form:
        delete_type = request.form['delete_type']
        delete_name = request.form['delete_name']

        if delete_type == 'profesor':
            c.execute("DELETE FROM teachers WHERE name = %s", (delete_name,))
            c.execute("DELETE FROM users WHERE username = %s AND role = 'profesor'", (delete_name,))
        elif delete_type == 'elev':
            c.execute("DELETE FROM users WHERE username = %s AND role = 'student'", (delete_name,))
        elif delete_type == 'materie':
            c.execute("DELETE FROM teachers WHERE subject = %s", (delete_name,))
        elif delete_type == 'sala':
            c.execute("DELETE FROM rooms WHERE name = %s", (delete_name,))

        conn.commit()
        return redirect(url_for('admin_panel'))


    conn.close()

    return render_template(
        'admin_panel.html',
        teachers=existing_teachers,
        elevi=elevi_existenti,
        classes=classes,
        materii=materii_existente,
        sali=sali_existente
    )







@app.route('/class/<class_name>')
def class_timetable(class_name):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_mysql_connection()
    c = conn.cursor()
    c.execute("""
        SELECT day, hour, subject, teacher, room
        FROM timetable
        WHERE class=%s
    """, (class_name,))
    data = c.fetchall()

    c.execute("""
        SELECT day, hour, new_subject, new_teacher, new_room 
        FROM overrides
        WHERE class=%s
    """, (class_name,))
    override_data = c.fetchall()
    overrides = {}
    for day, hour, new_subject, new_teacher, new_room in override_data:
        overrides[(day, hour)] = (new_subject, new_teacher, new_room)

    conn.close()

    days = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri']
    hours = range(1, 7)
    hour_labels = {
        1: "8-9", 2: "9-10", 3: "10-11", 4: "11-12", 
        5: "12-13", 6: "13-14",
    }

    timetable = {}
    for h in hours:
        timetable[h] = {d: None for d in days}
    for row in data:
        day, hour, subject, teacher, room = row
        key = (day, hour)
        if key in overrides:
            timetable[hour][day] = overrides[key]
        else:
            timetable[hour][day] = (subject, teacher, room)

    return render_template('class_timetable.html',
                           class_name=class_name,
                           timetable=timetable,
                           days=days,
                           hours=hours,
                           hour_labels=hour_labels)


@app.route('/edit', methods=['POST'])
def edit_timetable():
    conn = get_mysql_connection()
    c = conn.cursor()
    day = request.form['day']
    hour = int(request.form['hour'])
    cls = request.form['class']
    subject = request.form['subject']
    teacher = request.form['teacher']
    room = request.form['room']

    # Salvăm modificările în tabela de override-uri (MySQL: ON DUPLICATE KEY)
    c.execute("""
        INSERT INTO overrides (class, day, hour, new_subject, new_teacher, new_room, reason)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            new_subject = VALUES(new_subject),
            new_teacher = VALUES(new_teacher),
            new_room = VALUES(new_room),
            reason = VALUES(reason),
            timestamp = CURRENT_TIMESTAMP
    """, (cls, day, hour, subject, teacher, room, "Editare directă"))

    conn.commit()
    conn.close()
    return "success"



### EXPORT PDF


@app.route('/export/pdf')
def export_pdf():
    conn = get_mysql_connection()
    c = conn.cursor()
    c.execute("SELECT class, day, hour, subject, teacher, room FROM timetable")
    raw_data = c.fetchall()
    conn.close()

    timetable = {}
    for cls, day, hour, subject, teacher, room in raw_data:
        timetable[(cls, day, hour)] = f"{subject} - {teacher} ({room})"

    classes = sorted(list({cls for cls, _, _, _, _, _ in raw_data}),
                     key=lambda x: (int(''.join(filter(str.isdigit, x))), x))

    from fpdf import FPDF
    import math

    days = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri']
    hours = range(1, 7)
    hour_labels = {
        1:"8-9", 2:"9-10", 3:"10-11", 4:"11-12", 5:"12-13", 6:"13-14"
    }

    pdf = FPDF('L', 'mm', 'A4')
    pdf.add_font('DejaVuSans', '', 'DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVuSans', 'B', 'DejaVuSans-Bold.ttf', uni=True)
    pdf.set_auto_page_break(True, margin=10)

    margin = 10
    page_width = pdf.w - 2 * margin
    class_col_width = 30
    other_cols_width = (page_width - class_col_width) / 7
    line_height = 5

    def calc_nb_lines(txt, col_width, font_size):
        pdf.set_font('DejaVuSans', '', font_size)
        effective_width = col_width - 2
        if txt == "-":
            return 1
        text_width = pdf.get_string_width(txt)
        if text_width == 0:
            return 1
        return max(1, math.ceil(text_width / effective_width))

    for day in days:
        pdf.add_page()
        pdf.set_font('DejaVuSans', 'B', 16)
        pdf.cell(0, 10, txt=f"Orar - {day}", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font('DejaVuSans', 'B', 10)
        pdf.cell(class_col_width, 10, "Clasă", border=1, align="C")
        for hr in hours:
            pdf.cell(other_cols_width, 10, hour_labels[hr], border=1, align="C")
        pdf.ln()

        pdf.set_font('DejaVuSans', '', 8)
        for cls in classes:
            row_texts = [cls]
            for hr in hours:
                cell_value = timetable.get((cls, day, hr), "-")
                row_texts.append(cell_value)

            col_widths = [class_col_width] + [other_cols_width] * len(hours)
            font_size = 8
            nb_lines_list = [calc_nb_lines(str(txt), w, font_size) for txt, w in zip(row_texts, col_widths)]
            max_lines_in_row = max(nb_lines_list)
            row_h = max_lines_in_row * line_height

            x_start = pdf.get_x()
            y_start = pdf.get_y()
            for i, txt in enumerate(row_texts):
                x_current = pdf.get_x()
                y_current = pdf.get_y()
                pdf.set_font('DejaVuSans', '', font_size)
                pdf.multi_cell(col_widths[i], line_height, str(txt), border=0, align="C")
                pdf.rect(x_current, y_current, col_widths[i], row_h)
                pdf.set_xy(x_current + col_widths[i], y_current)
            pdf.set_xy(x_start, y_start + row_h)

    pdf.output("timetable.pdf")
    return send_file("timetable.pdf", as_attachment=True)



#### Export Excel



@app.route('/export/excel')
def export_excel():
    import pandas as pd

    conn = get_mysql_connection()
    c = conn.cursor()
    c.execute("SELECT class, day, hour, subject, teacher, room FROM timetable")
    raw_data = c.fetchall()
    conn.close()

    timetable = {}
    for cls, day, hour, subject, teacher, room in raw_data:
        timetable[(cls, day, hour)] = f"{subject} - {teacher} ({room})"

    classes = sorted(list({cls for cls, _, _, _, _, _ in raw_data}),
                     key=lambda x: (int(''.join(filter(str.isdigit, x))), x))

    days = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri']
    hours = range(1, 7)
    hour_labels = {
        1: "8-9", 2: "9-10", 3: "10-11", 4: "11-12", 5: "12-13", 6: "13-14"
    }

    day_colors = {
        'Luni': '#FFEFD5',
        'Marți': '#E6E6FA',
        'Miercuri': '#FFFACD',
        'Joi': '#D1F7D1',
        'Vineri': '#FFD5D5'
    }

    with pd.ExcelWriter("timetable.xlsx", engine="xlsxwriter") as writer:
        workbook = writer.book
        for day in days:
            worksheet = workbook.add_worksheet(day)
            worksheet.set_column(0, 0, 12)
            for col in range(1, 8):
                worksheet.set_column(col, col, 18)

            header_fmt = workbook.add_format({
                "bold": True,
                "text_wrap": True,
                "valign": "vcenter",
                "align": "center",
                "border": 1,
                "bg_color": day_colors.get(day, "#FFFFFF")
            })
            worksheet.write(0, 0, "Clasă", header_fmt)
            for idx, hr in enumerate(hours):
                worksheet.write(0, idx + 1, hour_labels[hr], header_fmt)

            class_fmt = workbook.add_format({
                "bold": True,
                "valign": "vcenter",
                "align": "center",
                "border": 1
            })
            cell_fmt = workbook.add_format({
                "text_wrap": True,
                "valign": "vcenter",
                "align": "center",
                "border": 1
            })

            row_idx = 1
            for cls in classes:
                worksheet.write(row_idx, 0, cls, class_fmt)
                for idx, hr in enumerate(hours):
                    cell_text = timetable.get((cls, day, hr), "-")
                    worksheet.write(row_idx, idx + 1, cell_text, cell_fmt)
                row_idx += 1

    return send_file("timetable.xlsx", as_attachment=True)



### Export clasa Excel



@app.route('/export/pdf/class/<class_name>')
def export_pdf_class(class_name):
    from fpdf import FPDF
    import math

    conn = get_mysql_connection()
    c = conn.cursor()
    c.execute("SELECT day, hour, subject, teacher, room FROM timetable WHERE class = %s", (class_name,))
    data = c.fetchall()
    conn.close()
    
    timetable = {}
    for day, hour, subject, teacher, room in data:
        timetable[(day, hour)] = f"{subject} - {teacher} ({room})"
    
    days = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri']
    hours = range(1, 7)
    hour_labels = {
        1: "8-9", 2: "9-10", 3: "10-11", 4: "11-12", 5: "12-13", 6: "13-14"
    }
    
    pdf = FPDF('L', 'mm', 'A4')
    pdf.add_font('DejaVuSans', '', 'DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVuSans', 'B', 'DejaVuSans-Bold.ttf', uni=True)
    pdf.set_auto_page_break(True, margin=10)
    
    margin = 10
    page_width = pdf.w - 2 * margin
    time_col_width = 20
    other_cols_width = (page_width - time_col_width) / len(days)
    line_height = 5
    font_size = 10

    def calc_nb_lines(txt, col_width, fsize):
        pdf.set_font('DejaVuSans', '', fsize)
        effective_width = col_width - 2
        if txt == "-":
            return 1
        text_width = pdf.get_string_width(txt)
        if text_width == 0:
            return 1
        return max(1, math.ceil(text_width / effective_width))

    pdf.add_page()
    pdf.set_font('DejaVuSans', 'B', 16)
    pdf.cell(0, 10, txt=f"Orar Clasă {class_name}", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font('DejaVuSans', 'B', font_size)
    row_texts = ["Ora"] + days
    col_widths = [time_col_width] + [other_cols_width] * len(days)
    
    nb_lines_list = [calc_nb_lines(txt, w, font_size) for txt, w in zip(row_texts, col_widths)]
    max_lines_in_row = max(nb_lines_list)
    row_h = max_lines_in_row * line_height
    
    x_start = pdf.get_x()
    y_start = pdf.get_y()
    for i, txt in enumerate(row_texts):
        x_current = pdf.get_x()
        y_current = pdf.get_y()
        pdf.multi_cell(col_widths[i], line_height, txt, border=0, align="C")
        pdf.rect(x_current, y_current, col_widths[i], row_h)
        pdf.set_xy(x_current + col_widths[i], y_current)
    pdf.set_xy(x_start, y_start + row_h)
    
    pdf.set_font('DejaVuSans', '', font_size)
    for hr in hours:
        row_texts = [hour_labels[hr]] + [timetable.get((day, hr), "-") for day in days]
        nb_lines_list = [calc_nb_lines(txt, w, font_size) for txt, w in zip(row_texts, col_widths)]
        max_lines_in_row = max(nb_lines_list)
        row_h = max_lines_in_row * line_height
        
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        for i, txt in enumerate(row_texts):
            x_current = pdf.get_x()
            y_current = pdf.get_y()
            pdf.multi_cell(col_widths[i], line_height, txt, border=0, align="C")
            pdf.rect(x_current, y_current, col_widths[i], row_h)
            pdf.set_xy(x_current + col_widths[i], y_current)
        pdf.set_xy(x_start, y_start + row_h)
    
    pdf_file = f"timetable_{class_name}.pdf"
    pdf.output(pdf_file)
    return send_file(pdf_file, as_attachment=True)





############ DETALII PROFESOR ######


@app.route('/detalii_profesor', methods=['GET', 'POST'])
def detalii_profesor():
    if 'user' not in session or session.get('role') != 'director':
        return redirect(url_for('login'))

    conn = get_mysql_connection()
    c = conn.cursor()

    # Dropdown: lista profesorilor
    c.execute("SELECT DISTINCT teacher FROM timetable ORDER BY teacher")
    profesori = [row[0] for row in c.fetchall()]

    date_profesor = None
    selected = request.form.get('profesor')

    if selected:
        # Total ore
        c.execute("SELECT COUNT(*) FROM timetable WHERE teacher = %s", (selected,))
        total_ore = c.fetchone()[0]

        # Clase + zile + săli
        c.execute("""
            SELECT class, day, room, subject, hour 
            FROM timetable 
            WHERE teacher = %s 
            ORDER BY day, hour
        """, (selected,))
        program = c.fetchall()

        date_profesor = {
            'nume': selected,
            'total_ore': total_ore,
            'program': program
        }

    conn.close()
    return render_template('detalii_profesor.html', profesori=profesori, date=date_profesor)





### export excel clasa



@app.route('/export/excel/class/<class_name>')
def export_excel_class(class_name):
    import pandas as pd

    conn = get_mysql_connection()
    c = conn.cursor()
    c.execute("SELECT day, hour, subject, teacher, room FROM timetable WHERE class = %s", (class_name,))
    data = c.fetchall()
    conn.close()

    timetable = {}
    for day, hour, subject, teacher, room in data:
        timetable[(day, hour)] = f"{subject} - {teacher} ({room})"

    days = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri']
    hours = range(1, 7)
    hour_labels = {
        1: "8-9", 2: "9-10", 3: "10-11", 4: "11-12", 5: "12-13", 6: "13-14"
    }

    file_name = f"timetable_{class_name}.xlsx"
    with pd.ExcelWriter(file_name, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Orar")

        worksheet.set_column(0, 0, 12)
        for col in range(1, len(days) + 1):
            worksheet.set_column(col, col, 18)

        header_fmt = workbook.add_format({
            "bold": True,
            "text_wrap": True,
            "valign": "vcenter",
            "align": "center",
            "border": 1,
            "bg_color": "#DCE6F1"
        })
        cell_fmt = workbook.add_format({
            "text_wrap": True,
            "valign": "vcenter",
            "align": "center",
            "border": 1
        })

        worksheet.write(0, 0, "Ora", header_fmt)
        for idx, day in enumerate(days):
            worksheet.write(0, idx + 1, day, header_fmt)

        row = 1
        for hr in hours:
            worksheet.write(row, 0, hour_labels[hr], header_fmt)
            for idx, d in enumerate(days):
                cell_text = timetable.get((d, hr), "-")
                worksheet.write(row, idx + 1, cell_text, cell_fmt)
            row += 1

    return send_file(file_name, as_attachment=True)






@app.route('/manual_edit/<class_name>', methods=['GET', 'POST'])
def manual_edit(class_name):
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        day = request.form['day']
        hour = int(request.form['hour'])
        new_subject = request.form['new_subject']
        new_teacher = request.form['new_teacher']
        new_room = request.form['new_room']
        reason = request.form.get('reason', '')

        conn = get_mysql_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO overrides (class, day, hour, new_subject, new_teacher, new_room, reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                new_subject = VALUES(new_subject),
                new_teacher = VALUES(new_teacher),
                new_room = VALUES(new_room),
                reason = VALUES(reason),
                timestamp = CURRENT_TIMESTAMP
        """, (class_name, day, hour, new_subject, new_teacher, new_room, reason))
        conn.commit()
        conn.close()
        flash("Modificare salvată!")
        return redirect(url_for('manual_edit', class_name=class_name))

    conn = get_mysql_connection()
    c = conn.cursor()
    c.execute("""
        SELECT day, hour, new_subject, new_teacher, new_room, reason 
        FROM overrides
        WHERE class = %s
    """, (class_name,))
    overrides = c.fetchall()
    conn.close()

    return render_template('manual_edit.html', class_name=class_name, overrides=overrides)



###Regenerare orar - manual




@app.route('/reset_timetable', methods=['POST'])
def reset_timetable():
    conn = get_mysql_connection()
    c = conn.cursor()
    c.execute("DELETE FROM overrides")
    
    conn.commit()
    conn.close()

    generate_timetable()  # ← aici e cheia, regenerăm orarul
    return "Orarul a fost resetat și regenerat cu succes!"







@app.route('/available_options', methods=['GET'])
def available_options():
    from flask import jsonify

    subject = request.args.get('subject')
    day = request.args.get('day')
    hour = int(request.args.get('hour'))

    conn = get_mysql_connection()
    c = conn.cursor()

    # Obținem toți profesorii care predau materia respectivă
    c.execute("SELECT name FROM teachers WHERE subject = %s", (subject,))
    teachers = [r[0] for r in c.fetchall()]

    # Obținem sălile potrivite
    def choose_room_options(subj):
        if subj in ["Informatică", "TIC"]:
            return ["Lab IT"]
        elif subj == "Chimie":
            return ["Lab Chimie"]
        elif subj == "Sport":
            return ["Sala Sport"]
        elif subj == "Muzică":
            return ["Sala de Muzică"]
        elif subj in ["Desen", "Arte Plastice"]:
            return ["Sala de Arte Plastice"]
        else:
            c.execute("SELECT name FROM rooms WHERE type = 'obișnuită'")
            return [r[0] for r in c.fetchall()]

    room_options = choose_room_options(subject)

    conn.close()
    return jsonify({"teachers": teachers, "rooms": room_options})


@app.route('/profesor_ore')
def profesor_ore():
    if 'user' not in session or session.get('role') != 'profesor':
        return redirect(url_for('login'))

    profesor = session['user']
    conn = get_mysql_connection()
    c = conn.cursor()

    # Luăm orele din orar unde apare ca profesor
    c.execute("""
        SELECT class, day, hour, subject
        FROM timetable
        WHERE teacher = %s
        ORDER BY day, hour
    """, (profesor,))
    ore = c.fetchall()
    conn.close()

    # Structură: zi → listă de ore (clasă, ora, materie)
    zile = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri']
    ore_pe_zi = {zi: [] for zi in zile}
    total_ore = 0

    for cls, zi, ora, materie in ore:
        ore_pe_zi[zi].append((ora, cls, materie))
        total_ore += 1

    # Sortăm orele în fiecare zi după oră
    for zi in ore_pe_zi:
        ore_pe_zi[zi].sort()

    return render_template('profesor_ore.html', profesor=profesor, ore_pe_zi=ore_pe_zi, total_ore=total_ore)



@app.route('/rapoarte_director')
def rapoarte_director():
    if 'user' not in session or session.get('role') != 'director':
        return redirect(url_for('login'))

    conn = get_mysql_connection()
    c = conn.cursor()

    # Profesori: nume, materie, total ore, zile active, clase
    c.execute("SELECT name, subject FROM teachers")
    prof_materii = dict(c.fetchall())

    c.execute("SELECT teacher, day, class FROM timetable")
    prof_raw = c.fetchall()

    prof_data = {}
    for teacher, zi, cls in prof_raw:
        if teacher not in prof_data:
            prof_data[teacher] = {
                "materie": prof_materii.get(teacher, "?"),
                "zile_active": set(),
                "clase_unice": set(),
                "total_ore": 0
            }
        prof_data[teacher]["zile_active"].add(zi)
        prof_data[teacher]["clase_unice"].add(cls)
        prof_data[teacher]["total_ore"] += 1

    profesori = []
    for nume, info in prof_data.items():
        profesori.append({
            "nume": nume,
            "materie": info["materie"],
            "zile_active": list(info["zile_active"]),
            "clase_unice": list(info["clase_unice"]),
            "total_ore": info["total_ore"]
        })

    # Clase: nume, total ore, zile active, ore/zi
    c.execute("SELECT class, day FROM timetable")
    raw_clase = c.fetchall()
    repartizare = {}
    for cls, zi in raw_clase:
        repartizare.setdefault(cls, {}).setdefault(zi, 0)
        repartizare[cls][zi] += 1

    clase = []
    for cls, zile in repartizare.items():
        total_ore = sum(zile.values())
        clase.append({
            "nume": cls,
            "total_ore": total_ore,
            "zile_active": list(zile.keys()),
            "repartizare": zile
        })

    # Săli: nume, tip, număr total de utilizări
    c.execute("SELECT name, type FROM rooms")
    room_types = dict(c.fetchall())

    c.execute("SELECT room FROM timetable")
    raw_sali = c.fetchall()
    sali_counter = {}
    for (sala,) in raw_sali:
        sali_counter[sala] = sali_counter.get(sala, 0) + 1

    sali = []
    for sala, nr in sali_counter.items():
        sali.append({
            "nume": sala,
            "tip": room_types.get(sala, "?"),
            "ore": nr
        })

    conn.close()

    return render_template("rapoarte_director.html",
                           profesori=profesori,
                           clase=clase,
                           sali=sali)






import re

@app.route('/view_fullscreen')
def view_fullscreen():
    if 'user' not in session or session.get('role') not in ['admin', 'profesor', 'director']:
        return redirect(url_for('login'))

    conn = get_mysql_connection()
    c = conn.cursor(buffered=True)
    c.execute("SELECT DISTINCT name FROM classes")
    classes = [row[0] for row in c.fetchall()]

    # Sortează clasele (ex: 9A, 9B, 10A, etc.)
    def class_sort_key(cls_name):
        match = re.match(r'(\d+)([A-Za-z])', cls_name)
        if match:
            return int(match.group(1)), match.group(2)
        return cls_name

    classes.sort(key=class_sort_key)

    days = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri']
    hours = range(1, 7)

    # Preluăm toate intrările din tabelul timetable într-un singur query
    c.execute("SELECT class, day, hour, subject, teacher, room FROM timetable")
    raw_data = c.fetchall()
    timetable = {}
    for (cls, day, hour, subject, teacher, room) in raw_data:
        timetable[(cls, day, int(hour))] = (subject, teacher, room)

    conn.close()

    return render_template('viewer.html', classes=classes, days=days, hours=hours, timetable=timetable)







@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


import webbrowser

if __name__ == '__main__':
    init_db()
    generate_timetable()

    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open("http://localhost:5000")

    app.run(debug=True)
