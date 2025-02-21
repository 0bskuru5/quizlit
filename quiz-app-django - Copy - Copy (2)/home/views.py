from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from . models import *
from django.http import JsonResponse, HttpResponseNotFound
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q
import chapa
import uuid
import time
from django.conf import settings
from .chapa_api import ChapaAPI


# Create your views here.

@login_required
def index(request):
    categories = Category.objects.all()
    context = {'categories': categories, 'homeactive': True}
    category_text = request.GET.get('category')
    if category_text:
        user = request.user
        quiz_query = Quiz.objects.filter(
        Q(user=user) & Q(category__name=category_text)  # ✅ Correct lookup
        )


        if not quiz_query.exists():
            category = Category.objects.get(name=category_text)
            quiz = Quiz.objects.create(
                user=user, total_marks=0, category=category, marks=0)
            quiz.save()
        else:
            quiz = quiz_query.first()
        return redirect(f'quiz/?category={category_text}')

    return render(request, 'home/index.html', context)


@login_required
def check_answer(request, uid, createObj):
    try:
        payload = {'status': 200}
        answer = Answer.objects.get(uid=str(uid))
        if createObj == 'true':
            question = GivenQuizQuestions.objects.get_or_create(
                question=answer.question, answer=answer)[0]
            quiz = Quiz.objects.get(
                user=request.user, category=answer.question.category)
            is_already_given = Quiz.objects.filter(
                Q(user=request.user) & Q(
                    given_question__question=question.question)
            ).exists()

            if not is_already_given:
                quiz.given_question.add(question)
                quiz.save()
            else:
                payload = {'status': 404}
            payload['marks'] = quiz.marks
        else:
            payload = {'status': 404}
        if answer.is_correct:
            payload['is_correct'] = 'true'
        else:
            payload['is_correct'] = 'false'

        return JsonResponse(payload)
    except Exception as e:

        return JsonResponse({'status': 404})


def quiz(request):
    try:
        category_name = request.GET.get('category')  # Get category name from URL
        questions = Question.objects.all()
        quiz = None  # Initialize quiz variable
        category = None  # Initialize category variable

        if category_name:
            category = get_object_or_404(Category, name=category_name)  # Fetch category
            quiz = Quiz.objects.filter(user=request.user, category=category).first()  # Get user's quiz

            if quiz:
                # Ensure no recursive save calls
                quiz.calculate_marks()
                total_marks, total_questions = quiz.category.get_total()
                Quiz.objects.filter(uid=quiz.uid).update(marks=quiz.marks)

            questions = questions.filter(category__name__icontains=category_name)

        # Pagination Logic
        p = Paginator(questions, 1)
        page_no = request.GET.get('page', 1)  # Default to page 1
        page_obj = p.get_page(page_no)

        context = {
            'page_obj': page_obj,
            'category': category,
            'quiz': quiz,
            'homeactive': True
        }

        return render(request, 'home/quiz.html', context)

    except Exception as e:
        return HttpResponse(f"Something Went Wrong ---> {str(e)}")


def sign_up(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password1']
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username, password=password)
            user.save()
            messages.success(request, 'Signuped successfully.')
            return redirect('sign_in')
        messages.error(
            request, 'User already exist try with different username.')
    return render(request, 'home/signup.html', {'sign_up_active': True})


