from django.contrib import admin
from django.urls import path
from lms import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('setup-profile/', views.setup_profile, name='setup_profile'),
    path('lesson/<int:lesson_id>/', views.lesson_view, name='lesson'),
    path('api/quiz/submit/', views.submit_quiz, name='submit_quiz'),
    path('api/study/time/', views.track_study_time, name='track_study_time'),
    path('profile/', views.profile_view, name='profile'),
    path('worksheets/', views.worksheets_view, name='worksheets'),
    path('departments/', views.department_view, name='departments'),
    path('videos/', views.videos_view, name='videos'),
    path('dept-manage/', views.dept_manage_view, name='dept_manage'),
    path('dept-manage/<int:dept_id>/edit/', views.dept_edit_view, name='dept_edit'),
    path('logbook/', views.logbook_view, name='logbook'),
    path('logbook/admin/', views.logbook_admin_view, name='logbook_admin'),
    path('past-tense/', views.past_tense_view, name='past_tense'),
    path('present-simple/', views.present_simple_view, name='present_simple'),
    path('past-continuous/', views.past_continuous_view, name='past_continuous'),
]
