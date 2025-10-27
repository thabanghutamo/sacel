"""
Language and Localization Service for SACEL Platform
Handles language detection, switching, and localization support
"""

from flask import session, request, current_app
from flask_babel import get_locale
from app.extensions import babel


class LanguageService:
    """Service for managing user language preferences and localization"""
    
    @staticmethod
    def get_supported_languages():
        """Get dictionary of supported languages"""
        return current_app.config.get('LANGUAGES', {'en': 'English'})
    
    @staticmethod
    def get_language_choices():
        """Get language choices for forms"""
        languages = LanguageService.get_supported_languages()
        return [(code, name) for code, name in languages.items()]
    
    @staticmethod
    def get_current_language():
        """Get current user's selected language"""
        return session.get('language', current_app.config.get('BABEL_DEFAULT_LOCALE', 'en'))
    
    @staticmethod
    def set_language(language_code):
        """Set user's language preference"""
        supported = LanguageService.get_supported_languages()
        if language_code in supported:
            session['language'] = language_code
            return True
        return False
    
    @staticmethod
    def detect_language():
        """Detect user's preferred language from browser or session"""
        # Check session first
        if 'language' in session:
            return session['language']
        
        # Check browser Accept-Language header
        supported_codes = list(LanguageService.get_supported_languages().keys())
        return request.accept_languages.best_match(supported_codes) or 'en'
    
    @staticmethod
    def get_language_name(code):
        """Get display name for language code"""
        languages = LanguageService.get_supported_languages()
        return languages.get(code, code.upper())
    
    @staticmethod
    def is_rtl_language(code):
        """Check if language is right-to-left"""
        rtl_languages = ['ar', 'he', 'fa', 'ur']  # None of SA languages are RTL
        return code in rtl_languages


def get_locale():
    """Babel locale selector function"""
    # Check if user manually selected a language
    if 'language' in session:
        return session['language']
    
    # Detect from browser
    return LanguageService.detect_language()


# Language mapping for AI content generation
AI_LANGUAGE_MAPPING = {
    'en': 'English',
    'af': 'Afrikaans',
    'zu': 'IsiZulu', 
    'xh': 'IsiXhosa',
    'st': 'Sesotho',
    'tn': 'Setswana',
    'ss': 'SiSwati',
    've': 'Tshivenda',
    'ts': 'Xitsonga',
    'nr': 'IsiNdebele',
    'nso': 'Sepedi'
}

