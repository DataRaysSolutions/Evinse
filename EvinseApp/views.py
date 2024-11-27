from django.db import connection, transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from datetime import datetime
import re
import os
from django.conf import settings
from django.utils.timezone import now
import math
import pandas as pd 
from .Evinse import read_files
from .Evinse import read_keywords_and_ids
from django.utils import timezone
from .Evinse import process_pdf_and_save_to_df
from django.http import FileResponse, Http404
from django.http import HttpResponse 
from pathlib import Path
from django.db import transaction, IntegrityError
from .highlight import get_pdf_directory
from .highlight import get_all_dbvalue
from .highlight import process_pdf_highlighting
from .highlight import save_and_open_temp_pdf
from django.http import JsonResponse
from urllib.parse import quote




def Signin(request):
    if request.method == 'POST':
        cUserName = request.POST['cUserName']
        cPassword = request.POST['cPassword']

        # Query to check if user exists in SignIn table with the provided username and password
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT nUserID 
                    FROM SignIn 
                    WHERE cUserName = %s AND cPassword = %s
                """, [cUserName, cPassword])

                user = cursor.fetchone()

                if user:
                    # Store nUserID in session
                    request.session['nUserID'] = user[0]
                    
                    # Redirect to project creation page upon successful login
                    return redirect('ProjectCreation')
                else:
                    # Add an error message if credentials are invalid
                    messages.error(request, 'Invalid username or password')

        except Exception as e:
            print(f"Database error: {e}")
            messages.error(request, 'There was an error processing your request. Please try again.')

    return render(request, 'Signin.html')

def Signup(request):
    if request.method == 'POST':
        # Get form data
        cUsername = request.POST.get('cUsername', '').strip()
        cEmail = request.POST.get('cEmail', '').strip()
        nMobile = request.POST.get('nMobile', '').strip()
        cPassword = request.POST.get('cPassword', '').strip()
        cConfirmPassword = request.POST.get('cConfirmPassword', '').strip()

        # Store form data to pass back to template
        form_data = {
            'cUsername': cUsername,
            'cEmail': cEmail,
            'nMobile': nMobile,
            'cPassword': cPassword,  
            'cConfirmPassword': cConfirmPassword, 
        }

        # Validation: Check required fields
        if not all([cUsername, cEmail, nMobile, cPassword, cConfirmPassword]):
            messages.error(request, 'All fields are required.')
            return render(request, 'Signup.html', {'form_data': form_data})

        # Validation: Username length
        if len(cUsername) < 3 or len(cUsername) > 50:
            messages.error(request, 'Username must be between 3 and 50 characters long.')
            return render(request, 'Signup.html', {'form_data': form_data})

        # Validation: Email format
        EmailRegex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(EmailRegex, cEmail):
            messages.error(request, 'Enter a valid email address.')
            return render(request, 'Signup.html', {'form_data': form_data})

        # Validation: Mobile number format (assuming 10 digits)
        if not nMobile.isdigit() or len(nMobile) != 10:
            messages.error(request, 'Enter a valid 10-digit mobile number.')
            return render(request, 'Signup.html', {'form_data': form_data})

        # Validation: Password strength (minimum length 8)
        if len(cPassword) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'Signup.html', {'form_data': form_data})

        # Validation: Passwords match
        if cPassword != cConfirmPassword:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'Signup.html', {'form_data': form_data})

        # Check if the username, email, or mobile already exists in the database
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT nUserID FROM SignIn WHERE cUserName = %s OR cEmail = %s OR nMobileNumber = %s
                """, [cUsername, cEmail, nMobile])
                existing_user = cursor.fetchone()
                
                if existing_user:
                    messages.error(request, 'An account with this Username, Email, or Mobile Number already exists.')
                    return render(request, 'Signup.html', {'form_data': form_data})

        except Exception as e:
            print(f"Database error: {e}")
            messages.error(request, 'There was an error. Please try again.')
            return render(request, 'Signup.html', {'form_data': form_data})

        # Get current date and time for dDOC
        CurrentDatetime = datetime.now()

        # Save the new user using the stored procedure
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    EXEC spNewUser %s, %s, %s, %s, %s
                """, [cUsername, cPassword, nMobile, cEmail, CurrentDatetime])
            messages.success(request, 'Account created successfully. Please sign in.')
            return redirect('Signin')
        except Exception as e:
            print(f"Database error: {e}")
            messages.error(request, 'There was an error creating your account. Please try again.')
            return render(request, 'Signup.html', {'form_data': form_data})

    return render(request, 'Signup.html')


def ProjectCreation(request):
    # Get the logged-in user's nUserID from the session
    nUserID = request.session.get('nUserID')

    # Check if the user is logged in; if not, redirect to sign-in
    if not nUserID:
        messages.error(request, 'You must be logged in to create a project.')
        return redirect('Signin')
    
    # Fetch projects associated with the user
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cProjectName, nProjectID
                FROM ProjectDetails
                WHERE nUserID = %s
            """, [nUserID])
            UserProjects = cursor.fetchall()
    except Exception as e:
        messages.error(request, 'There was an error fetching your projects. Please try again.')
        UserProjects = []

    # Fetch the user's name for display
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT cUserName FROM SignIn WHERE nUserID = %s", [nUserID])
            UserRow = cursor.fetchone()
            cUserName = UserRow[0] if UserRow else None
    except Exception as e:
        messages.error(request, 'Could not retrieve user information.')
        cUserName = None

    return render(request, 'ProjectCreation.html', {
        'UserProjects': [project[0] for project in UserProjects],
        'cUserName': cUserName,
    })






