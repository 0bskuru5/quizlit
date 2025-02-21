from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4
from random import shuffle
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta

# 🔹 Base Model (Common fields for all models)
class BaseModel(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# 🔹 Categories (Each quiz belongs to a category)
class Category(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(default="")
    total_marks = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    image = models.ImageField(upload_to="media/", default=None, null=True, blank=True)
    pdf_file = models.FileField(upload_to="pdfs/", default=None, null=True, blank=True)  # PDF file field
    total_time = models.IntegerField(default=60)

    def __str__(self):
        return self.name

    def get_total(self):
        """Fix the method to properly calculate total marks and quizzes."""
        if not hasattr(self, '_total_calculated'):
            self._total_calculated = True
            total_quizzes = self.quiz.count()  # Use 'quiz' instead of 'quiz_set'
            total_marks = self.quiz.aggregate(models.Sum('marks'))['marks__sum'] or 0
            return total_marks, total_quizzes
        return 0, 0  # Default case


# 🔹 Questions
class Question(BaseModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField()
    mark = models.IntegerField(default=5)

    def __str__(self):
        return f"Q-{self.question} | Category-{self.category}"

    def get_answer(self):
        answers = list(Answer.objects.filter(question=self))
        shuffle(answers)
        return [{"answer": answer.answer, "is_correct": answer.is_correct} for answer in answers]

    class Meta:
        ordering = ["uid"]


# 🔹 Answers
class Answer(BaseModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    answer = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question} | Answer-{self.answer} | Correct-{self.is_correct}"

    class Meta:
        ordering = ["uid"]


# 🔹 Given Quiz Questions (Tracks which questions were attempted)
class GivenQuizQuestions(BaseModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    time_taken = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.question.question} - {self.answer.answer}"


# 🔹 Quiz Model (Each user takes multiple quizzes)
class Quiz(models.Model):
    STATUS_CHOICES = (
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    )
    created_at = models.DateTimeField(auto_now_add=True)  # This should be here!
    updated_at = models.DateTimeField(auto_now=True)  # Updates on save
    uid = models.CharField(max_length=32, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="quiz")  # ✅ Fixed related_name
    given_question = models.ManyToManyField(GivenQuizQuestions, blank=True)
    marks = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_started")
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)

    def calculate_marks(self):
        """Calculate total marks based on correct answers."""
        if hasattr(self, '_marks_calculated'):
            return  

        self._marks_calculated = True  
        total_marks_obtained = sum(self.given_question.values_list('points', flat=True) or [0])  
        
        if self.marks != total_marks_obtained:  
            self.marks = total_marks_obtained
            self.save(update_fields=['marks'])  

    def __str__(self):
        return f"{self.user.username} | {self.category.name} | {self.marks} marks"

    @property
    def completion_rate(self):
        """Returns quiz completion percentage"""
        return round((self.marks / self.total_marks) * 100, 2) if self.total_marks else 0

# ✅ Update marks when quiz is completed
@receiver(post_save, sender=Quiz)
def update_marks(sender, instance, created, **kwargs):
    if instance.category:
        instance.end_time = instance.start_time + timedelta(minutes=instance.category.total_time)
    instance.calculate_marks()

# 🔹 Payment Model (User pays for each quiz)
from uuid import uuid4

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.FloatField()
    currency = models.CharField(max_length=25, default='ETB')
    email = models.EmailField(null=True, blank=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    payment_title = models.CharField(max_length=255, default='Payment')
    status = models.CharField(max_length=50, default='created')
    response_dump = models.JSONField(default=dict, blank=True)
    checkout_url = models.URLField(null=True, blank=True)
    callback_url = models.URLField(default='http://localhost:8000/payment-callback/', blank=True)

    def __str__(self):
        return f"{self.first_name} - {self.last_name} | {self.amount}"

    def serialize(self) -> dict:
        return {
            'amount': self.amount,
            'currency': self.currency,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }

class UserActivity(models.Model):
    ACTION_CHOICES = (
        ('login', 'Login'),
        ('quiz', 'Quiz Attempt'),
        ('payment', 'Payment'),
        # Add more actions as needed
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"


# 🔹 Analytics for Quiz Performance
class QuizAnalytics(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    total_attempts = models.IntegerField(default=0)
    average_score = models.FloatField(default=0)

    def __str__(self):
        return f"{self.category.name} - Attempts: {self.total_attempts} - Avg Score: {self.average_score}"


class Candidate(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('banned', 'Banned'),
        ],
        default='active'
    )
    total_score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