def sign_in(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if (user):
            login(request, user)
            messages.success(request, 'Signined Successfully.')
            return redirect('index')
        messages.error(request, 'Enter valid username or password.')
    return render(request, 'home/signin.html', {'sign_in_active': True})


def sign_out(request):
    logout(request)
    return redirect('/')


def loadAttendedQuestionData(request, uid):
    context = {}
    try:
        givenQuiz = Quiz.objects.filter(
            Q(user=request.user) & Q(given_question__question__uid=uid)
        )
        is_question_attened = givenQuiz.exists()

        payload = []
        context['status'] = 404
        if is_question_attened:
            context['status'] = 200
            quiz = givenQuiz[0]
            all_given_questions = quiz.given_question.all()
            all_given_questions = all_given_questions.filter(question__uid=uid)
            given_answer = all_given_questions.first().answer
            for i in all_given_questions.first().question.answers.all():
                if i == given_answer:
                    payload.append({'uid': str(i.uid), 'isCorrect': str(
                        i.is_correct), 'isSelected': 'true'})
                else:
                    payload.append({'uid': str(i.uid), 'isCorrect': str(
                        i.is_correct), 'isSelected': 'false'})
        context['payload'] = payload

    except:
        context['status'] = 404
    return JsonResponse(context)

def quiz_activity(request):
    quizzes = Quiz.objects.all()  # Fetch all quizzes or apply filters as needed
    return render(request, 'quiz_activity.html', {'quizzes': quizzes})

# Initialize Chapa with the secret key
chapa.api_key = settings.CHAPA_API_KEY

def initiate_payment(request):
    Payment.objects.create( 
        user=request.user,
        first_name='John',  # Adjust as needed
        last_name='Doe',  # Adjust as needed
        email='johndoe@gmail.com',
        amount=1000,  # Adjust amount as needed
        status='pending'
    )
    transaction_id = Payment.objects.last().id
    if not transaction_id:
        return HttpResponseNotFound("Transaction ID is required")

    try:
        transaction = Payment.objects.get(id=transaction_id)
    except Payment.DoesNotExist:
        return HttpResponseNotFound("Transaction not found")

    response = ChapaAPI.initialize_payment(transaction)
    if response.get('status') == 'success':
        return render(request, 'payment_initiated.html', {
            'checkout_url': response['data']['checkout_url']
        })

    return HttpResponseNotFound("Payment initiation failed")


def check_payment_status(request, transaction_id):
    try:
        transaction = Payment.objects.get(id=transaction_id)
    except Payment.DoesNotExist:
        return HttpResponseNotFound("Transaction not found")

    response = ChapaAPI.verify_payment(transaction)
    return render(request, 'payment_status.html', {'response': response})


def payment_result(request):
    transaction_id = request.GET.get('transaction_id')
    if not transaction_id:
        return JsonResponse({"status": "failed", "message": "Transaction ID not provided."})

    try:
        transaction = Payment.objects.get(id=transaction_id)
        if transaction.status == 'success':
            transaction.status = 'paid'
            transaction.save()
            return JsonResponse({"status": "success", "message": "Payment completed successfully."})
        return JsonResponse({"status": "failed", "message": "Payment not successful."})
    except Payment.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Transaction ID not found."})


def payment_callback(request):
    payment_reference = request.GET.get("tx_ref")
    if not payment_reference:
        return JsonResponse({"status": "failed", "message": "Transaction reference not provided"})

    transaction = Payment.objects.filter(id=payment_reference).first()
    if transaction:
        response = ChapaAPI.verify_payment(transaction)
        if response.get("status") == "success":
            transaction.status = 'completed'
            transaction.save()
            return redirect('/')
        return JsonResponse({"status": "failed", "message": "Payment verification failed"})
    
    return JsonResponse({"status": "failed", "message": "Transaction not found"})


def return_payment(request):
    payment_reference = request.GET.get("tx_ref")
    if not payment_reference:
        return render(request, 'payment_failed.html', {'message': 'Transaction reference not found in URL.'})

    transaction = Payment.objects.filter(id=payment_reference).first()
    if transaction and transaction.status == 'completed':
        return render(request, 'payment_success.html', {'transaction': transaction})
    
    return render(request, 'payment_failed.html', {'message': 'Transaction not found or payment failed.'})


def payment_result_detail(request, transaction_id):
    transaction = get_object_or_404(Payment, id=transaction_id)
    return render(request, 'payment_result.html', {'transaction': transaction})