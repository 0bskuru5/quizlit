from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.db.models import Sum, Count
from django.http import JsonResponse
from home.models import User, Quiz, Payment, Category  # Import models from home
from django.contrib import messages
from django.db.models import Avg, Count
from django.http import JsonResponse
from home.models import UserActivity
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.db.models import Count, Sum



# Check if the user is an admin
def is_admin(user):
    return user.is_staff  # Modify this if you have a custom permission system

# Management Dashboard - Candidate Profiles, Quiz Performance, and Payment Status
@login_required
@user_passes_test(is_admin)
def management_dashboard(request):
    candidates = User.objects.filter(is_staff=False)
    candidate_data = []

    for candidate in candidates:
        quizzes = Quiz.objects.filter(user=candidate)
        total_score = quizzes.aggregate(Sum("marks"))["marks__sum"] or 0
        status = "Completed" if quizzes.exists() else "Not Started"
        
        # Get latest payment
        payment = Payment.objects.filter(user=candidate, status="completed").order_by("-created_at").first()
        payment_status = payment.status if payment else "No Payment"

        candidate_data.append({
            "id": candidate.id,
            "username": candidate.username,
            "email": candidate.email,
            "total_score": total_score,
            "status": status,
            "payment_status": payment_status,
        })

    return render(request, "management/dashboard.html", {"candidates": candidate_data})

# Approve Payments
@login_required
@user_passes_test(is_admin)
def approve_payment(request, user_id):
    payment = Payment.objects.filter(user_id=user_id, status="pending").first()
    if payment:
        payment.status = "completed"
        payment.save()
        messages.success(request, "Payment approved successfully.")
    else:
        messages.error(request, "No pending payment found.")
    return redirect("management_dashboard")

# Ensure payment before taking a quiz
@login_required
def check_payment(request, category_id):
    user = request.user
    category = get_object_or_404(Category, id=category_id)

    has_paid = Payment.objects.filter(user=user, category=category, status="completed").exists()
    if not has_paid:
        return JsonResponse({"status": "error", "message": "Payment required for this quiz."}, status=403)

    return JsonResponse({"status": "success"})

# Track Quiz Performance & User Activity
@login_required
@user_passes_test(is_admin)
def quiz_activity(request):
    quiz_data = Quiz.objects.values("category__name").annotate(
        total_quizzes=Count("id"), total_marks=Sum("marks")
    )

    return render(request, "management/quiz_activity.html", {"quiz_data": quiz_data})

# Data Visualization - Popular Books and Quiz Completion Rates
@login_required
@user_passes_test(is_admin)
def data_visualization(request):
    category_data = Category.objects.annotate(
        total_quizzes=Count("quiz")
    ).order_by("-total_quizzes")

    return render(request, "management/data_visualization.html", {"categories": category_data})

def management_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user and user.is_staff:  # Ensuring only admins can log in
            login(request, user)
            return redirect("management_dashboard")
        else:
            messages.error(request, "Invalid credentials or unauthorized access.")
    
    return render(request, "management/login.html")

# Logout Management
def management_logout(request):
    logout(request)
    return redirect("management_login")

def user_activity_log(request):
    activities = UserActivity.objects.all().order_by('-timestamp')  # Fetch all activities, ordered by timestamp
    return render(request, 'management/user_activity_log.html', {'activities': activities})


def candidate_detail(request, id):
    candidate = get_object_or_404(Candidate, id=id)
    return render(request, 'candidate_detail.html', {'candidate': candidate})

def statistics_view(request):
    # Data for the overall statistics
    total_users = User.objects.count()
    total_categories = Category.objects.count()
    total_quizzes = Quiz.objects.count()
    total_money_earned = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0

    # Data for the graph
    labels = ['Total Users', 'Total Categories', 'Total Quizzes Taken', 'Total Money Earned']
    values = [total_users, total_categories, total_quizzes, total_money_earned]

    # Creating the bar chart
    fig, ax = plt.subplots(figsize=(10, 6))

    # Creating the bar chart
    bars = ax.bar(labels, values, color=['#007bff', '#28a745', '#dc3545', '#ffc107'], edgecolor='black')

    # Adding labels and title with better font styles
    ax.set_xlabel('Metrics', fontsize=14, fontweight='bold')
    ax.set_ylabel('Values', fontsize=14, fontweight='bold')
    ax.set_title('Overall Quiz App Statistics', fontsize=16, fontweight='bold')

    # Adding gridlines for better readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Displaying the values on top of the bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f'{yval}', ha='center', va='bottom', fontsize=12)

    # Setting a clean background
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('#f8f9fa')

    # Save plot to a BytesIO object and encode as base64 for embedding in HTML
    img_buf = BytesIO()
    plt.tight_layout()  # Ensure everything fits in the figure neatly
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    img_base64 = base64.b64encode(img_buf.getvalue()).decode('utf-8')
    img_buf.close()

    context = {
        'img_base64': img_base64,
        'total_users': total_users,
        'total_categories': total_categories,
        'total_quizzes': total_quizzes,
        'total_money_earned': total_money_earned,
    }

    return render(request, 'management/statistics.html', context)