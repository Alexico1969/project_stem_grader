#!/usr/bin/env python3
"""
Google Sheets Integration Module
Handles authentication and data export to Google Sheets
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import tkinter as tk
from tkinter import messagebox

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GoogleSheetsExporter:
    def __init__(self):
        self.service = None
        self.authenticated = False
    
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        creds = None
        # The file token.pickle stores the user's access and refresh tokens.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    messagebox.showerror("Error", 
                        "credentials.json file not found!\n\n"
                        "Please follow these steps:\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Create a new project or select existing one\n"
                        "3. Enable Google Sheets API\n"
                        "4. Create credentials (OAuth 2.0 Client ID)\n"
                        "5. Download the JSON file and rename it to 'credentials.json'\n"
                        "6. Place it in the same folder as this application")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('sheets', 'v4', credentials=creds)
            self.authenticated = True
            return True
        except Exception as e:
            messagebox.showerror("Authentication Error", f"Failed to authenticate: {str(e)}")
            return False
    
    def create_sheet_with_tabs(self, title):
        """Create a new Google Sheet with separate tabs for F2, F5, F6"""
        if not self.authenticated:
            if not self.authenticate():
                return None
        
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': [
                    {
                        'properties': {
                            'title': 'F2 Section',
                            'sheetId': 0
                        }
                    },
                    {
                        'properties': {
                            'title': 'F5 Section', 
                            'sheetId': 1
                        }
                    },
                    {
                        'properties': {
                            'title': 'F6 Section',
                            'sheetId': 2
                        }
                    },
                    {
                        'properties': {
                            'title': 'Other Students',
                            'sheetId': 3
                        }
                    }
                ]
            }
            
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            
            return spreadsheet.get('spreadsheetId')
        except HttpError as error:
            messagebox.showerror("Error", f"Failed to create sheet: {error}")
            return None
    
    def format_sheet_data(self, assignment_name, f2_grades, f5_grades, f6_grades, other_grades):
        """Format data for Google Sheets export"""
        data = []
        
        # Add header
        data.append([f"Assignment: {assignment_name}"])
        data.append([])  # Empty row
        
        # F2 Section
        if f2_grades:
            data.append(["F2 SECTION"])
            data.append(["Last Name", "First Name", "Grade"])
            for student_name, grade in f2_grades:
                if ',' in student_name:
                    parts = student_name.split(', ')
                    if len(parts) >= 2:
                        last_name = parts[0].strip()
                        first_name = parts[1].strip()
                        data.append([last_name, first_name, grade])
            data.append([])  # Empty row
        
        # F5 Section
        if f5_grades:
            data.append(["F5 SECTION"])
            data.append(["Last Name", "First Name", "Grade"])
            for student_name, grade in f5_grades:
                if ',' in student_name:
                    parts = student_name.split(', ')
                    if len(parts) >= 2:
                        last_name = parts[0].strip()
                        first_name = parts[1].strip()
                        data.append([last_name, first_name, grade])
            data.append([])  # Empty row
        
        # F6 Section
        if f6_grades:
            data.append(["F6 SECTION"])
            data.append(["Last Name", "First Name", "Grade"])
            for student_name, grade in f6_grades:
                if ',' in student_name:
                    parts = student_name.split(', ')
                    if len(parts) >= 2:
                        last_name = parts[0].strip()
                        first_name = parts[1].strip()
                        data.append([last_name, first_name, grade])
            data.append([])  # Empty row
        
        # Other students
        if other_grades:
            data.append(["OTHER STUDENTS"])
            data.append(["Last Name", "First Name", "Grade"])
            for student_name, grade in other_grades:
                if ',' in student_name:
                    parts = student_name.split(', ')
                    if len(parts) >= 2:
                        last_name = parts[0].strip()
                        first_name = parts[1].strip()
                        data.append([last_name, first_name, grade])
        
        return data
    
    def export_to_sheets(self, assignment_name, f2_grades, f5_grades, f6_grades, other_grades):
        """Export assignment grades to Google Sheets with separate tabs"""
        if not self.authenticated:
            if not self.authenticate():
                return None
        
        # Create new sheet with tabs
        sheet_title = f"Assignment Grades - {assignment_name}"
        spreadsheet_id = self.create_sheet_with_tabs(sheet_title)
        
        if not spreadsheet_id:
            return None
        
        try:
            # Write data to each sheet tab
            self.write_section_data(spreadsheet_id, 'F2 Section', f2_grades, assignment_name)
            self.write_section_data(spreadsheet_id, 'F5 Section', f5_grades, assignment_name)
            self.write_section_data(spreadsheet_id, 'F6 Section', f6_grades, assignment_name)
            self.write_section_data(spreadsheet_id, 'Other Students', other_grades, assignment_name)
            
            # Format all sheets
            self.format_all_sheets(spreadsheet_id)
            
            # Get the sheet URL
            sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            
            return sheet_url
            
        except HttpError as error:
            messagebox.showerror("Error", f"Failed to write data: {error}")
            return None
    
    def format_sheet(self, spreadsheet_id):
        """Apply formatting to the Google Sheet"""
        try:
            requests = []
            
            # Format headers (bold)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True,
                                'fontSize': 14
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.textFormat'
                }
            })
            
            # Format section headers (bold, background color)
            for i in range(0, 100):  # Check first 100 rows for section headers
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': i,
                            'endRowIndex': i + 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'red': 0.9,
                                    'green': 0.9,
                                    'blue': 0.9
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat,userEnteredFormat.backgroundColor'
                    }
                })
            
            # Auto-resize columns
            requests.append({
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 3
                    }
                }
            })
            
            # Apply formatting
            body = {
                'requests': requests
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
        except HttpError as error:
            print(f"Formatting error (non-critical): {error}")
    
    def write_section_data(self, spreadsheet_id, sheet_name, grades_data, assignment_name):
        """Write data to a specific sheet tab"""
        if not grades_data:
            return
        
        # Format data for this section
        data = []
        data.append([f"Assignment: {assignment_name}"])
        data.append([f"Section: {sheet_name}"])
        data.append([])  # Empty row
        data.append(["Last Name", "First Name", "Grade"])
        
        for student_name, grade in grades_data:
            if ',' in student_name:
                parts = student_name.split(', ')
                if len(parts) >= 2:
                    last_name = parts[0].strip()
                    first_name = parts[1].strip()
                    data.append([last_name, first_name, grade])
        
        # Write data to the specific sheet
        body = {
            'values': data
        }
        
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption='RAW',
            body=body
        ).execute()

    def write_section_multi_columns(self, spreadsheet_id, sheet_name, header_assignments, rows):
        """Write data to a specific sheet tab where rows already contain [Last, First, grade1, grade2, ...]
        header_assignments is a list of assignment column headers (strings)"""
        if not rows:
            return

        data = []
        data.append([f"Sub-chapter export"])  # Title row
        data.append([f"Section: {sheet_name}"])
        data.append([])

        # Column headers: Last Name, First Name, then each assignment, then Total
        header = ["Last Name", "First Name"] + header_assignments + ["Total"]
        data.append(header)

        # Append all rows (assumed already in Last, First, grade1... order)
        for r in rows:
            # compute total for the grade columns (elements after first two)
            try:
                grades = r[2:]
            except Exception:
                grades = []
            total = 0.0
            for g in grades:
                try:
                    # allow numeric values or numeric strings
                    total += float(g)
                except Exception:
                    # ignore blanks or non-numeric
                    continue
            new_row = list(r) + [total]
            data.append(new_row)

        body = {'values': data}

        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption='RAW',
            body=body
        ).execute()

    def export_subchapter_to_sheets(self, subchapter, assignments, sections_dict):
        """Export multiple assignments (assignments list) organized by section (sections_dict)
        sections_dict should be a dict: {'F2': [[last,first,g1,g2...], ...], 'F5': [...], 'F6': [...], 'Other': [...]}"""
        if not self.authenticated:
            if not self.authenticate():
                return None

        sheet_title = f"Subchapter {subchapter} Grades"
        spreadsheet_id = self.create_sheet_with_tabs(sheet_title)
        if not spreadsheet_id:
            return None

        try:
            # Write each section using the split writer (submitted / not_submitted)
            self.write_section_split(spreadsheet_id, 'F2 Section', assignments, sections_dict.get('F2', {'submitted': [], 'not_submitted': []}))
            self.write_section_split(spreadsheet_id, 'F5 Section', assignments, sections_dict.get('F5', {'submitted': [], 'not_submitted': []}))
            self.write_section_split(spreadsheet_id, 'F6 Section', assignments, sections_dict.get('F6', {'submitted': [], 'not_submitted': []}))
            self.write_section_split(spreadsheet_id, 'Other Students', assignments, sections_dict.get('Other', {'submitted': [], 'not_submitted': []}))

            # Try to apply formatting for these sheets (auto-resize columns etc.)
            self.format_all_sheets(spreadsheet_id)

            sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            return sheet_url

        except HttpError as error:
            messagebox.showerror("Error", f"Failed to write subchapter data: {error}")
            return None

    def write_section_split(self, spreadsheet_id, sheet_name, header_assignments, section_data):
        """Write a sheet with a legend and two blocks: Submitted and Not submitted.
        section_data is a dict {'submitted': [rows], 'not_submitted': [rows]}"""
        submitted = section_data.get('submitted', [])
        not_sub = section_data.get('not_submitted', [])

        data = []
        data.append([f"Sub-chapter: {header_assignments[0].split()[0] if header_assignments else ''}"])
        data.append([f"Section: {sheet_name}"])
        data.append(["Legend:", "Blank cell = no submission"])
        data.append([])

        # Submitted block
        data.append(["Submitted"])
        header = ["Last Name", "First Name"] + header_assignments + ["Total"]
        data.append(header)
        for r in submitted:
            # compute total for the grade columns (elements after first two)
            grades = r[2:]
            total = 0.0
            for g in grades:
                try:
                    total += float(g)
                except Exception:
                    continue
            data.append(list(r) + [total])

        data.append([])

        # Not submitted block
        data.append(["Not submitted"])
        data.append(header)
        for r in not_sub:
            grades = r[2:]
            total = 0.0
            for g in grades:
                try:
                    total += float(g)
                except Exception:
                    continue
            data.append(list(r) + [total])

        body = {'values': data}

        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption='RAW',
            body=body
        ).execute()
    
    def format_all_sheets(self, spreadsheet_id):
        """Apply formatting to all sheets in the spreadsheet"""
        try:
            requests = []
            
            # Format each sheet
            sheet_names = ['F2 Section', 'F5 Section', 'F6 Section', 'Other Students']
            
            for sheet_name in sheet_names:
                # Format headers (bold, larger font)
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_names.index(sheet_name),
                            'startRowIndex': 0,
                            'endRowIndex': 4  # First 4 rows (title, section, empty, headers)
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True,
                                    'fontSize': 12
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat'
                    }
                })
                
                # Format column headers (bold, background color)
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_names.index(sheet_name),
                            'startRowIndex': 3,
                            'endRowIndex': 4
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'red': 0.9,
                                    'green': 0.9,
                                    'blue': 0.9
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat,userEnteredFormat.backgroundColor'
                    }
                })
                
                # Auto-resize columns
                requests.append({
                    'autoResizeDimensions': {
                        'dimensions': {
                            'sheetId': sheet_names.index(sheet_name),
                            'dimension': 'COLUMNS',
                            'startIndex': 0,
                            'endIndex': 3
                        }
                    }
                })
            
            # Apply all formatting
            if requests:
                body = {
                    'requests': requests
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=body
                ).execute()
                
        except HttpError as error:
            print(f"Formatting error (non-critical): {error}")
