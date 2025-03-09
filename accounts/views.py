import json


from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q as models_Q
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AccountBookForm, SignUpForm, TransactionForm
from .models import AccountBook, Transaction


def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "accounts/landing.html")


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")

            # Create default account book for new user
            AccountBook.objects.create(user=user, name="Personal Account", description="Default personal account book")

            return redirect("dashboard")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")  # Redirect to dashboard after successful login
        else:
            messages.error(request, "Your login credentials are incorrect. Are you new here? Please sign up!")

    return render(request, "accounts/login.html")


@login_required
def dashboard(request):

    # Get all account books for the user
    account_books = AccountBook.objects.filter(user=request.user).order_by("-created_at")

    # If user has no account books, create a default one
    if not account_books.exists():
        default_book = AccountBook.objects.create(
            user=request.user, name="Personal Account", description="Default personal account book"
        )
        account_books = [default_book]

    # Get summary data for each account book
    books_data = []
    for book in account_books:
        transactions = Transaction.objects.filter(account_book=book)
        income = transactions.filter(type="income").aggregate(Sum("amount"))["amount__sum"] or 0
        expenses = transactions.filter(type="expense").aggregate(Sum("amount"))["amount__sum"] or 0

        books_data.append(
            {
                "book": book,
                "income": income,
                "expenses": expenses,
                "balance": income - expenses,
            }
        )

    context = {
        "books_data": books_data,
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
def account_book_detail(request, book_id):
    account_book = get_object_or_404(AccountBook, id=book_id, user=request.user)
    transactions = Transaction.objects.filter(account_book=account_book)

    # Calculate totals
    income = transactions.filter(type="income").aggregate(Sum("amount"))["amount__sum"] or 0
    expenses = transactions.filter(type="expense").aggregate(Sum("amount"))["amount__sum"] or 0
    balance = income - expenses

    # Daily trend data for graph
    daily_data = list(
        transactions.values("date")
        .annotate(
            total_income=Sum("amount", filter=models_Q(type="income")),
            total_expenses=Sum("amount", filter=models_Q(type="expense")),
        )
        .order_by("date")
    )

    # Convert to JSON format for JavaScript
    daily_data_json = json.dumps(daily_data, default=str)

    context = {
        "account_book": account_book,
        "transactions": transactions,
        "income": income,
        "expenses": expenses,
        "balance": balance,
        "daily_data_json": daily_data_json,  # Send serialized JSON data
    }
    return render(request, "accounts/account_book_detail.html", context)


@login_required
def create_account_book(request):
    if request.method == "POST":
        form = AccountBookForm(request.POST)
        if form.is_valid():
            account_book = form.save(commit=False)
            account_book.user = request.user
            account_book.save()
            messages.success(request, "Account book created successfully!")
            return redirect("dashboard")
    else:
        form = AccountBookForm()

    return render(request, "accounts/create_account_book.html", {"form": form})


@login_required
def add_transaction(request, book_id):
    account_book = get_object_or_404(AccountBook, id=book_id, user=request.user)

    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.account_book = account_book
            transaction.save()
            messages.success(request, "Transaction added successfully!")
            return redirect("account_book_detail", book_id=book_id)
    else:
        form = TransactionForm()

    return render(request, "accounts/add_transaction.html", {"form": form, "account_book": account_book})


@login_required
def transaction_history(request):
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, "accounts/transaction_history.html", {"transactions": transactions})


@login_required
def delete_account_book(request, book_id):
    account_book = get_object_or_404(AccountBook, id=book_id, user=request.user)
    account_book.delete()
    messages.success(request, "Account book deleted successfully!")
    return redirect("dashboard")


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("landing")