def convert_size(size_bytes):
    """Converts file size from bytes to human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def GetProjectID(cProjectName, nUserID):
    # Helper function to get the project ID from the ProjectDetails table
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nProjectID
                FROM ProjectDetails 
                WHERE cProjectName = %s AND nUserID = %s
            """, [cProjectName, nUserID])
            result = cursor.fetchone()

        return result[0] if result else None
    except Exception as e:
        print(f"Error in GetProjectID: {e}")
        return None


def DeleteFile(request, cProjectName, file_name):
    # Get the logged-in user's nUserID from the session
    nUserID = request.session.get('nUserID')
    
    if not nUserID:
        messages.error(request, 'You must be logged in to delete files.')
        return redirect('Signin')

    # Get the project ID from cProjectName
    nProjectID = GetProjectID(cProjectName, nUserID)

    if not nProjectID:
        messages.error(request, 'Invalid project.')
        return redirect('FileUpload', cProjectName=cProjectName)

    # Delete the file from the file system
    try:
        # Fetch the user's cUserName
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cUserName
                FROM SignIn
                WHERE nUserID = %s
            """, [nUserID])
            result = cursor.fetchone()
            if result:
                cUserName = result[0]
            else:
                messages.error(request, 'Unable to fetch user information.')
                return redirect('FileUpload', cProjectName=cProjectName)

        # Construct the file path
        file_path = os.path.join(settings.MEDIA_ROOT, cUserName, cProjectName, file_name)

        # Remove the file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            messages.error(request, f'File "{file_name}" not found in the file system.')

    except Exception as e:
        print(f"Error deleting file from file system: {e}")
        messages.error(request, f'Error deleting file "{file_name}".')

    # Delete the file record from the database
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM ProjectFiles
                WHERE cFileName = %s AND nProjectID = %s AND nUserID = %s
            """, [file_name, nProjectID, nUserID])

        messages.success(request, f'File "{file_name}" deleted successfully.')
    except Exception as e:
        print(f"Database error: {e}")
        messages.error(request, f'Error deleting file "{file_name}" from the database.')

    return redirect('FileUpload', cProjectName=cProjectName)


def InsertKeywords(request, cProjectName):
    # Get the logged-in user's nUserID from the session
    nUserID = request.session.get('nUserID')

    if not nUserID:
        messages.error(request, 'You must be logged in to insert keywords.')
        return redirect('Signin')
    
    # Fetch the user's name
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT cUserName FROM SignIn WHERE nUserID = %s", [nUserID])
            UserRow = cursor.fetchone()
            if UserRow:
                cUserName = UserRow[0]
                print(f"Home: Retrieved username: {cUserName}")
            else:
                cUserName = None
    except Exception as e:
        print(f"Home: Error fetching user data: {e}")
        cUserName = None

    # Fetch projects associated with the user
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cProjectName
                FROM ProjectDetails
                WHERE nUserID = %s
            """, [nUserID])
            UserProjects = cursor.fetchall()  # List of tuples containing project names
    except Exception as e:
        print(f"Database error: {e}")
        messages.error(request, 'There was an error fetching your projects. Please try again.')
        UserProjects = []

    # Get the project ID from cProjectName
    nProjectID = GetProjectID(cProjectName, nUserID)


    if not nProjectID:
        messages.error(request, 'Invalid project.')
        return redirect('FileUpload', cProjectName=cProjectName)

    if request.method == 'POST':
        cKeywords = request.POST.get('cKeywords')

        if not cKeywords:
            messages.error(request, 'Keywords cannot be empty.')
            return redirect('InsertKeywords', cProjectName=cProjectName)

        try:
            # Check if the keyword already exists for the project
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM KeywordsDetails
                    WHERE nProjectID = %s AND cKeyword = %s
                """, [nProjectID, cKeywords])
                KeywordExists = cursor.fetchone()[0]
                # print(KeywordExists,"KeywordExistsKeywordExists")

            if KeywordExists:
                messages.error(request, 'This keyword already exists for the project.')
                return redirect('InsertKeywords', cProjectName=cProjectName)

            # Get the current datetime
            dDOC = datetime.now()

            # Call the stored procedure to save the keyword info in the database
            with connection.cursor() as cursor:
                cursor.execute("""
                    EXEC spSaveKeyword @iMode=%s, @nProjectID=%s, @nUserID=%s, @cKeyword=%s, @dDOC=%s
                """, [1, nProjectID, nUserID, cKeywords, dDOC])

            messages.success(request, 'Keywords inserted successfully.')
            return redirect('InsertKeywords', cProjectName=cProjectName)

        except Exception as e:
            print(f"Database error: {e}")

    # Fetch existing keywords (ensure you include nKeywordID and nState)
    KeywordsList = []
    keyword_ids = []  # List to hold keyword IDs
    keyword_names = [] 
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nKeywordID, cKeyword, nState 
                FROM KeywordsDetails 
                WHERE nProjectID = %s
            """, [nProjectID])
            KeywordsList = cursor.fetchall()
            # print(KeywordsList,"KeywordsList")
            for kw in KeywordsList:
                keyword_ids.append(kw[0])
                keyword_names.append(kw[1])
            request.session['keyword_ids'] = keyword_ids
            request.session['keyword_names'] = keyword_names
            file_list = request.session.get('file_list', [])
            print(file_list,"file_list")
            file_ids = request.session.get('file_ids', [])
            output = read_files(file_list,file_ids)
            # print(output,"output")
            keywords_with_ids = read_keywords_and_ids(keyword_names,keyword_ids)
            print(keywords_with_ids,"keywords_with_idsssssss")
            dataframe=process_pdf_and_save_to_df(output, keywords_with_ids)
            print(dataframe,"dataframe")
            insert_extracted_data_into_db(dataframe, nUserID,cProjectName)
            
    except Exception as e:
        print(f"Database error: {e}")
    # Pass the keyword ID and state along with the keyword name
    return render(request, 'InsertKeywords.html', {
        'cProjectName': cProjectName,
        'KeywordsList': [{'id': kw[0], 'name': kw[1], 'state': kw[2]} for kw in KeywordsList],  # Extract id, name, and state
        'UserProjects': [project[0] for project in UserProjects],  # Extract project names from tuples
        'cUserName': cUserName,
    })


def EditKeywordState(request, keyword_id, cProjectName):
    # Get the logged-in user's nUserID from the session
    nUserID = request.session.get('nUserID')

    if not nUserID:
        messages.error(request, 'You must be logged in to edit the keyword state.')
        return redirect('Signin')
    
    # Fetch the user's name
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT cUserName FROM SignIn WHERE nUserID = %s", [nUserID])
            UserRow = cursor.fetchone()
            if UserRow:
                cUserName = UserRow[0]
                print(f"Home: Retrieved username: {cUserName}")
            else:
                cUserName = None
    except Exception as e:
        print(f"Home: Error fetching user data: {e}")
        cUserName = None

    # Fetch projects associated with the user
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cProjectName
                FROM ProjectDetails
                WHERE nUserID = %s
            """, [nUserID])
            UserProjects = cursor.fetchall()  # List of tuples containing project names
    except Exception as e:
        print(f"Database error: {e}")
        messages.error(request, 'There was an error fetching your projects. Please try again.')
        UserProjects = []

    if request.method == 'POST':
        # Fetch the new keyword and state from the form
        new_keyword = request.POST.get('keyword')
        nState = request.POST.get('nState')
        try:
            # Update the keyword and its state in the database
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE KeywordsDetails
                    SET cKeyword = %s, nState = %s
                    WHERE nKeywordID = %s AND nUserID = %s
                """, [new_keyword, nState, keyword_id, nUserID])

            messages.success(request, 'Keyword and state updated successfully.')
            return redirect('InsertKeywords', cProjectName=cProjectName)
        except Exception as e:
            print(f"Database error: {e}")
            messages.error(request, 'There was an error updating the keyword and state. Please try again.')

    # Fetch the current state and keyword of the keyword
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cKeyword, nState
                FROM KeywordsDetails
                WHERE nKeywordID = %s AND nUserID = %s
            """, [keyword_id, nUserID])
            keyword_row = cursor.fetchone()
            if keyword_row:
                keyword = keyword_row[0]
                CurrentState = keyword_row[1]
            else:
                messages.error(request, 'Keyword not found.')
                return redirect('InsertKeywords', cProjectName=cProjectName)
    except Exception as e:
        print(f"Database error: {e}")
        messages.error(request, 'There was an error fetching the keyword data.')

    return render(request, 'EditKeywordState.html', {
        'nKeywordID': keyword_id,
        'cProjectName': cProjectName,
        'CurrentState': CurrentState,
        'keyword': keyword,  # Pass the current keyword to the template
        'UserProjects': [project[0] for project in UserProjects],  # Extract project names from tuples
        'cUserName': cUserName,
    })




