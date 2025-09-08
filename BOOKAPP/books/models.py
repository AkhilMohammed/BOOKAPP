from django.db import models
from iam.models import User


class Author(models.Model):
    author = models.OneToOneField(User, on_delete=models.CASCADE, related_name='author_profile')
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.author.first_name} {self.author.last_name} - Author Profile"


class Vendor(models.Model):
    vendor = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    company_name = models.CharField(max_length=255, blank=True)
    company_description = models.TextField(blank=True, null=True)
    company_website = models.URLField(blank=True, null=True)
    company_logo = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.vendor.first_name} {self.vendor.last_name} - Vendor Profile"


class Genre(models.Model):
    genre = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.genre


class Book(models.Model):
    title = models.CharField(max_length=255)
    authors = models.ForeignKey('books.Author', on_delete=models.CASCADE, related_name="books")
    genre = models.ForeignKey('books.Genre', on_delete=models.CASCADE, related_name="books")
    original_publication_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class BookEditions(models.Model):
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name="editions")
    language = models.CharField(max_length=50)
    isbn = models.CharField(max_length=13, unique=True)
    publication_date = models.DateField()
    number_of_pages = models.PositiveIntegerField()
    cover_image = models.ImageField(upload_to="book_covers/", blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    vendor = models.ForeignKey('books.Vendor', on_delete=models.SET_NULL, null=True, related_name="editions")
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.book.title} - {self.language} Edition"

class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("paid", "Paid"), ("shipped", "Shipped"), ("cancelled", "Cancelled"), ("delivered", "Delivered")],
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    edition = models.ForeignKey('books.BookEditions', on_delete=models.CASCADE, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    def get_total_price(self):
        return (self.unit_price - self.discount_amount) * self.quantity
    






