from django.db import models

# Create your models here.
from django.contrib.auth.models import User

class Course(models.Model):
    # Define the Course data
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def total_mins(self):
        return sum(r.duration_mins for r in self.records.all())
    
class Goal(models.Model):
    # Define the Goal data
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    target_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.course.name})"
    
class StudyRecord(models.Model):
    # Define the Record data
    STUDY_TYPES = [
        ('lecture', 'Lecture'),
        ('reading', 'Reading'),
        ('revision', 'Revision'),
        ('practice', 'Practice'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='records')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='records')
    title = models.CharField(max_length=200)
    study_type = models.CharField(max_length=50, choices=STUDY_TYPES)
    duration_mins = models.PositiveIntegerField()
    study_date = models.DateField()
    reflection_note = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.study_date})"
