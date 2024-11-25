from django.urls import path
from . import views

# from .views import upload_and_process_files

urlpatterns = [
    path('', views.Signin, name='Signin'),  # Set signin view as home page
    path('Signup/', views.Signup, name='Signup'),  # URL for the sign-up page
    path('ProjectCreation/', views.ProjectCreation, name='ProjectCreation'),
    path('FileUpload/<str:cProjectName>/', views.FileUpload, name='FileUpload'),  # URL for file upload page
    path('delete-file/<str:cProjectName>/<str:file_name>/', views.DeleteFile, name='DeleteFile'),
    path('insertkeywords/<str:cProjectName>/', views.InsertKeywords, name='InsertKeywords'),
    path('edit-keyword-state/<int:keyword_id>/<str:cProjectName>/', views.EditKeywordState, name='EditKeywordState'),
    # path('files/<str:cProjectName>/',views.files,name='files'),
    path('filekeyword/<str:cProjectName>/',views.keywords,name='filekeyword'),
    path('home/',views.Home,name='Home'),
    path('delete_file/<str:filename>/', views.delete_file, name='delete_file'),
    path('store_value/<int:id>/<path:value>/<str:cProjectName>/', views.store_value, name='store_value'),
    path('display_pdf/', views.display_pdf, name='display_pdf'),
    # path('fetch_training_data/<str:cProjectName>/', views.fetch_training_data,name='fetch_training_data'),
    # path('TrainingData/',views.TrainingData,name='TrainingData'),
    # path('upload/', upload_and_process_files, name='upload_and_process_files'),
    path('Signout/', views.Signout, name='Signout'),
]
