from django.urls import path

from . import views

app_name = 'autofill'

urlpatterns = [
    path('', views.index, name='home'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/forms/', views.SectionView.as_view(), name='sections'),

    path('dashboard/forms/add/', views.AddSectionView.as_view(), name='add-section'),
    path('dashboard/forms/edit/<int:pk>/', views.EditSectionView.as_view(), name='edit-section'),
    path('dashboard/forms/detail/<int:pk>/', views.DetailSectionView.as_view(), name='detail-section'),
    path('dashboard/forms/delete/<int:pk>', views.delete_section, name='delete-section'),
    
    path('dashboard/forms/add/interval/<int:pk>/', views.AddIntervalView.as_view(), name='add-interval'),
    path('dashboard/forms/add/clocked/<int:pk>/', views.AddClockedView.as_view(), name='add-clocked'),
    path('dashboard/forms/add/crontab/<int:pk>/', views.AddCrontabView.as_view(), name='add-crontab'),
    path('dashboard/forms/add/solar/<int:pk>/', views.AddSolarView.as_view(), name='add-solar'),
    
    path('dashboard/forms/regenerate/<int:pk>/', views.regenerate_section, name='regenerate-section'),

    path('dashboard/section/detail/switch/<int:pk>/', views.form_switch, name='form-switch'),
    path('dashboard/section/submit/<int:pk>/', views.send_form, name='send-form'),
    path('dashboard/section/answer/input/<int:pk>/', views.answers, name='answers'),
    
    path('dashboard/logs/', views.LogView.as_view(), name='logs'),
    path('dashboard/logs/detail/<int:pk>/', views.LogDetailView.as_view(), name='log-detail'),
]