def FileUpload(request, cProjectName):
    # Initialize variables for file handling
    global file_list
    global file_ids
    global keyword_list
    keyword_list = []
    file_list = []
    file_ids=[]
    successfully_uploaded_files=0
    files_already_exist=[]
    nUserID = request.session.get('nUserID')

    if not nUserID:
        messages.error(request, 'You must be logged in to upload files.')
        return redirect('Signin')

    # Fetch the user's username from the database
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cUserName
                FROM SignIn
                WHERE nUserID = %s
            """, [nUserID])
            result = cursor.fetchone()
            if result:
                cUserName = result[0]
            else:
                messages.error(request, 'Unable to fetch user information.')
                return redirect('FileUpload', cProjectName=cProjectName)
    except Exception as e:
        print(f"Database error: {e}")
        messages.error(request, '')
        return redirect('FileUpload', cProjectName=cProjectName)

    # Fetch projects associated with the user to display on the upload page
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cProjectName
                FROM ProjectDetails
                WHERE nUserID = %s
            """, [nUserID])
            UserProjects = cursor.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        messages.error(request, 'There was an error fetching your projects. Please try again.')
        UserProjects = []

    # Check if the project exists for the user
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM ProjectDetails
                WHERE nUserID = %s AND cProjectName = %s
            """, [nUserID, cProjectName])
            project_exists = cursor.fetchone()[0]

            if not project_exists:
                messages.error(request, 'Project not found.')
                return redirect('ProjectCreation')

    except Exception as e:
        print(f"Database error: {e}")
        messages.error(request, 'There was an error checking the project. Please try again.')
        return redirect('ProjectCreation')

    if request.method == 'POST':
        UploadedFiles = request.FILES.getlist('UploadedFile')  # Get a list of uploaded files
        cExtention = UploadedFiles[::-1]
        print(UploadedFiles,"UploadedFiles")
        print(len(UploadedFiles),"hgjghjghg")
        if not UploadedFiles:
            messages.error(request, 'You must select files to upload.')
            return redirect('FileUpload', cProjectName=cProjectName)

        # Set the total size limit (example: 250 MB)
        limit = 250 * 1024 * 1024

        # Fetch the total size of previously uploaded files for this project
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT SUM(nFileSize)
                    FROM ProjectFiles
                    WHERE nProjectID = (
                        SELECT nProjectID
                        FROM ProjectDetails
                        WHERE cProjectName = %s AND nUserID = %s
                    )
                """, [cProjectName, nUserID])
                previous_total_size = cursor.fetchone()[0] or 0
                print(previous_total_size,"previous_total_size")

        except Exception as e:
            print(f"Database error: {e}")
            messages.error(request, 'There was an error checking the previously uploaded file sizes.')
            return redirect('FileUpload', cProjectName=cProjectName)

        # Calculate total size of all uploaded files
        total_size = sum(UploadedFile.size for UploadedFile in UploadedFiles)
        combained_size =previous_total_size+total_size
        if combained_size > limit:
            messages.error(request, f'Total file size (including previously uploaded files) exceeds the 2 MB limit. '
                                    f'Please reduce the file size or number of files.')
            return redirect('FileUpload', cProjectName=cProjectName)

        # Create the directory structure: cUserName/ProjectName/
        UserFolder = os.path.join(settings.MEDIA_ROOT,cUserName)
        ProjectFolder = os.path.join(UserFolder,cProjectName)

        if not os.path.exists(ProjectFolder):
            os.makedirs(ProjectFolder)

        # Iterate over each file and save it
        for UploadedFile in UploadedFiles:
            if isinstance(UploadedFile, str):
                print(f"Skipping non-file: {UploadedFile}")
                continue  # Skip if it's a string rather than a file object
            file_name = UploadedFile.name
            file_size_bytes = UploadedFile.size  # Get the file size in bytes
            _,cExtention = os.path.splitext(file_name)

            # Check for duplicate file in the database
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM ProjectFiles
                        WHERE cFileName = %s AND nProjectID = (
                            SELECT nProjectID
                            FROM ProjectDetails
                            WHERE cProjectName = %s AND nUserID = %s
                        )
                    """, [file_name, cProjectName, nUserID])
                    file_exists = cursor.fetchone()[0] > 0

                if file_exists:
                    files_already_exist.append(file_name) 
                    continue  # Skip to the next file if it already exists
            except Exception as e:
                print(f"Database error: {e}")
                messages.error(request, f'There was an error checking for duplicate files.')
                continue  # Skip to the next file

            # Save the file to the specified path
            file_path = os.path.join(ProjectFolder, file_name)
            with open(file_path, 'wb+') as destination:
                for chunk in UploadedFile.chunks():
                    destination.write(chunk)
                    print(destination,"filepathpathssssss")

            try:
                dDOC = datetime.now()
                # Get the project ID from cProjectName in ProjectDetails
                nProjectID = GetProjectID(cProjectName, nUserID)

                # Save file info to the database
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC spSaveFile @iMode=%s, @nProjectID=%s, @nUserID=%s, @cFileName=%s, @nFileSize=%s, @cExtention=%s, @dDOC=%s
                    """, [1, nProjectID, nUserID, file_name, file_size_bytes, cExtention, dDOC])
                successfully_uploaded_files += 1
            except Exception as e:
                print(f"Database error: {e}")
                messages.error(request, f'There was an error uploading the file "{file_name}". Please try again.')

        # Success and warning messages
        if successfully_uploaded_files > 0:
            messages.success(request, f'{successfully_uploaded_files} file(s) uploaded successfully.')

        if files_already_exist:
            messages.warning(request, f'{len(files_already_exist)} file(s) already exist.')

        return redirect('FileUpload', cProjectName=cProjectName)

    # Fetch the list of files for the specified project
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nProjectID
                FROM ProjectDetails
                WHERE cProjectName = %s AND nUserID = %s
            """, [cProjectName, nUserID])
            project_id = cursor.fetchone()
            if not project_id:
                messages.error(request, 'Project not found.')

        # Fetch the files for the project
            cursor.execute("""
                SELECT cFileName, nFileID
                FROM ProjectFiles
                WHERE nProjectID = %s
            """, [project_id[0]])

            files = cursor.fetchall()
            print(f"Fetched filesssss: {files}")  # Output fetched files for debugging

            # Get the username to construct the file path
            cursor.execute("""
                SELECT cUserName
                FROM SignIn
                WHERE nUserID = %s
            """, [nUserID])
            result = cursor.fetchone()
            if result:
                cUserName = result[0]
            else:
                messages.error(request, 'Unable to fetch user information.')
                return redirect('Signin')

            # Define the base folder where files are stored
            UserFolder = os.path.join(settings.MEDIA_ROOT, cUserName)
            ProjectFolder = os.path.join(UserFolder, cProjectName)
            request.session['ProjectFolder'] = ProjectFolder
            print(ProjectFolder,"ProjectFolder")
            dir=get_pdf_directory(ProjectFolder)
            
            file_ids = []
            for file in files:
                file_name = file[0]
                file_path = os.path.join(ProjectFolder, file_name)  # Construct the full file path
                # print(file_path,"file_path")
                pdf_paths=get_pdf_directory(file_path)
                # print(pdf_paths,"pdf_pathspdf_paths")
                
                
                if os.path.exists(file_path):  # Check if the file exists
                    file_list.append(file_path)
                    file_ids.append(file[1])
                    request.session['file_list'] = file_list
                    print(file_list,"filelist")
                    request.session['file_ids'] = file_ids
                    
            if not file_list:
                print("No valid files found in the project directory")
            print(file_list,"ok!!!!!!!!!!!!")

            
    except Exception as e:
        print(f"Database error: {e}")
        file_list = []


    return render(request, 'FileUpload.html', {
        'UserProjects': [project[0] for project in UserProjects],
        'cProjectName': cProjectName,
        'files': file_list,
        'cUserName': cUserName,
    })


def delete_file(request, filename):
    if request.method == 'POST':
        # Get the current user ID from the session
        nUserID = request.session.get('nUserID')

        if not nUserID:
            messages.error(request, 'You must be logged in to delete files.')
            return redirect('Signin')

        # Fetch the username associated with the current user ID from the database
        try:
            with connection.cursor() as cursor:
                cursor.execute(""" 
                    SELECT cUserName 
                    FROM SignIn 
                    WHERE nUserID = %s
                """, [nUserID])
                result = cursor.fetchone()
                
                if result:
                    cUserName = result[0]
                else:
                    messages.error(request, 'Unable to fetch user information.')
                    return redirect('FileUpload', cProjectName=request.POST.get('project_name', 'default'))
        
        except Exception as e:
            messages.error(request, f"Error fetching user info: {e}")
            return redirect('FileUpload', cProjectName=request.POST.get('project_name', 'default'))

        # Get the project name from POST data
        cProjectName = request.POST.get('project_name', 'default')

        # Define the file path where files are stored (e.g., media directory)
        file_path = Path(settings.MEDIA_ROOT) / cUserName / cProjectName / filename
        filename_only = os.path.basename(filename)  # Extract only the filename, e.g., "Arora 2018.pdf"

        # Attempt to delete the file from the file system
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception as e:
                messages.error(request, f'Error deleting file: {str(e)}')
                return redirect('FileUpload', cProjectName=cProjectName)
        else:
            messages.error(request, 'File not found on the filesystem.')
            return redirect('FileUpload', cProjectName=cProjectName)

        # Proceed to delete file entries from the database
        try:
            with connection.cursor() as cursor:
                # Fetch the project ID for the current project
                cursor.execute("""
                    SELECT nProjectID
                    FROM ProjectDetails
                    WHERE cProjectName = %s AND nUserID = %s
                """, [cProjectName, nUserID])
                project_id_row = cursor.fetchone()

                if project_id_row:
                    project_id = project_id_row[0]

                    # Fetch the nFileID for the file to be deleted using only the filename
                    cursor.execute("""
                        SELECT nFileID
                        FROM ProjectFiles
                        WHERE nProjectID = %s AND cFileName = %s
                    """, [project_id, filename_only])  # Use `filename_only` here
                    file_id_row = cursor.fetchone()

                    if file_id_row:
                        nFileID = file_id_row[0]

                        # Delete the file entry from the ProjectFiles table
                        cursor.execute("""
                            DELETE FROM ProjectFiles
                            WHERE nProjectID = %s AND cFileName = %s
                        """, [project_id, filename_only])  # Use `filename_only` here

                        # Delete the corresponding rows from TrainingData table
                        cursor.execute("""
                            DELETE FROM TrainingDataDetails
                            WHERE nFileNameID = %s
                        """, [nFileID])

                        if cursor.rowcount > 0:
                            messages.success(request, f'File "{filename_only}" deleted.')
                        else:
                            messages.error(request, 'Error: No rows deleted. Possible issue with entry.')
                    else:
                        messages.error(request, f'File ID not found for "{filename_only}".')
                else:
                    messages.error(request, f'Project "{cProjectName}" not found for the user.')

        except Exception as e:
            messages.error(request, f"Error deleting file from database: {e}")

    # Redirect back to the file upload page after deletion
    return redirect('FileUpload', cProjectName=cProjectName)





   


def insert_extracted_data_into_db(dataframe, nUserID, cProjectName):
    """
    Inserts extracted data into the database using the stored procedure.
    Includes duplicate checking to prevent duplicate entries.
    """
    
    # Get the project ID from cProjectName
    nProjectID = GetProjectID(cProjectName, nUserID)
    
    try:
        # Ensure project ID retrieval was successful
        if not nProjectID:
            raise ValueError(f"No project found for name {cProjectName} and user ID {nUserID}")
        
        with connection.cursor() as cursor:
            for index, row in dataframe.iterrows():
                nKeywordID = row['Keyword ID']
                nFileNameID = row['PDF Number']
                nPageNumber = row['Page']
                nStartLine = row['start line']
                nEndLine = row['end Line']
                cSentence = row['Sentence'].strip() if pd.notna(row['Sentence']) else ''
                cData = row['Data Type'].strip() if pd.notna(row['Data Type']) else ''
                cDataValue = row['Value'].strip() if pd.notna(row['Value']) else ''
                
                # Check for duplicates using parameterized query with proper CAST
                check_duplicate_query = """
                    SELECT COUNT(*)
                    FROM TrainingDataDetails
                    WHERE nProjectID = %s
                    AND nKeywordID = %s
                    AND nFileNameID = %s
                    AND nPageNumber = %s
                    AND nStartLine = %s
                    AND nEndLine = %s
                    AND CAST(cSentence AS NVARCHAR(MAX)) = CAST(%s AS NVARCHAR(MAX))
                    AND CAST(cData AS NVARCHAR(MAX)) = CAST(%s AS NVARCHAR(MAX))
                    AND CAST(cDataValue AS NVARCHAR(MAX)) = CAST(%s AS NVARCHAR(MAX))
                """
                
                params = [
                    nProjectID,
                    nKeywordID,
                    nFileNameID,
                    nPageNumber,
                    nStartLine,
                    nEndLine,
                    cSentence,
                    cData,
                    cDataValue
                ]
                
                try:
                    cursor.execute(check_duplicate_query, params)
                    duplicate_count = cursor.fetchone()[0]
                
                    # Skip if duplicate found
                    if duplicate_count > 0:
                       print(f"Skipping duplicate entry for PDF {nFileNameID}, Page {nPageNumber}")
                       continue
                    
                    # Insert new record using stored procedure
                    insert_query = """
                    EXEC [dbo].[spTrainingData]
                    @iMode = %s,
                    @nTrainingID = %s,
                    @nProjectID = %s,
                    @nKeywordID = %s,
                    @nFileNameID = %s,
                    @nPageNumber = %s,
                    @nStartLine = %s,
                    @nEndLine = %s,
                    @cSentence = %s,
                    @cData = %s,
                    @cDataValue = %s
                    """
                            
                    insert_params = [
                    1,                  # @iMode
                    None,              # @nTrainingID
                    nProjectID,
                    nKeywordID,
                    nFileNameID,
                    nPageNumber,
                    nStartLine,
                    nEndLine,
                    cSentence,
                    cData,
                    cDataValue
                    ]
                            
                    cursor.execute(insert_query, insert_params)
                    connection.commit()  # Commit after each successful insert
                
                except Exception as e:
                    print(f"Error inserting extracted data: {str(e)}")
                    print(f"Database error: {str(e)}")
                    connection.rollback()
                    raise
    finally:
        if not connection.autocommit:
            connection.commit()



 
def keywords(request, cProjectName):
    global keyword_list
    keyword_list = []
    keyword_names = []
    nUserID = request.session.get('nUserID')
    print(nUserID, "UserID")

    if not nUserID:
        messages.error(request, 'You must be logged in to view files.')
        return redirect('Signin')

    # Fetch project ID
    nProjectID = GetProjectID(cProjectName, nUserID)
    print(nProjectID, "ProjectID")

    KeywordsList = []
    uploadedfile = []
    cDataValuesList = request.session.get('cDataValuesList', [])  # Load data from session if it exists

    # Fetch the user's name
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT cUserName FROM SignIn WHERE nUserID = %s", [nUserID])
            UserRow = cursor.fetchone()
            if UserRow:
                cUserName = UserRow[0]
                print(f"Home: Retrieved username: {cUserName}")
            else:
                cUserName = None
    except Exception as e:
        print(f"Home: Error fetching user data: {e}")
        cUserName = None

    # Fetch projects associated with the user
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cProjectName
                FROM ProjectDetails
                WHERE nUserID = %s
            """, [nUserID])
            UserProjects = cursor.fetchall()  # List of tuples containing project names
    except Exception as e:
        print(f"Database error: {e}")
        messages.error(request, 'There was an error fetching your projects. Please try again.')
        UserProjects = []

    try:
        with connection.cursor() as cursor:
            # Query to fetch keywords
            cursor.execute("""
                SELECT nKeywordID, cKeyword 
                FROM KeywordsDetails 
                WHERE nProjectID = %s and nState=1
            """, [nProjectID])

            KeywordsList = cursor.fetchall()
            print(KeywordsList, "Fetched Keywords")

            # Store keyword names for later use if needed
            for keywords in KeywordsList:
                keyword_names.append(keywords[1])
                print(keyword_names, "Keyword Names")
    except Exception as e:
        print(f"Database error: {e}")

    # Fetch file uploads corresponding to nProjectID and nUserID
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nFileID, cFileName 
                FROM ProjectFiles 
                WHERE nProjectID = %s AND nUserID = %s
            """, [nProjectID, nUserID])

            upload = cursor.fetchall()
            for up in upload:
                uploadedfile.append(up[1])
            print(uploadedfile, "Uploaded Files")

    except Exception as e:
        print(f"Database error while fetching file uploads: {e}")
        return HttpResponse("An error occurred while fetching file uploads.", status=500)

    # Handle POST request
    if request.method == 'POST':
        selected_keywords = request.POST.getlist('selected_keywords')
        selected_files = request.POST.getlist('selected_data')

        print(selected_keywords, "selected_keywords")
        print(selected_files, "selected_files")

        # Save selected checkboxes to session
        request.session['selected_keywords'] = selected_keywords
        request.session['selected_files'] = selected_files

        # Fetch the data values based on the selected keywords and files
        cDataValuesList = fetch_training_data(request, selected_keywords, selected_files, nProjectID)
        print(cDataValuesList, "cDataValuesList")

        # Save the data values to session
        request.session['cDataValuesList'] = cDataValuesList

    # Load previously selected checkboxes from session if they exist
    selected_keywords = request.session.get('selected_keywords', [])
    selected_files = request.session.get('selected_files', [])

    # Return the rendered template with the context
    return render(request, 'keywords.html', {
        'cProjectName': cProjectName,
        'KeywordsList': [{'id': kw[0], 'name': kw[1]} for kw in KeywordsList],
        'uploadedfile': [{'id': up[0], 'name': up[1]} for up in upload],
        'cDataValuesList': cDataValuesList,
        'selected_keywords': selected_keywords,  # Pass selected keywords
        'selected_files': selected_files,        # Pass selected files
        'UserProjects': [project[0] for project in UserProjects],
        'cUserName': cUserName,
    })


    
def fetch_training_data(request,selected_keywords, selected_files, nProjectID):
    """
    Fetch cDataValues based on the selected keywords and files using the stored procedure.
    """
    cDataValues = []
    global cDataValuesList_list
    global alldata
    cDataValuesList_list=[]
    alldata=[]
    try:
        with connection.cursor() as cursor:
            for keyword_id in selected_keywords:
                print(keyword_id,"keyword_id")
                for file_id in selected_files:
                    # Debugging: Print parameters
                    print(f"Executing stored procedure with: nProjectID={nProjectID}, nKeywordID={keyword_id}, nFileNameID={file_id}")

                    cursor.execute("""
                        EXEC spTrainingData @iMode=%s, @nTrainingID = %s,
                        @nProjectID = %s,
                        @nKeywordID = %s,
                        @nFileNameID = %s,
                        @nPageNumber = %s,
                        @nStartLine = %s,
                        @nEndLine = %s,
                        @cSentence = %s,
                        @cData = %s,
                        @cDataValue = %s
                            
                    """, [
                        2,  # iMode to fetch data
                        None,  # nTrainingID (not used when fetching)
                        nProjectID,
                        keyword_id,
                        file_id,
                        None, None, None, None, None, None  # Rest of the parameters
                    ])
                    
                    # Fetch results
                    result = cursor.fetchall()
                    # print(result,"resultresult")
                    if result:  # If there are results, extend the list
                        cDataValues.extend(result)
                        # print(cDataValues,"cDataValuescDataValuessssss")
                        cDataValuesList_list = [{'value': row[9],'id':row[0]} for row in cDataValues]
                        print(cDataValuesList_list,"cDataValuesList_listssssssssssssssssssss")
                        alldata=[{'keyword': row[2],'file':row[3],'page':row[4],'startline':row[5],'endline':row[6],'cdata':row[8],'cDataValue':row[9]} for row in cDataValues]
                        
                    else:
                        print(f"No results returned for keyword_id={keyword_id} and file_id={file_id}")

    except Exception as e:
        print(f"Error while fetching training data: {e}")

    return cDataValuesList_list
   


def store_value(request, id, value,cProjectName):
    
    nUserID = request.session.get('nUserID')
    print(nUserID,"nUserID")
    nProjectID = GetProjectID(cProjectName, nUserID)
    print(nProjectID,"cProjectName")
    # Store the clicked cDataValue and ID in session
    request.session['clicked_cDataValue'] = value
    request.session['clicked_cDataValueID'] = id
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cUserName
                FROM SignIn
                WHERE nUserID = %s
            """, [nUserID])
            result = cursor.fetchone()
            if result:
                cUserName = result[0]
            else:
                messages.error(request, 'Unable to fetch user information.')
               
    except Exception as e:
        print(f"Database error: {e}")
        messages.error(request, 'There was an error fetching your username. Please try again.')
    try:
        with connection.cursor() as cursor:
            # Fetch project ID to verify the project exists for this user
            cursor.execute("""
                SELECT nProjectID
                FROM ProjectName
                WHERE cProjectName = %s AND nUserID = %s
            """, [cProjectName, nUserID])
            project_data = cursor.fetchone()
            
    except Exception as e:
        print(f"Database error: {e}")
        messages.error(request, 'There was an error fetching your username. Please try again.')
    # Fetch all corresponding details from the database
    try:
        with connection.cursor() as cursor:
            # Retrieve the nTrainingID from the session
            nTrainingID = request.session.get('clicked_cDataValueID')
            cDataValue=request.session.get('clicked_cDataValue')

            # open=open_file(file_list)
            print(nTrainingID,"nTrainingIDnTrainingID")
            print(cDataValue,"cDataValuecDataValue")
            try:
                cursor.execute("""
                SELECT 
                    td.nKeywordID,
                    td.nFileNameID,
                    td.nPageNumber,
                    td.nStartLine,
                    td.nEndLine,
                    td.cData,
                    td.cDataValue,
                    pf.cFileName
                FROM TrainingDataDetails td
                JOIN ProjectFiles pf ON td.nFileNameID = pf.nFileID
                WHERE td.nTrainingID = %s
            """, [nTrainingID])

                alldata = cursor.fetchone()
                print(alldata,"yesssssss")
                if alldata:
                    cFileName = alldata[-1]
                    print(cFileName,"cFileNamecFileNamessss")
                    nPageNumber=alldata[2]
                    print(nPageNumber,"nPageNumberssss")
                # datas=open_file(alldata)
                    print(alldata, "alldatass")
                    UserFolder = os.path.join(settings.MEDIA_ROOT, cUserName)
                    print(UserFolder,"UserFolder")
                    ProjectFolder = os.path.join(UserFolder, cProjectName)
                    print(ProjectFolder,"ProjectFolder")
                    full_path = os.path.join(ProjectFolder, cFileName)
                    print(full_path,"full_path")
                    # Generate the PDF URL correctly
                    if os.path.exists(full_path):
                        relative_path = os.path.relpath(full_path, settings.MEDIA_ROOT).replace("\\", "/")
                        media_url = f"{settings.MEDIA_URL}{relative_path}"
                        print(media_url, "Fullssfile pathmediaaaaaaaaaaaaaa")
                        request.session['processed_pdf_url'] = media_url
                        print("request.session['processed_pdf_url']",request.session['processed_pdf_url'])
                        x = list(alldata)
                        x.append(full_path)
                        alldata_with_path = tuple(x)
                        print(alldata_with_path,"alldata_with_pathalldata_with_path")
                        get_all_dbvalues=get_all_dbvalue(alldata_with_path)
                        # print(get_all_dbvalues,"get_all_dbvalues")
                        process_pdf_highlightings=process_pdf_highlighting(alldata_with_path,ProjectFolder)
                        # print(process_pdf_highlightings,"process_pdf_highlightingsprocess_pdf_highlightings")
                        save_and_open_temp_pdfs=save_and_open_temp_pdf(full_path,nPageNumber)
                    
            except Exception as e:
                print("Error:", str(e))    
    except Exception as e:
        print("ghvghvgcvg")
    
    # Return or redirect to a different view
    print("Processing completed.")
    return redirect('filekeyword', cProjectName=cProjectName)
    return render(request,'files.html')




