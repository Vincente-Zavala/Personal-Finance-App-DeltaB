from django.urls import path

from . import views

urlpatterns = [
    path('index/', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('budget/', views.budget, name='budget'),
    path('newtransactions/', views.newtransactions, name='newtransactions'),
    path('alltransactions/', views.alltransactions, name='alltransactions'),
    path('tasks/', views.tasks, name='tasks'),
    path('setup/', views.setup, name='setup'),
    path('color/', views.color, name='color'),
    path('addtransaction/', views.addtransaction, name='addtransaction'),
    path('addinput/', views.addinput, name='addinput'),
    path('element/', views.element, name='element'),
    path("edit-limits/<int:pk>/", views.edit_categorytype_limits, name="edit_categorytype_limits"),
    path("filtertransactions", views.filtertransactions, name="filtertransactions"),
    path("deletetransactions", views.deletetransactions, name="deletetransactions"),
    path("uploadfile", views.uploadfile, name="uploadfile"),
    path("signup/", views.signup, name="signup"),
    path("signin/", views.signin, name="signin"),
    path("home/", views.home, name="home")
]