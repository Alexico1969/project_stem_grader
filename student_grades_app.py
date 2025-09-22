#!/usr/bin/env python3
"""
Student Grades Management App
A tkinter application to manage and view student grades from Project Stem and class lists.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import csv
import re
from collections import defaultdict
from google_sheets_integration import GoogleSheetsExporter

class StudentGradesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Grades Management System")
        self.root.geometry("1000x700")
        
        # Data storage
        self.grades_data = []
        self.student_names = {}
        self.assignments = []
        self.students = []
        
        # Google Sheets integration
        self.sheets_exporter = GoogleSheetsExporter()
        
        # Create main interface
        self.create_widgets()
        
        # Load data
        self.load_data()
    
    def create_widgets(self):
        """Create the main interface widgets"""
        # Title
        title_label = tk.Label(self.root, text="Student Grades Management System", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Menu frame
        menu_frame = tk.Frame(self.root)
        menu_frame.pack(pady=20)

        # Menu buttons
        btn1 = tk.Button(menu_frame, text="1. Find Grade for Specific Student and Assignment",
                         command=self.find_specific_grade, width=50, height=2)
        btn1.pack(pady=5)

        btn2 = tk.Button(menu_frame, text="2. Find All Grades for a Specific Student",
                         command=self.find_student_grades, width=50, height=2)
        btn2.pack(pady=5)

        btn3 = tk.Button(menu_frame, text="3. Find All Grades for a Specific Assignment",
                         command=self.find_assignment_grades, width=50, height=2)
        btn3.pack(pady=5)

        btn4 = tk.Button(menu_frame, text="4. Export Assignment Grades to Google Sheets",
                         command=self.export_to_google_sheets, width=50, height=2)
        btn4.pack(pady=5)

        btn5 = tk.Button(menu_frame, text="5. Export Sub-chapter to Google Sheets",
                         command=self.export_subchapter_to_sheets, width=50, height=2)
        btn5.pack(pady=5)
        
        # Results area
        results_frame = tk.Frame(self.root)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(results_frame, text="Results:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=20, width=100)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Data loaded successfully")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_data(self):
        """Load data from CSV files"""
        try:
            # Load grades data
            self.load_grades_data()
            
            # Load student names from F2, F5, F6
            self.load_student_names()
            
            # Extract assignments and students
            self.extract_assignments_and_students()
            
            self.status_var.set(f"Data loaded: {len(self.students)} students, {len(self.assignments)} assignments")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            self.status_var.set("Error loading data")
    
    def load_grades_data(self):
        """Load grades data from the main CSV file"""
        try:
            with open('grades.csv', 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                
                # Skip header and points possible rows
                header = next(reader)
                next(reader)  # Skip points possible row
                
                # Store assignments (skip first 5 columns which are student info)
                self.assignments = header[5:]
                
                # Load student data
                for row_num, row in enumerate(reader, start=3):  # Start from row 3 (after header and points)
                    if row and row[0].strip():
                        # The CSV reader already handles quotes, so we don't need regex matching
                        student_name = row[0].strip()
                        student_id = row[1] if len(row) > 1 else ""
                        
                        # Store grades data
                        grades = {}
                        for i, assignment in enumerate(self.assignments):
                            if i + 5 < len(row):
                                grade_value = row[i + 5].strip()
                                if grade_value:
                                    try:
                                        grades[assignment] = float(grade_value)
                                    except ValueError:
                                        grades[assignment] = grade_value
                                else:
                                    grades[assignment] = None
                        
                        self.grades_data.append({
                            'name': student_name,
                            'id': student_id,
                            'grades': grades
                        })
                            
        except FileNotFoundError:
            raise Exception("Grades CSV file not found")
        except Exception as e:
            raise Exception(f"Error reading grades file: {str(e)}")
    
    def load_student_names(self):
        """Load student names from F2, F5, F6 files"""
        self.student_names = {'F2': [], 'F5': [], 'F6': []}
        
        for file_prefix in ['F2', 'F5', 'F6']:
            filename = f'{file_prefix} - names.csv'
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if row and row[0].strip() and row[0].lower() != 'name':
                            self.student_names[file_prefix].append(row[0].strip())
            except FileNotFoundError:
                print(f"Warning: {filename} not found")
            except Exception as e:
                print(f"Warning: Error reading {filename}: {str(e)}")
    
    def extract_assignments_and_students(self):
        """Extract unique assignments and students"""
        self.students = []
        for student in self.grades_data:
            # Convert "Last, First" format to "First Last" for display
            if ',' in student['name']:
                parts = student['name'].split(', ')
                if len(parts) == 2:
                    display_name = f"{parts[1]} {parts[0]}"
                else:
                    display_name = student['name']
            else:
                display_name = student['name']
            
            self.students.append(display_name)
        
        self.students.sort()
    
    def normalize_name(self, name):
        """Normalize names for comparison"""
        return re.sub(r'\s+', ' ', name.strip().lower())
    
    def find_student_in_grades(self, search_name):
        """Find a student in grades data using flexible matching"""
        search_normalized = self.normalize_name(search_name)
        
        for student in self.grades_data:
            # Convert "Last, First" format to "First Last" for comparison
            if ',' in student['name']:
                parts = student['name'].split(', ')
                if len(parts) == 2:
                    student_display_name = f"{parts[1]} {parts[0]}"
                else:
                    student_display_name = student['name']
            else:
                student_display_name = student['name']
            
            student_normalized = self.normalize_name(student_display_name)
            
            # Check exact match
            if search_normalized == student_normalized:
                return student
            
            # Check flexible matching (first and last name)
            search_parts = search_normalized.split()
            student_parts = self.normalize_name(student['name']).split(', ')
            
            if len(search_parts) >= 2 and len(student_parts) >= 2:
                search_first_last = {search_parts[0], search_parts[-1]}
                student_first_last = {student_parts[1].split()[0], student_parts[0].split()[0]}
                
                if search_first_last == student_first_last:
                    return student
        
        return None
    
    def find_specific_grade(self):
        """Menu option 1: Find grade for specific student and assignment"""
        dialog = SpecificGradeDialog(self.root, self.students, self.assignments)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            student_name, assignment = dialog.result
            student = self.find_student_in_grades(student_name)
            
            if student:
                grade = student['grades'].get(assignment)
                if grade is not None:
                    result = f"Student: {student_name}\n"
                    result += f"Assignment: {assignment}\n"
                    result += f"Grade: {grade}\n"
                    result += f"Student ID: {student['id']}\n"
                else:
                    result = f"Student: {student_name}\n"
                    result += f"Assignment: {assignment}\n"
                    result += "Grade: Not submitted/No grade\n"
            else:
                result = f"Student '{student_name}' not found in grades data.\n"
                result += "Available students:\n"
                for s in self.students[:10]:  # Show first 10 as examples
                    result += f"  - {s}\n"
                if len(self.students) > 10:
                    result += f"  ... and {len(self.students) - 10} more\n"
            
            self.display_result(result)
    
    def find_student_grades(self):
        """Menu option 2: Find all grades for a specific student"""
        dialog = StudentSelectionDialog(self.root, self.students)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            student_name = dialog.result
            student = self.find_student_in_grades(student_name)
            
            if student:
                result = f"All Grades for: {student_name}\n"
                result += f"Student ID: {student['id']}\n"
                result += "=" * 50 + "\n\n"
                
                # Group assignments by type
                lesson_practice = []
                code_practice = []
                assignments = []
                quizzes = []
                tests = []
                other = []
                
                for assignment, grade in student['grades'].items():
                    if grade is not None:
                        if "Lesson Practice" in assignment:
                            lesson_practice.append((assignment, grade))
                        elif "Code Practice" in assignment:
                            code_practice.append((assignment, grade))
                        elif "Assignment" in assignment:
                            assignments.append((assignment, grade))
                        elif "Quiz" in assignment:
                            quizzes.append((assignment, grade))
                        elif "Test" in assignment:
                            tests.append((assignment, grade))
                        else:
                            other.append((assignment, grade))
                
                # Display by category
                if lesson_practice:
                    result += "LESSON PRACTICE:\n"
                    for assignment, grade in lesson_practice:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                if code_practice:
                    result += "CODE PRACTICE:\n"
                    for assignment, grade in code_practice:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                if assignments:
                    result += "ASSIGNMENTS:\n"
                    for assignment, grade in assignments:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                if quizzes:
                    result += "QUIZZES:\n"
                    for assignment, grade in quizzes:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                if tests:
                    result += "TESTS:\n"
                    for assignment, grade in tests:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                if other:
                    result += "OTHER:\n"
                    for assignment, grade in other:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                # Summary
                total_grades = len([g for g in student['grades'].values() if g is not None])
                result += f"Total completed assignments: {total_grades}\n"
                
            else:
                result = f"Student '{student_name}' not found in grades data.\n"
            
            self.display_result(result)
    
    def find_assignment_grades(self):
        """Menu option 3: Find all grades for a specific assignment"""
        dialog = AssignmentSelectionDialog(self.root, self.assignments)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            assignment = dialog.result
            result = f"All Grades for Assignment: {assignment}\n"
            result += "=" * 50 + "\n\n"
            
            # Group students by their class sections (F2, F5, F6)
            f2_grades = []
            f5_grades = []
            f6_grades = []
            other_grades = []
            
            for student in self.grades_data:
                # Get the raw grade (may be None if not submitted)
                grade = student['grades'].get(assignment)

                # Determine which class section this student belongs to (None -> Other)
                student_section = self.get_student_section(student['name'])

                # Display empty string for missing grades so the student still appears in the roster
                display_grade = grade if grade is not None else ""

                if student_section == 'F2':
                    f2_grades.append((student['name'], display_grade))
                elif student_section == 'F5':
                    f5_grades.append((student['name'], display_grade))
                elif student_section == 'F6':
                    f6_grades.append((student['name'], display_grade))
                else:
                    other_grades.append((student['name'], display_grade))
            
            # Display results by section
            total_students_with_grades = len(f2_grades) + len(f5_grades) + len(f6_grades) + len(other_grades)
            result += f"Total students with grades: {total_students_with_grades}\n\n"
            
            # F2 Section
            if f2_grades:
                f2_grades.sort(key=lambda x: self.get_last_name(x[0]))
                result += "F2 SECTION:\n"
                result += "-" * 20 + "\n"
                for student_name, grade in f2_grades:
                    csv_format = self.format_csv_name(student_name, grade)
                    result += f"{csv_format}\n"
                result += f"\nF2 Total: {len(f2_grades)} students\n\n"
            
            # F5 Section
            if f5_grades:
                f5_grades.sort(key=lambda x: self.get_last_name(x[0]))
                result += "F5 SECTION:\n"
                result += "-" * 20 + "\n"
                for student_name, grade in f5_grades:
                    csv_format = self.format_csv_name(student_name, grade)
                    result += f"{csv_format}\n"
                result += f"\nF5 Total: {len(f5_grades)} students\n\n"
            
            # F6 Section
            if f6_grades:
                f6_grades.sort(key=lambda x: self.get_last_name(x[0]))
                result += "F6 SECTION:\n"
                result += "-" * 20 + "\n"
                for student_name, grade in f6_grades:
                    csv_format = self.format_csv_name(student_name, grade)
                    result += f"{csv_format}\n"
                result += f"\nF6 Total: {len(f6_grades)} students\n\n"
            
            # Other students (not in F2, F5, F6)
            if other_grades:
                other_grades.sort(key=lambda x: self.get_last_name(x[0]))
                result += "OTHER STUDENTS:\n"
                result += "-" * 20 + "\n"
                for student_name, grade in other_grades:
                    csv_format = self.format_csv_name(student_name, grade)
                    result += f"{csv_format}\n"
                result += f"\nOther Total: {len(other_grades)} students\n\n"
            
            # Overall Statistics
            all_grades = f2_grades + f5_grades + f6_grades + other_grades
            numeric_grades = [g for _, g in all_grades if isinstance(g, (int, float))]
            if numeric_grades:
                result += "OVERALL STATISTICS:\n"
                result += "-" * 20 + "\n"
                result += f"Average: {sum(numeric_grades) / len(numeric_grades):.2f}\n"
                result += f"Highest: {max(numeric_grades)}\n"
                result += f"Lowest: {min(numeric_grades)}\n"
            
            if total_students_with_grades == 0:
                result += "No students have submitted this assignment.\n"
            
            self.display_result(result)
    
    def export_to_google_sheets(self):
        """Menu option 4: Export assignment grades to Google Sheets"""
        dialog = AssignmentSelectionDialog(self.root, self.assignments)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            assignment = dialog.result
            
            # Group students by their class sections (F2, F5, F6)
            f2_grades = []
            f5_grades = []
            f6_grades = []
            other_grades = []
            
            for student in self.grades_data:
                # Get the raw grade (may be None if not submitted)
                grade = student['grades'].get(assignment)

                # Determine which class section this student belongs to (None -> Other)
                student_section = self.get_student_section(student['name'])

                # Use empty string for missing grades so the student appears on the exported roster
                display_grade = grade if grade is not None else ""

                if student_section == 'F2':
                    f2_grades.append((student['name'], display_grade))
                elif student_section == 'F5':
                    f5_grades.append((student['name'], display_grade))
                elif student_section == 'F6':
                    f6_grades.append((student['name'], display_grade))
                else:
                    other_grades.append((student['name'], display_grade))
            
            # Sort each section by last name
            f2_grades.sort(key=lambda x: self.get_last_name(x[0]))
            f5_grades.sort(key=lambda x: self.get_last_name(x[0]))
            f6_grades.sort(key=lambda x: self.get_last_name(x[0]))
            other_grades.sort(key=lambda x: self.get_last_name(x[0]))
            
            # Export to Google Sheets
            try:
                self.status_var.set("Exporting to Google Sheets...")
                self.root.update()
                
                sheet_url = self.sheets_exporter.export_to_sheets(
                    assignment, f2_grades, f5_grades, f6_grades, other_grades
                )
                
                if sheet_url:
                    result = f"Successfully exported to Google Sheets!\n\n"
                    result += f"Assignment: {assignment}\n"
                    result += f"F2 students: {len(f2_grades)}\n"
                    result += f"F5 students: {len(f5_grades)}\n"
                    result += f"F6 students: {len(f6_grades)}\n"
                    result += f"Other students: {len(other_grades)}\n\n"
                    result += f"Google Sheet URL:\n{sheet_url}\n\n"
                    result += "Click the URL above to open your Google Sheet!"
                    
                    self.status_var.set("Export completed successfully")
                else:
                    result = "Failed to export to Google Sheets. Please check your credentials."
                    self.status_var.set("Export failed")
                
                self.display_result(result)
                
            except Exception as e:
                error_msg = f"Error exporting to Google Sheets: {str(e)}"
                messagebox.showerror("Export Error", error_msg)
                self.status_var.set("Export failed")

    def export_subchapter_to_sheets(self):
        """Menu option 5: Export all assignments for a sub-chapter (e.g., 1.4) to Google Sheets
        Each section (F2, F5, F6, Other) gets its own worksheet. The worksheet columns are:
        Last Name | First Name | <subchapter Lesson Practice> | <subchapter Code Practice Q1> | Q2 | Q3 ...
        """
        # Build a list of unique sub-chapter prefixes from assignments (token before first space)
        prefixes = []
        for a in self.assignments:
            tok = a.strip().split()[0] if a.strip() else ''
            if tok and tok not in prefixes:
                prefixes.append(tok)

        dialog = SubChapterDialog(self.root, prefixes)
        self.root.wait_window(dialog.dialog)

        if not dialog.result:
            return

        subchapter = dialog.result.strip()

        # Find matching assignments for the chosen prefix
        matching = [a for a in self.assignments if a.strip().startswith(subchapter)]

        if not matching:
            messagebox.showinfo("No assignments", f"No assignments found for sub-chapter {subchapter}")
            return

        # Build per-section data with split: {'F2': {'submitted': [...], 'not_submitted': [...]}, ...}
        sections = {k: {'submitted': [], 'not_submitted': []} for k in ['F2', 'F5', 'F6', 'Other']}

        for student in self.grades_data:
            section = self.get_student_section(student['name']) or 'Other'

            # Parse names
            if ',' in student['name']:
                parts = student['name'].split(', ')
                last = parts[0].strip() if parts else ''
                first = parts[1].strip() if len(parts) > 1 else ''
            else:
                parts = student['name'].split()
                first = parts[0].strip() if parts else ''
                last = parts[-1].strip() if len(parts) > 1 else ''

            # Build base row [Last, First]
            base = [last, first]

            # Build row of grades for matching assignments
            grade_row = []
            any_submitted = False
            for a in matching:
                g = student['grades'].get(a)
                if g is not None:
                    any_submitted = True
                    grade_row.append(g)
                else:
                    grade_row.append("")

            full_row = base + grade_row

            key = section if section in ['F2', 'F5', 'F6'] else 'Other'
            if any_submitted:
                sections[key]['submitted'].append(full_row)
            else:
                sections[key]['not_submitted'].append(full_row)

        # Call exporter
        try:
            self.status_var.set("Exporting subchapter to Google Sheets...")
            self.root.update()

            sheet_url = self.sheets_exporter.export_subchapter_to_sheets(subchapter, matching, sections)

            if sheet_url:
                result = f"Successfully exported sub-chapter {subchapter} to Google Sheets:\n{sheet_url}\n"
                result += "\nLegend: blank cell = no submission"
                self.status_var.set("Export completed successfully")
            else:
                result = "Failed to export sub-chapter to Google Sheets."
                self.status_var.set("Export failed")

            self.display_result(result)

        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting sub-chapter: {str(e)}")
            self.status_var.set("Export failed")
    
    def get_student_section(self, student_name):
        """Determine which class section (F2, F5, F6) a student belongs to"""
        # Convert "Last, First" format to "First Last" for comparison
        if ',' in student_name:
            parts = student_name.split(', ')
            if len(parts) == 2:
                display_name = f"{parts[1]} {parts[0]}"
            else:
                display_name = student_name
        else:
            display_name = student_name
        
        # Check each section with flexible matching
        for section, names in self.student_names.items():
            for name in names:
                # Try exact match first
                if self.normalize_name(display_name) == self.normalize_name(name):
                    return section
                
                # Try flexible matching for names like "Riley Sky Mantaring" vs "Mantaring, Riley"
                display_parts = self.normalize_name(display_name).split()
                name_parts = self.normalize_name(name).split()
                
                if len(display_parts) >= 2 and len(name_parts) >= 2:
                    # Check if first and last names match, ignoring middle names
                    display_first_last = {display_parts[0], display_parts[-1]}
                    name_first_last = {name_parts[0], name_parts[-1]}
                    
                    if display_first_last == name_first_last:
                        return section
        
        return None  # Not found in any section
    
    def format_display_name(self, student_name):
        """Convert 'Last, First' format to 'First Last' for display"""
        if ',' in student_name:
            parts = student_name.split(', ')
            if len(parts) == 2:
                return f"{parts[1]} {parts[0]}"
        return student_name
    
    def get_last_name(self, student_name):
        """Extract last name for sorting purposes"""
        if ',' in student_name:
            # Format: "Last, First" - last name is the first part
            parts = student_name.split(', ')
            if len(parts) >= 1:
                return parts[0].strip().lower()
        else:
            # Format: "First Last" - last name is the last part
            parts = student_name.split()
            if len(parts) >= 2:
                return parts[-1].strip().lower()
        return student_name.strip().lower()
    
    def format_csv_name(self, student_name, grade):
        """Format student name and grade as CSV: Last name, First name, Grade"""
        if ',' in student_name:
            # Format: "Last, First" - already in correct order
            parts = student_name.split(', ')
            if len(parts) >= 2:
                last_name = parts[0].strip()
                first_name = parts[1].strip()
                return f"{last_name},{first_name},{grade}"
            else:
                return f"{student_name},{grade}"
        else:
            # Format: "First Last" - need to split and reorder
            parts = student_name.split()
            if len(parts) >= 2:
                first_name = parts[0].strip()
                last_name = parts[-1].strip()
                return f"{last_name},{first_name},{grade}"
            else:
                return f"{student_name},{grade}"
    
    def display_result(self, result):
        """Display result in the results text area and make URLs clickable."""
        import webbrowser

        # Clear existing content
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        # Pattern to find URLs
        url_re = re.compile(r"(https?://[\w\-._~:/?#[\]@!$&'()*+,;=%]+)")

        pos = 0
        for match in url_re.finditer(result):
            start, end = match.span()
            # Insert text before URL
            if start > pos:
                self.results_text.insert(tk.END, result[pos:start])

            url = match.group(0)
            tag_name = f"url_{start}_{end}"
            # Insert URL text with tag
            self.results_text.insert(tk.END, url, (tag_name,))

            # Configure tag appearance (blue underline) and bindings
            self.results_text.tag_config(tag_name, foreground="blue", underline=1)
            # On click, open in default browser
            self.results_text.tag_bind(tag_name, "<Button-1>", lambda e, u=url: webbrowser.open(u))
            # Change cursor on hover
            self.results_text.tag_bind(tag_name, "<Enter>", lambda e: self.results_text.config(cursor="hand2"))
            self.results_text.tag_bind(tag_name, "<Leave>", lambda e: self.results_text.config(cursor=""))

            pos = end

        # Insert remaining text after last URL
        if pos < len(result):
            self.results_text.insert(tk.END, result[pos:])

        # Ensure the widget is editable only programmatically
        self.results_text.config(state=tk.DISABLED)


class SpecificGradeDialog:
    def __init__(self, parent, students, assignments):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Find Specific Grade")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Student selection
        tk.Label(self.dialog, text="Select Student:", font=("Arial", 12, "bold")).pack(pady=10)
        
        self.student_var = tk.StringVar()
        student_combo = ttk.Combobox(self.dialog, textvariable=self.student_var, width=50)
        student_combo['values'] = students
        student_combo.pack(pady=5)
        
        # Assignment selection
        tk.Label(self.dialog, text="Select Assignment:", font=("Arial", 12, "bold")).pack(pady=10)
        
        self.assignment_var = tk.StringVar()
        assignment_combo = ttk.Combobox(self.dialog, textvariable=self.assignment_var, width=50)
        assignment_combo['values'] = assignments
        assignment_combo.pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Find Grade", command=self.ok_clicked, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked, width=15).pack(side=tk.LEFT, padx=5)
    
    def ok_clicked(self):
        if self.student_var.get() and self.assignment_var.get():
            self.result = (self.student_var.get(), self.assignment_var.get())
            self.dialog.destroy()
        else:
            messagebox.showwarning("Warning", "Please select both student and assignment")
    
    def cancel_clicked(self):
        self.dialog.destroy()


class StudentSelectionDialog:
    def __init__(self, parent, students):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Student")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        tk.Label(self.dialog, text="Select Student:", font=("Arial", 12, "bold")).pack(pady=20)
        
        self.student_var = tk.StringVar()
        student_combo = ttk.Combobox(self.dialog, textvariable=self.student_var, width=50)
        student_combo['values'] = students
        student_combo.pack(pady=10)
        
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked, width=15).pack(side=tk.LEFT, padx=5)
    
    def ok_clicked(self):
        if self.student_var.get():
            self.result = self.student_var.get()
            self.dialog.destroy()
        else:
            messagebox.showwarning("Warning", "Please select a student")
    
    def cancel_clicked(self):
        self.dialog.destroy()


class AssignmentSelectionDialog:
    def __init__(self, parent, assignments):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Assignment")
        self.dialog.geometry("500x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        tk.Label(self.dialog, text="Select Assignment:", font=("Arial", 12, "bold")).pack(pady=20)
        
        self.assignment_var = tk.StringVar()
        assignment_combo = ttk.Combobox(self.dialog, textvariable=self.assignment_var, width=60)
        assignment_combo['values'] = assignments
        assignment_combo.pack(pady=10)
        
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked, width=15).pack(side=tk.LEFT, padx=5)
    
    def ok_clicked(self):
        if self.assignment_var.get():
            self.result = self.assignment_var.get()
            self.dialog.destroy()
        else:
            messagebox.showwarning("Warning", "Please select an assignment")
    
    def cancel_clicked(self):
        self.dialog.destroy()


class SubChapterDialog:
    def __init__(self, parent, subchapter_choices):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Sub-chapter")
        self.dialog.geometry("360x160")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        tk.Label(self.dialog, text="Select sub-chapter:", font=("Arial", 12)).pack(pady=8)
        self.subchapter_var = tk.StringVar()
        combo = ttk.Combobox(self.dialog, textvariable=self.subchapter_var, values=subchapter_choices, width=20)
        combo.pack(pady=4)
        if subchapter_choices:
            combo.current(0)

        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="OK", command=self.ok_clicked, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked, width=10).pack(side=tk.LEFT, padx=5)

    def ok_clicked(self):
        val = self.subchapter_var.get().strip()
        if val:
            self.result = val
            self.dialog.destroy()
        else:
            messagebox.showwarning("Warning", "Please select a sub-chapter")

    def cancel_clicked(self):
        self.dialog.destroy()


def main():
    root = tk.Tk()
    app = StudentGradesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
