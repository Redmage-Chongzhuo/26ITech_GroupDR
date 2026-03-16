from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum
from .models import StudyRecord, Course, Goal
from .forms import StudyRecordForm, CourseForm, GoalForm, RegisterForm
import datetime
from collections import Counter

#──Auth──
def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1']
        )
        login(request, user)
        return redirect('record_list')
    return render(request, 'tracker/register.html', {'form': form})

def login_view(request):
    error = None
    if request.method == 'POST':
        user = authenticate(
            username=request.POST.get('username', ''),
            password=request.POST.get('password', '')
        )
        if user:
            login(request, user)
            return redirect('record_list')
        else:
            error = 'Invalid username or password.'
    return render(request, 'tracker/login.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('login')

#──Summary helper──
def _build_summary(records):
    total_mins = records.aggregate(total=Sum('duration_mins'))['total'] or 0
    if total_mins < 60:
        total_mins_display = f"{total_mins} mins"
    else:
        h = total_mins // 60
        m = total_mins % 60
        if m > 0:
            total_mins_display = f"{h}h {m}m"
        else:
            total_mins_display = f"{h}h"

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    this_week_count = records.filter(study_date__gte=week_start).count()

    type_counts = Counter(r.get_study_type_display() for r in records)
    if type_counts:
        top_type = type_counts.most_common(1)[0][0]
    else:
        top_type = None

    return {
        'total_mins_display': total_mins_display,
        'this_week_count': this_week_count,
        'top_type': top_type,
    }

#──Study Records──
@login_required
def record_list(request):
    records = StudyRecord.objects.filter(user=request.user).order_by('-study_date').select_related('course')
    grouped_reco = {}
    for re in records:
        key = re.study_date.strftime('%B %Y')
        if key not in grouped_reco:
            grouped_reco[key] = []
        grouped_reco[key].append(re)

    context = {'records': records, 'grouped_reco': grouped_reco}
    context.update(_build_summary(records))
    return render(request, 'tracker/record_list.html', context)

@login_required
def record_create(request):
    form = StudyRecordForm(user=request.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.user = request.user
        record.save()
        return redirect('record_list')
    return render(request, 'tracker/record_form.html', {'form': form, 'action': 'Create'})

@login_required
def record_edit(request, pk):
    record = get_object_or_404(StudyRecord, pk=pk, user=request.user)
    form = StudyRecordForm(user=request.user, data=request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('record_list')
    return render(request, 'tracker/record_form.html', {'form': form, 'action': 'Edit'})

@login_required
def record_delete(request, pk):
    record = get_object_or_404(StudyRecord, pk=pk, user=request.user)
    if request.method == 'POST':
        record.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponse(status=204)
        return redirect('record_list')
    return render(request, 'tracker/record_confirm_delete.html', {'record': record})

#──Courses──
@login_required
def course_list(request):
    courses = Course.objects.filter(user=request.user).prefetch_related('records', 'goals')
    return render(request, 'tracker/course_list.html', {'courses': courses})

@login_required
def course_create(request):
    form = CourseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        course.user = request.user
        course.save()
        return redirect('course_list')
    return render(request, 'tracker/course_form.html', {'form': form, 'action': 'Create'})

@login_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)
    form = CourseForm(request.POST or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('course_list')
    return render(request, 'tracker/course_form.html', {'form': form, 'action': 'Edit'})

@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)
    if request.method == 'POST':
        course.delete()
        return redirect('course_list')
    return render(request, 'tracker/course_confirm_delete.html', {'course': course})

@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)
    records = StudyRecord.objects.filter(course=course).order_by('-study_date')
    goals = Goal.objects.filter(course=course)
    context = {
        'course': course,
        'records': records,
        'goals': goals,
    }
    context.update(_build_summary(records))
    return render(request, 'tracker/course_detail.html', context)

#──Goals──
@login_required
def goal_create(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk, user=request.user)
    form = GoalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        goal = form.save(commit=False)
        goal.course = course
        goal.save()
        return redirect('course_detail', pk=course_pk)
    return render(request, 'tracker/goal_form.html', {'form': form, 'course': course, 'action': 'Add'})

@login_required
def goal_edit(request, pk):
    goal = get_object_or_404(Goal, pk=pk, course__user=request.user)
    form = GoalForm(request.POST or None, instance=goal)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('course_detail', pk=goal.course.pk)
    return render(request, 'tracker/goal_form.html', {'form': form, 'course': goal.course, 'action': 'Edit'})

@login_required
def goal_delete(request, pk):
    goal = get_object_or_404(Goal, pk=pk, course__user=request.user)
    course_pk = goal.course.pk
    if request.method == 'POST':
        goal.delete()
        return redirect('course_detail', pk=course_pk)
    return render(request, 'tracker/goal_confirm_delete.html', {'goal': goal})