# Common educational terms translation mapping
EDUCATION_TERMS = {
    'en': {
        # Basic Education Terms
        'assignment': 'Assignment',
        'teacher': 'Teacher',
        'student': 'Student',
        'grade': 'Grade',
        'subject': 'Subject',
        'homework': 'Homework',
        'test': 'Test',
        'exam': 'Exam',
        'lesson': 'Lesson',
        'school': 'School',
        'principal': 'Principal',
        'classroom': 'Classroom',
        
        # Action Words
        'submit': 'Submit',
        'complete': 'Complete',
        'pending': 'Pending',
        'approved': 'Approved',
        'rejected': 'Rejected',
        'save': 'Save',
        'cancel': 'Cancel',
        'edit': 'Edit',
        'delete': 'Delete',
        'view': 'View',
        'add': 'Add',
        'create': 'Create',
        'update': 'Update',
        'search': 'Search',
        'filter': 'Filter',
        'download': 'Download',
        'upload': 'Upload',
        
        # Navigation & UI
        'dashboard': 'Dashboard',
        'profile': 'Profile',
        'settings': 'Settings',
        'logout': 'Logout',
        'login': 'Login',
        'home': 'Home',
        'back': 'Back',
        'next': 'Next',
        'previous': 'Previous',
        'menu': 'Menu',
        'close': 'Close',
        'open': 'Open',
        
        # Application Management
        'applications': 'Applications',
        'application': 'Application',
        'admissions': 'Admissions',
        'enrollment': 'Enrollment',
        'registration': 'Registration',
        'apply': 'Apply',
        'review': 'Review',
        'approve': 'Approve',
        'reject': 'Reject',
        'status': 'Status',
        'reference': 'Reference',
        'documents': 'Documents',
        
        # Analytics & Reports
        'analytics': 'Analytics',
        'reports': 'Reports',
        'statistics': 'Statistics',
        'metrics': 'Metrics',
        'total': 'Total',
        'count': 'Count',
        'percentage': 'Percentage',
        'overview': 'Overview',
        'summary': 'Summary',
        
        # User Information
        'name': 'Name',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'email': 'Email',
        'phone': 'Phone',
        'address': 'Address',
        'date': 'Date',
        'time': 'Time',
        'age': 'Age',
        'gender': 'Gender',
        
        # Messages & Notifications
        'success': 'Success',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Information',
        'message': 'Message',
        'notification': 'Notification',
        'alert': 'Alert',
        'confirm': 'Confirm',
        'welcome': 'Welcome',
        'thank_you': 'Thank You',
        
        # Common Phrases
        'please_wait': 'Please wait',
        'loading': 'Loading',
        'no_data': 'No data available',
        'select_option': 'Select an option',
        'required_field': 'This field is required',
        'invalid_format': 'Invalid format',
        'access_denied': 'Access denied',
        'page_not_found': 'Page not found',
        
        # Admin Terms
        'admin': 'Admin',
        'administrator': 'Administrator',
        'system_administrator': 'System Administrator',
        'school_administrator': 'School Administrator',
        
        # Student Assignment Interface
        'my_assignments': 'My Assignments',
        'assignments_overview': 'Assignments Overview',
        'due_soon': 'Due Soon',
        'overdue': 'Overdue',
        'completed': 'Completed',
        'progress': 'Progress',
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'due_date': 'Due Date',
        'difficulty': 'Difficulty',
        'submit_assignment': 'Submit Assignment',
        'questions': 'Questions',
        'time_remaining': 'Time Remaining',
        'auto_save': 'Auto Save',
        'ai_help': 'AI Help',
        'ask_ai': 'Ask AI',
        'submit_confirmation': 'Submit Confirmation',
        'assignment_submitted': 'Assignment Submitted',
        'submission_successful': 'Submission Successful',
        'file_upload': 'File Upload',
        'drag_drop_files': 'Drag and drop files here',
        'browse_files': 'Browse Files',
        'selected_files': 'Selected Files',
        'remove_file': 'Remove File',
        'show_instructions': 'Show Instructions',
        'hide_instructions': 'Hide Instructions',
        'easy': 'Easy',
        'medium': 'Medium',
        'hard': 'Hard',
        'expert': 'Expert',
        'not_started': 'Not Started',
        'in_progress': 'In Progress',
        'submitted': 'Submitted',
        'graded': 'Graded',
        'question_help': 'Question Help',
        'get_hint': 'Get Hint',
        'explain_topic': 'Explain Topic',
        'check_answer': 'Check Answer',
        'final_submission': 'Final Submission',
        'confirm_submit': 'Confirm Submit',
        'cannot_undo': 'This action cannot be undone',
        'yes_submit': 'Yes, Submit',
        'keep_working': 'Keep Working',
        'saved_successfully': 'Saved Successfully',
        'saving': 'Saving',
        'question_number': 'Question',
        'of': 'of',
        'points': 'Points',
        'total_points': 'Total Points',
        'your_answer': 'Your Answer',
        'answer_required': 'Answer Required',
        'timer': 'Timer',
        'hours': 'Hours',
        'minutes': 'Minutes',
        'seconds': 'Seconds',
        'time_up': 'Time Up',
        'assignment_description': 'Assignment Description',
        'instructions': 'Instructions',
        'resources': 'Resources',
        'submission_details': 'Submission Details'
    },
    'af': {
        # Basic Education Terms
        'assignment': 'Opdrag',
        'teacher': 'Onderwyser',
        'student': 'Student',
        'grade': 'Graad',
        'subject': 'Vak',
        'homework': 'Huiswerk',
        'test': 'Toets',
        'exam': 'Eksamen',
        'lesson': 'Les',
        'school': 'Skool',
        'principal': 'Skoolhoof',
        'classroom': 'Klaskamer',
        
        # Action Words
        'submit': 'Indien',
        'complete': 'Voltooi',
        'pending': 'Hangende',
        'approved': 'Goedgekeur',
        'rejected': 'Verwerp',
        'save': 'Stoor',
        'cancel': 'Kanselleer',
        'edit': 'Wysig',
        'delete': 'Skrap',
        'view': 'Bekyk',
        'add': 'Voeg by',
        'create': 'Skep',
        'update': 'Opdateer',
        'search': 'Soek',
        'filter': 'Filter',
        'download': 'Aflaai',
        'upload': 'Oplaai',
        
        # Navigation & UI
        'dashboard': 'Instrumentebord',
        'profile': 'Profiel',
        'settings': 'Instellings',
        'logout': 'Teken uit',
        'login': 'Teken in',
        'home': 'Tuis',
        'back': 'Terug',
        'next': 'Volgende',
        'previous': 'Vorige',
        'menu': 'Kieslys',
        'close': 'Sluit',
        'open': 'Maak oop',
        
        # Application Management
        'applications': 'Aansoeke',
        'application': 'Aansoek',
        'admissions': 'Toelating',
        'enrollment': 'Inskrywing',
        'registration': 'Registrasie',
        'apply': 'Aansoek doen',
        'review': 'Hersien',
        'approve': 'Keur goed',
        'reject': 'Verwerp',
        'status': 'Status',
        'reference': 'Verwysing',
        'documents': 'Dokumente',
        
        # Analytics & Reports
        'analytics': 'Analise',
        'reports': 'Verslae',
        'statistics': 'Statistieke',
        'metrics': 'Metrieke',
        'total': 'Totaal',
        'count': 'Tel',
        'percentage': 'Persentasie',
        'overview': 'Oorsig',
        'summary': 'Opsomming',
        
        # User Information
        'name': 'Naam',
        'first_name': 'Voornaam',
        'last_name': 'Van',
        'email': 'E-pos',
        'phone': 'Telefoon',
        'address': 'Adres',
        'date': 'Datum',
        'time': 'Tyd',
        'age': 'Ouderdom',
        'gender': 'Geslag',
        
        # Messages & Notifications
        'success': 'Sukses',
        'error': 'Fout',
        'warning': 'Waarskuwing',
        'info': 'Inligting',
        'message': 'Boodskap',
        'notification': 'Kennisgewing',
        'alert': 'Waarskuwing',
        'confirm': 'Bevestig',
        'welcome': 'Welkom',
        'thank_you': 'Dankie',
        
        # Common Phrases
        'please_wait': 'Wag asseblief',
        'loading': 'Laai',
        'no_data': 'Geen data beskikbaar nie',
        'select_option': 'Kies \'n opsie',
        'required_field': 'Hierdie veld is verplig',
        'invalid_format': 'Ongeldige formaat',
        'access_denied': 'Toegang geweier',
        'page_not_found': 'Bladsy nie gevind nie',
        
        # Admin Terms
        'admin': 'Admin',
        'administrator': 'Administrateur',
        'system_administrator': 'Stelsel Administrateur',
        'school_administrator': 'Skool Administrateur',
        
        # Student Assignment Interface
        'my_assignments': 'My Opdragte',
        'assignments_overview': 'Opdragte Oorsig',
        'due_soon': 'Binnekort Verskuldig',
        'overdue': 'Oorverskuldig',
        'completed': 'Voltooi',
        'progress': 'Vordering',
        'start_date': 'Begin Datum',
        'end_date': 'Eind Datum',
        'due_date': 'Skuld Datum',
        'difficulty': 'Moeilikheidsgraad',
        'submit_assignment': 'Dien Opdrag In',
        'questions': 'Vrae',
        'time_remaining': 'Tyd Oor',
        'auto_save': 'Outomatiese Stoor',
        'ai_help': 'KI Hulp',
        'ask_ai': 'Vra KI',
        'submit_confirmation': 'Indiening Bevestiging',
        'assignment_submitted': 'Opdrag Ingedien',
        'submission_successful': 'Indiening Suksesvol',
        'file_upload': 'Lêer Oplaai',
        'drag_drop_files': 'Sleep en los lêers hier',
        'browse_files': 'Blaai Lêers',
        'selected_files': 'Gekose Lêers',
        'remove_file': 'Verwyder Lêer',
        'show_instructions': 'Toon Instruksies',
        'hide_instructions': 'Versteek Instruksies',
        'easy': 'Maklik',
        'medium': 'Medium',
        'hard': 'Moeilik',
        'expert': 'Kundige',
        'not_started': 'Nie Begin Nie',
        'in_progress': 'Besig',
        'submitted': 'Ingedien',
        'graded': 'Gegradeer',
        'question_help': 'Vraag Hulp',
        'get_hint': 'Kry Wenk',
        'explain_topic': 'Verduidelik Onderwerp',
        'check_answer': 'Kontroleer Antwoord',
        'final_submission': 'Finale Indiening',
        'confirm_submit': 'Bevestig Indiening',
        'cannot_undo': 'Hierdie aksie kan nie ongedaan gemaak word nie',
        'yes_submit': 'Ja, Dien In',
        'keep_working': 'Hou Aan Werk',
        'saved_successfully': 'Suksesvol Gestoor',
        'saving': 'Stoor',
        'question_number': 'Vraag',
        'of': 'van',
        'points': 'Punte',
        'total_points': 'Totale Punte',
        'your_answer': 'Jou Antwoord',
        'answer_required': 'Antwoord Vereis',
        'timer': 'Tydhouer',
        'hours': 'Ure',
        'minutes': 'Minute',
        'seconds': 'Sekondes',
        'time_up': 'Tyd Op',
        'assignment_description': 'Opdrag Beskrywing',
        'instructions': 'Instruksies',
        'resources': 'Hulpbronne',
        'submission_details': 'Indiening Besonderhede'
    },
    'zu': {
        'assignment': 'Umsebenzi',
        'teacher': 'Uthisha',
        'student': 'Umfundi',
        'grade': 'Ibanga',
        'subject': 'Isifundo',
        'homework': 'Umsebenzi wasekhaya',
        'test': 'Isivivinyo',
        'exam': 'Uvivinyo',
        'lesson': 'Isifundo',
        'school': 'Isikole',
        'principal': 'Unhloko wesikole',
        'classroom': 'Igumbi lokufundisa',
        'submit': 'Thumela',
        'complete': 'Qeda',
        'pending': 'Kulinde',
        'approved': 'Kuvunyiwe',
        'rejected': 'Kwenqatshelwe',
        'dashboard': 'Ibhodi lokusebenza',
        'profile': 'Iphrofayela',
        'settings': 'Izilungiselelo',
        'logout': 'Phuma',
        'login': 'Ngena',
        
        # Student Assignment Interface
        'my_assignments': 'Imisebenzi Yami',
        'assignments_overview': 'Ukubuka Imisebenzi',
        'due_soon': 'Kufanele Maduze',
        'overdue': 'Kufanele Kudlule',
        'completed': 'Kuqediwe',
        'progress': 'Inqubekelaphambili',
        'start_date': 'Usuku Lokuqala',
        'end_date': 'Usuku Lokugcina',
        'due_date': 'Usuku Okufanele',
        'difficulty': 'Ubunzima',
        'submit_assignment': 'Thumela Umsebenzi',
        'questions': 'Imibuzo',
        'time_remaining': 'Isikhathi Esisele',
        'auto_save': 'Ukugcina Ngokuzenzekela',
        'ai_help': 'Usizo Lwe-AI',
        'ask_ai': 'Buza I-AI',
        'submit_confirmation': 'Ukuqinisekisa Ukuthumela',
        'assignment_submitted': 'Umsebenzi Uthunyelwe',
        'submission_successful': 'Ukuthumela Kuphumelele',
        'file_upload': 'Ukulayisha Ifayela',
        'drag_drop_files': 'Hudula bese ubeka amafayela lapha',
        'browse_files': 'Phendla Amafayela',
        'selected_files': 'Amafayela Akhethiwe',
        'remove_file': 'Susa Ifayela',
        'show_instructions': 'Bonisa Imiyalelo',
        'hide_instructions': 'Fihla Imiyalelo',
        'easy': 'Kulula',
        'medium': 'Phakathi',
        'hard': 'Kunzima',
        'expert': 'Uchwepheshe',
        'not_started': 'Akuzange Kuqale',
        'in_progress': 'Kuyaqhubeka',
        'submitted': 'Kuthunyelwe',
        'graded': 'Kumangiwe',
        'question_help': 'Usizo Lombuzo',
        'get_hint': 'Thola Iphakamiso',
        'explain_topic': 'Chaza Isihloko',
        'check_answer': 'Hlola Impendulo',
        'final_submission': 'Ukuthumela Kokugcina',
        'confirm_submit': 'Qinisekisa Ukuthumela',
        'cannot_undo': 'Lokhu akukwazi ukwenziwa kabusha',
        'yes_submit': 'Yebo, Thumela',
        'keep_working': 'Qhubeka Usebenza',
        'saved_successfully': 'Kugcinwe Ngempumelelo',
        'saving': 'Kuyagcinwa',
        'question_number': 'Umbuzo',
        'of': 'kuka',
        'points': 'Amaphuzu',
        'total_points': 'Amaphuzu Aphelele',
        'your_answer': 'Impendulo Yakho',
        'answer_required': 'Impendulo Iyadingeka',
        'timer': 'Isibali Sikhathi',
        'hours': 'Amahora',
        'minutes': 'Amaminithi',
        'seconds': 'Ama-sekendi',
        'time_up': 'Isikhathi Siphelile',
        'assignment_description': 'Incazelo Yomsebenzi',
        'instructions': 'Imiyalelo',
        'resources': 'Izinsiza',
        'submission_details': 'Imininingwane Yokuthumela'
    },
    'xh': {
        'assignment': 'Umsebenzi',
        'teacher': 'Utitshala',
        'student': 'Umfundi',
        'grade': 'Ibanga',
        'subject': 'Isifundo',
        'homework': 'Umsebenzi wasekhaya',
        'test': 'Uvavanyo',
        'exam': 'Uvivinyo',
        'lesson': 'Isifundo',
        'school': 'Isikolo',
        'principal': 'Inqununu yesikolo',
        'classroom': 'Igumbi lokufundisa',
        'submit': 'Ngenisa',
        'complete': 'Gqiba',
        'pending': 'Kulindwe',
        'approved': 'Yamkelwe',
        'rejected': 'Yaliwe',
        'dashboard': 'Ibhodi yolawulo',
        'profile': 'Iprofayile',
        'settings': 'Imilungiselelo',
        'logout': 'Phuma',
        'login': 'Ngena',
        
        # Student Assignment Interface
        'my_assignments': 'Imisebenzi Yam',
        'assignments_overview': 'Ukujonga Imisebenzi',
        'due_soon': 'Kufuneka Masinyane',
        'overdue': 'Kufuneka Kudlule',
        'completed': 'Kugqityiwe',
        'progress': 'Inkqubela',
        'start_date': 'Umhla Wokuqala',
        'end_date': 'Umhla Wokugqibela',
        'due_date': 'Umhla Ekufuneka',
        'difficulty': 'Ubunzima',
        'submit_assignment': 'Ngenisa Umsebenzi',
        'questions': 'Imibuzo',
        'time_remaining': 'Ixesha Elisele',
        'auto_save': 'Ukugcina Ngokuzenzekelayo',
        'ai_help': 'Uncedo Lwe-AI',
        'ask_ai': 'Buza I-AI',
        'submit_confirmation': 'Ukuqinisekisa Ukufaka',
        'assignment_submitted': 'Umsebenzi Ufakiwe',
        'submission_successful': 'Ukufaka Kuphumelele',
        'file_upload': 'Ukufaka Ifayile',
        'drag_drop_files': 'Tsala uze ubeke iifayile apha',
        'browse_files': 'Khangela Iifayile',
        'selected_files': 'Iifayile Ezikhethiweyo',
        'remove_file': 'Susa Ifayile',
        'show_instructions': 'Bonisa Imiyalelo',
        'hide_instructions': 'Fihla Imiyalelo',
        'easy': 'Lula',
        'medium': 'Phakathi',
        'hard': 'Nzima',
        'expert': 'Ingcali',
        'not_started': 'Akuqaliwanga',
        'in_progress': 'Kuyaqhubeka',
        'submitted': 'Kufakiwe',
        'graded': 'Kumanqulwe',
        'question_help': 'Uncedo Lombuzo',
        'get_hint': 'Fumana Icebo',
        'explain_topic': 'Cacisa Isihloko',
        'check_answer': 'Khangela Impendulo',
        'final_submission': 'Ukufaka Kokugqibela',
        'confirm_submit': 'Qinisekisa Ukufaka',
        'cannot_undo': 'Oku akukwazi ukubuyiselwa',
        'yes_submit': 'Ewe, Faka',
        'keep_working': 'Qhubeka Usebenza',
        'saved_successfully': 'Kugcinwe Ngempumelelo',
        'saving': 'Kuyagcinwa',
        'question_number': 'Umbuzo',
        'of': 'wa',
        'points': 'Amanqaku',
        'total_points': 'Amanqaku Apheleleyo',
        'your_answer': 'Impendulo Yakho',
        'answer_required': 'Impendulo Iyafuneka',
        'timer': 'Isibali Sexesha',
        'hours': 'Iiyure',
        'minutes': 'Imizuzu',
        'seconds': 'Imizuzwana',
        'time_up': 'Ixesha Liphelile',
        'assignment_description': 'Inkcazo Yomsebenzi',
        'instructions': 'Imiyalelo',
        'resources': 'Izibonelelo',
        'submission_details': 'Iinkcukacha Zokufaka'
    },
    'st': {
        'assignment': 'Mosebetsi',
        'teacher': 'Mosuwe',
        'student': 'Moithuti',
        'grade': 'Sehlopha',
        'subject': 'Thuto',
        'homework': 'Mosebetsi wa hae',
        'test': 'Tlhahlobo',
        'exam': 'Tlhahlobo e kgolo',
        'lesson': 'Thuto',
        'school': 'Sekolo',
        'principal': 'Modulasetulo wa sekolo',
        'classroom': 'Phaposi ya thuto',
        'submit': 'Romela',
        'complete': 'Qeta',
        'pending': 'E emetse',
        'approved': 'E amohelitswe',
        'rejected': 'E hanilwe',
        'dashboard': 'Boto ya taolo',
        'profile': 'Profaele',
        'settings': 'Ditokiso',
        'logout': 'Tswa',
        'login': 'Kena',
        
        # Student Assignment Interface
        'my_assignments': 'Mesebetsi ya Ka',
        'assignments_overview': 'Pono ya Mesebetsi',
        'due_soon': 'E tlameha haufinyane',
        'overdue': 'E feta nako',
        'completed': 'E qetilwe',
        'progress': 'Tsoelo-pele',
        'start_date': 'Letsatsi la qalo',
        'end_date': 'Letsatsi la qeto',
        'due_date': 'Letsatsi la pheletso',
        'difficulty': 'Bothata',
        'submit_assignment': 'Romela Mosebetsi',
        'questions': 'Dipotso',
        'time_remaining': 'Nako e saleng',
        'auto_save': 'Boloka ka ithuelo',
        'ai_help': 'Thuso ya AI',
        'ask_ai': 'Botsa AI',
        'submit_confirmation': 'Tiiso ya ho romela',
        'assignment_submitted': 'Mosebetsi o rometswe',
        'submission_successful': 'Ho romela ho atlehile',
        'file_upload': 'Ho kenya faele',
        'drag_drop_files': 'Hula o behele difaele mona',
        'browse_files': 'Batla Difaele',
        'selected_files': 'Difaele tse khethilweng',
        'remove_file': 'Tlosa Faele',
        'show_instructions': 'Bontsha ditaelo',
        'hide_instructions': 'Pata ditaelo',
        'easy': 'Bonolo',
        'medium': 'Mahareng',
        'hard': 'Thata',
        'expert': 'Setsebi',
        'not_started': 'Ha se qalile',
        'in_progress': 'E tsoela pele',
        'submitted': 'E rometswe',
        'graded': 'E fuwe manane',
        'question_help': 'Thuso ya potso',
        'get_hint': 'Fumana tlhahiso',
        'explain_topic': 'Hlalosa sehlooho',
        'check_answer': 'Hlahloba karabo',
        'final_submission': 'Ho romela ha qetello',
        'confirm_submit': 'Tiisa ho romela',
        'cannot_undo': 'Ha ho khone ho khutlisetswa',
        'yes_submit': 'Ee, Romela',
        'keep_working': 'Tsoela pele ho sebetsa',
        'saved_successfully': 'Ho bolokilwe ka katleho',
        'saving': 'Ho boloka',
        'question_number': 'Potso',
        'of': 'ya',
        'points': 'Dintlha',
        'total_points': 'Dintlha kaofela',
        'your_answer': 'Karabo ya hao',
        'answer_required': 'Karabo e hlokahala',
        'timer': 'Sesebali nako',
        'hours': 'Dihora',
        'minutes': 'Metsotso',
        'seconds': 'Metsotswana',
        'time_up': 'Nako e fedile',
        'assignment_description': 'Tlhaloso ya mosebetsi',
        'instructions': 'Ditaelo',
        'resources': 'Disebediswa',
        'submission_details': 'Lintlha tsa ho romela'
    }
}


