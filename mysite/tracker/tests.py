from django.test import TestCase

# Create your tests here.
"""
Unit tests for StudyTrack tracker app.
Run with: python manage.py test tracker
"""
import datetime
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import StudyRecord, Course, Goal
from .forms import StudyRecordForm, RegisterForm, CourseForm, GoalForm


# ── Model Tests ──────────────────────────────────────

class CourseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass1234')

    def test_course_str(self):
        course = Course.objects.create(user=self.user, name='IT')
        self.assertEqual(str(course), 'IT')

    def test_course_total_mins(self):
        course = Course.objects.create(user=self.user, name='IT')
        StudyRecord.objects.create(user=self.user, course=course, title='S1',
            study_type='reading', duration_mins=30, study_date=datetime.date.today())
        StudyRecord.objects.create(user=self.user, course=course, title='S2',
            study_type='lecture', duration_mins=45, study_date=datetime.date.today())
        self.assertEqual(course.total_mins(), 75)

    def test_course_belongs_to_user(self):
        course = Course.objects.create(user=self.user, name='Maths')
        self.assertEqual(course.user, self.user)


class GoalModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bob', password='pass1234')
        self.course = Course.objects.create(user=self.user, name='IT')

    def test_goal_str(self):
        goal = Goal.objects.create(course=self.course, title='Finish labs')
        self.assertIn('Finish labs', str(goal))

    def test_goal_default_status(self):
        goal = Goal.objects.create(course=self.course, title='Read textbook')
        self.assertEqual(goal.status, 'in_progress')


class StudyRecordModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='carol', password='pass1234')

    def test_record_str(self):
        record = StudyRecord.objects.create(user=self.user, title='Session 1',
            study_type='reading', duration_mins=60, study_date=datetime.date.today())
        self.assertIn('Session 1', str(record))

    def test_record_course_optional(self):
        record = StudyRecord.objects.create(user=self.user, title='Session',
            study_type='reading', duration_mins=30, study_date=datetime.date.today())
        self.assertIsNone(record.course)


# ── Form Tests ───────────────────────────────────────

class CourseFormTest(TestCase):
    def test_valid_course_form(self):
        form = CourseForm(data={'name': 'IT', 'description': ''})
        self.assertTrue(form.is_valid())

    def test_missing_name_fails(self):
        form = CourseForm(data={'name': '', 'description': ''})
        self.assertFalse(form.is_valid())


class GoalFormTest(TestCase):
    def test_valid_goal_form(self):
        form = GoalForm(data={'title': 'Finish labs', 'target_date': '', 'status': 'in_progress'})
        self.assertTrue(form.is_valid())

    def test_missing_title_fails(self):
        form = GoalForm(data={'title': '', 'status': 'in_progress'})
        self.assertFalse(form.is_valid())


class RegisterFormTest(TestCase):
    def test_valid_registration(self):
        form = RegisterForm(data={'username': 'newuser', 'password1': 'SecurePass99', 'password2': 'SecurePass99'})
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        form = RegisterForm(data={'username': 'newuser', 'password1': 'abc', 'password2': 'xyz'})
        self.assertFalse(form.is_valid())

    def test_duplicate_username(self):
        User.objects.create_user(username='taken', password='pass')
        form = RegisterForm(data={'username': 'taken', 'password1': 'SecurePass99', 'password2': 'SecurePass99'})
        self.assertFalse(form.is_valid())


# ── View Tests ───────────────────────────────────────

class AuthViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='pass1234')

    def test_login_success(self):
        response = self.client.post(reverse('login'), {'username': 'alice', 'password': 'pass1234'})
        self.assertRedirects(response, reverse('record_list'))

    def test_login_failure(self):
        response = self.client.post(reverse('login'), {'username': 'alice', 'password': 'wrong'})
        self.assertContains(response, 'Invalid username or password')

    def test_unauthenticated_redirects(self):
        response = self.client.get(reverse('record_list'))
        self.assertRedirects(response, '/login/?next=/records/')


class RecordViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='bob', password='pass1234')
        self.client.login(username='bob', password='pass1234')
        self.record = StudyRecord.objects.create(user=self.user, title='Test',
            study_type='reading', duration_mins=30, study_date=datetime.date.today())

    def test_record_list(self):
        response = self.client.get(reverse('record_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test')

    def test_create_record(self):
        response = self.client.post(reverse('record_create'), {
            'title': 'New', 'study_type': 'lecture',
            'duration_mins': 45, 'study_date': datetime.date.today().isoformat(),
            'reflection_note': '',
        })
        self.assertRedirects(response, reverse('record_list'))

    def test_delete_record(self):
        response = self.client.post(reverse('record_delete', args=[self.record.pk]))
        self.assertRedirects(response, reverse('record_list'))
        self.assertFalse(StudyRecord.objects.filter(pk=self.record.pk).exists())

    def test_ajax_delete(self):
        response = self.client.post(reverse('record_delete', args=[self.record.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 204)

    def test_cannot_delete_others_record(self):
        other = User.objects.create_user(username='eve', password='pass1234')
        other_record = StudyRecord.objects.create(user=other, title='Eve session',
            study_type='reading', duration_mins=20, study_date=datetime.date.today())
        response = self.client.post(reverse('record_delete', args=[other_record.pk]))
        self.assertEqual(response.status_code, 404)


class CourseViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='carol', password='pass1234')
        self.client.login(username='carol', password='pass1234')
        self.course = Course.objects.create(user=self.user, name='IT')

    def test_course_list(self):
        response = self.client.get(reverse('course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'IT')

    def test_create_course(self):
        response = self.client.post(reverse('course_create'), {'name': 'Maths', 'description': ''})
        self.assertRedirects(response, reverse('course_list'))
        self.assertTrue(Course.objects.filter(name='Maths').exists())

    def test_course_detail(self):
        response = self.client.get(reverse('course_detail', args=[self.course.pk]))
        self.assertEqual(response.status_code, 200)

    def test_cannot_view_others_course(self):
        other = User.objects.create_user(username='dave', password='pass1234')
        other_course = Course.objects.create(user=other, name='Secret')
        response = self.client.get(reverse('course_detail', args=[other_course.pk]))
        self.assertEqual(response.status_code, 404)


class GoalViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='dave', password='pass1234')
        self.client.login(username='dave', password='pass1234')
        self.course = Course.objects.create(user=self.user, name='IT')
        self.goal = Goal.objects.create(course=self.course, title='Finish labs')

    def test_create_goal(self):
        response = self.client.post(reverse('goal_create', args=[self.course.pk]),
            {'title': 'Read notes', 'target_date': '', 'status': 'in_progress'})
        self.assertRedirects(response, reverse('course_detail', args=[self.course.pk]))

    def test_delete_goal(self):
        response = self.client.post(reverse('goal_delete', args=[self.goal.pk]))
        self.assertRedirects(response, reverse('course_detail', args=[self.course.pk]))
        self.assertFalse(Goal.objects.filter(pk=self.goal.pk).exists())