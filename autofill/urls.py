from django.urls import path

from . import views

app_name = 'autofill'

urlpatterns = [
    path('', views.index, name='home'),

    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/forms/', views.SectionView.as_view(), name='sections'),

    path('dashboard/forms/detail/<int:pk>/', views.DetailSectionView.as_view(), name='detail-section'),
    path('dashboard/forms/delete/<int:pk>', views.delete_section, name='delete-section'),
    
    path("dashboard/forms/add/<str:schedule>/<int:pk>/", views.AddScheduleView.as_view(), name="add-schedule"),
    
    path('dashboard/forms/regenerate/<int:pk>/', views.regenerate_question, name='regenerate-question'),

    path('dashboard/section/detail/switch/<int:pk>/', views.form_switch, name='form-switch'),
    path('dashboard/section/submit/<int:pk>/', views.send_form, name='send-form'),
    path('dashboard/section/answer/input/<int:pk>/', views.AnswersView.as_view(), name='answers'),
    
    path('dashboard/logs/', views.LogView.as_view(), name='logs'),
    # path('dashboard/logs/detail/<int:pk>/', views.LogDetailView.as_view(), name='log-detail'),
]