def get_translated_term(term, language_code='en'):
    """Get translated educational term"""
    if language_code not in EDUCATION_TERMS:
        language_code = 'en'
    
    terms = EDUCATION_TERMS.get(language_code, EDUCATION_TERMS['en'])
    return terms.get(term, term.title())


# Alias for easier import
translate_term = get_translated_term


def get_ai_language_name(code):
    """Get language name for AI content generation"""
    return AI_LANGUAGE_MAPPING.get(code, 'English')


# Template helper functions
def register_language_helpers(app):
    """Register language helper functions for templates"""
    
    @app.template_global()
    def get_languages():
        """Template function to get available languages"""
        return LanguageService.get_supported_languages()
    
    @app.template_global()
    def current_language():
        """Template function to get current language"""
        return LanguageService.get_current_language()
    
    @app.template_global()
    def translate_term(term):
        """Template function to translate educational terms and content"""
        from app.services.content_service import get_content
        current_lang = LanguageService.get_current_language()
        
        # Try content service first, then education terms
        content = get_content(term, current_lang)
        if content != term.title().replace('_', ' '):
            return content
        
        # Fallback to education terms
        return get_translated_term(term, current_lang)
    
    @app.template_filter()
    def language_name(code):
        """Template filter to get language display name"""
        return LanguageService.get_language_name(code)