def display_pdf(request):
    process_pdf_highlightings = request.session.get('processed_pdf_url')
    if process_pdf_highlightings and os.path.exists(process_pdf_highlightings):
            # Serve the highlighted PDF as a response
            print("haiiiiiiiii")
            return FileResponse(open(process_pdf_highlightings, 'rb'), content_type='application/pdf')
    else:
            messages.error(request, 'Error generating the highlighted PDF.')
            return Http404("Highlighted PDF not found.")
      
    return render(request, 'display_pdf.html')
    

    




def Home(request):
    nUserID = request.session.get('nUserID')

    if not nUserID:
        return redirect('Signin')

    cUserName = None

    # Fetch the username
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT cUserName FROM SignIn WHERE nUserID = %s", [nUserID])
            UserRow = cursor.fetchone()
            if UserRow:
                cUserName = UserRow[0]
    except Exception as e:
        print(f"Error fetching user data: {e}")

    # Fetch projects associated with the user
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cProjectName
                FROM ProjectDetails
                WHERE nUserID = %s
            """, [nUserID])
            UserProjects = cursor.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        messages.error(request, 'Error fetching your projects.')
        UserProjects = []

    # Hardcoded outcome options (as per your checkbox structure)
    outcome_options = [
        'Prevalence',
        'Incidence',
        'Odds Ratio',
        'Relative Risk',
        'Correlation Coefficient',
        'Mean Change',
        'Hazard Ratio'
    ]

    edit_mode = request.GET.get('edit') == 'true'
    original_project = request.GET.get('original_project')

    # Pre-fill selected outcomes in edit mode
    selected_outcomes = []
    if edit_mode and original_project:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT cOutcomeValues FROM OutcomeBoxes WHERE cProjectName = %s AND nUserID = %s""", [original_project, nUserID])
                result = cursor.fetchone()
                if result:
                    selected_outcomes = result[0].split(',')  # Assuming values are stored as comma-separated
        except Exception as e:
            print(f"Error fetching selected outcomes: {e}")

    if request.method == 'POST':
        form_data = {
            'title': request.POST.get('title'),
            'short_title': request.POST.get('short-title'),
            'nPopulation': request.POST.get('nPopulation'),
            'cComparator': request.POST.get('cComparator'),
            'cOutcome': request.POST.get('cOutcome'),
            'objective1': request.POST.get('objective1'),
            'objective2': request.POST.get('objective2'),
            'objective3': request.POST.get('objective3'),
            'start_date': request.POST.get('start-date'),
            'end_date': request.POST.get('end-date'),
        }

        # Collect selected checkbox values for dispersion and outcomes
        selected_dispersion = request.POST.getlist('dispersion_options')  # List of selected dispersion values
        selected_outcomes = request.POST.getlist('outcome_options')  # List of selected outcome values

        # Convert lists to comma-separated strings
        selected_dispersion_str = ','.join(selected_dispersion)
        selected_outcomes_str = ','.join(selected_outcomes)

        # Parse dates
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, '%d-%b-%Y').date()
            except ValueError:
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError("Invalid date format. Please use dd-MMM-yyyy or yyyy-mm-dd.")

        try:
            start_date = parse_date(form_data['start_date'])
            end_date = parse_date(form_data['end_date'])

            if edit_mode:
                # Check for valid start date in edit mode
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT dStartDate
                        FROM ProjectDetails
                        WHERE nUserID = %s AND cProjectName = %s
                    """, [nUserID, original_project])
                    current_start_date_row = cursor.fetchone()
                if current_start_date_row:
                    current_start_date = datetime.strptime(str(current_start_date_row[0]), '%d-%b-%Y').date()
                    if start_date < current_start_date:
                        messages.error(request, 'New start date must be after or equal to the current start date.')
                        raise ValueError("Invalid start date")
            else:
                if start_date < timezone.now().date():
                    messages.error(request, 'Start date cannot be in the past.')
                    raise ValueError("Invalid start date")

            if end_date < start_date:
                messages.error(request, 'End date cannot be before start date.')
                raise ValueError("Invalid end date")

        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'Home.html', {
                'form_data': form_data,
                'edit_mode': edit_mode,
                'UserProjects': [project[0] for project in UserProjects],
                'cUserName': cUserName,
                'outcome_options': outcome_options,
                'selected_outcomes': selected_outcomes
            })

        # Save data to the project and outcome/dispersion tables
        try:
            with transaction.atomic():
                # Insert or update data for the project
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC spInsertProjectData 
                        @iMode = %s,
                        @nUserID = %s,
                        @cProjectName = %s,
                        @cShortName = %s,
                        @nPopulation = %s,
                        @cComparator = %s,
                        @cOutcome = %s,
                        @dDoC = %s,
                        @objective1 = %s,
                        @objective2 = %s,
                        @objective3 = %s,
                        @startDate = %s,
                        @endDate = %s,
                        @originalProjectName = %s,
                        @dispersionValues = %s,
                        @outcomeValues = %s
                    """, [
                        2 if edit_mode else 1,
                        nUserID,
                        form_data['title'],
                        form_data['short_title'],
                        form_data['nPopulation'],
                        form_data['cComparator'],
                        form_data['cOutcome'],
                        timezone.now(),
                        form_data['objective1'],
                        form_data['objective2'],
                        form_data['objective3'],
                        start_date,
                        end_date,
                        original_project if edit_mode else None,
                        selected_dispersion_str,
                        selected_outcomes_str
                    ])

            return redirect('ProjectCreation')

        except Exception as e:
            messages.error(request, 'Error during project operation.')
            print(f"Error during project operation: {e}")

    return render(request, 'Home.html', {
        'UserProjects': [project[0] for project in UserProjects],
        'cUserName': cUserName,
        'edit_mode': edit_mode,
        'form_data': {},
        'outcome_options': outcome_options,
        'selected_outcomes': selected_outcomes
    })






def parse_date(date_str):
    try:
        # Try parsing in dd-MMM-yyyy format directly
        date_obj = datetime.strptime(date_str, '%d-%b-%Y')
    except ValueError:
        try:
            # If the initial parsing fails, try yyyy-mm-dd format
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Invalid date format.")

    # Return the date in dd-MMM-yyyy format
    return date_obj.strftime('%d-%b-%Y')
    



def Signout(request):
    messages.success(request, 'You have been successfully signed out.')
    return redirect('Signin')

