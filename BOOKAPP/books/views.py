from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated  
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Book, Author, Vendor, Genre, BookEditions, Order, OrderItem
from iam.permissions import IsAdminUser,IsSuperAdminUser, IsVendorUser
from rest_framework.permissions import IsAuthenticated 
from .serializers import AuthorSerializer, VendorSerializer, OrderSerializer
from iam.models import User, profile
from datetime import datetime, date

import logging

logger = logging.getLogger(__name__)


# Create your views here.

class AuthorView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, *args, **kwargs):
        try:
            author = request.data.get('author')
            logger.debug("Received author ID: %s", author)
            author_object = CustomUser.objects.get(id=author, is_active=True)
            logger.debug("Author object retrieved: %s", author_object)

            if not author_object:
                return Response({"error": "Author not found or inactive"}, status=status.HTTP_404_NOT_FOUND)
            serializer = AuthorSerializer(data=request.data, context ={'author': author_object})
            if serializer.is_valid():
                logger.debug("Author serializer is valid: %s", serializer.validated_data)
                author_profile = serializer.save()
                return Response({"message": "Author profile created successfully", "author_id": author_profile.id}, status=status.HTTP_201_CREATED)
        except CustomUser.DoesNotExist:
            logger.error("Author with ID %s does not exist", author)
            return Response({"error": "Author does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Error creating author profile: %s", str(e))
            return Response({"error": "An error occurred while creating the author profile"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AuthorListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            authors = Author.objects.all()
            logger.debug("Retrieved authors: %s", authors)

            authors_list = []
            for book_author in authors:
                logger.debug("Processing author: %s", book_author.author_id)
                
                author_object = CustomUser.objects.select_related("profile","author_profile").get(id=book_author.author_id, is_active=True)
                logger.debug("Processing author object: %s", author_object)
                data = {
                    "id": author_object.Author.id,
                    "first_name": author_object.first_name,
                    "last_name": author_object.last_name,
                    "email": author_object.email,
                    "is_active": author_object.is_active,
                    "profile": {
                        "bio": author_object.Author.bio if hasattr(author_object, 'Author') else None,
                        "phone_number": author_object.profile.phone_number if hasattr(author_object, 'profile') else None,
                        "D_no": author_object.profile.D_no if hasattr(author_object, 'profile') else None,
                        "street_name": author_object.profile.street_name if hasattr(author_object, 'profile') else None,
                        "city": author_object.profile.city if hasattr(author_object, 'profile') else None,
                        "state": author_object.profile.state if hasattr(author_object, 'profile') else None,
                        "country": author_object.profile.country if hasattr(author_object, 'profile') else None,
                        "zip_code": author_object.profile.zip_code if hasattr(author_object, 'profile') else None
                    }
                    
                } 
                logger.debug("Author data: %s", data)
                authors_list.append(data)
            return Response({"data" : authors_list},status=status.HTTP_200_OK)
        
        except CustomUser.DoesNotExist:
            logger.error("No active authors found")
            return Response({"error": "No active authors found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Error retrieving authors: %s", str(e))
            return Response({"error": "An error occurred while retrieving authors"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class VendorView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        try:
            Vendor = request.data.get('vendor')
            logger.debug("Received vendor ID: %s", Vendor)
            vendor_object = CustomUser.objects.get(id=Vendor, is_active=True)
            logger.debug("Vendor object retrieved: %s", vendor_object)

            if not vendor_object:
                return Response({"error": "Vendor not found or inactive"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = VendorSerializer(data=request.data, context={'vendor': vendor_object})
            if serializer.is_valid():
                logger.debug("Vendor serializer is valid: %s", serializer.validated_data)
                vendor_profile = serializer.save()
                logger.debug("Vendor profile created: %s", vendor_profile)
                return Response({"message": "Vendor profile created successfully", "vendor_id": vendor_profile.id}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            logger.error("Vendor with ID %s does not exist", Vendor)
            return Response({"error": "Vendor does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Error creating vendor profile: %s", str(e))
            return Response({"error": "An error occurred while creating the vendor profile"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # put and delete methods here if needed


class VendorListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        try:
            vendor_user = request.data.get('vendor')
            if vendor_user:
                vendor_fk = Vendor.objects.get(id = vendor_user) 
                vendor_object = CustomUser.objects.select_related("profile", "vendor_profile").get(id= vendor_fk.vendor_id, is_active=True)
                data = {
                    "id": vendor_object.vendor_profile.id,
                    "first_name": vendor_object.first_name,
                    "last_name": vendor_object.last_name,
                    "email": vendor_object.email,
                    "is_active": vendor_object.is_active,
                    "profile": {
                        "phone_number": vendor_object.profile.phone_number if hasattr(vendor_object, 'profile') else None,
                        "D_no": vendor_object.profile.D_no if hasattr(vendor_object, 'profile') else None,
                        "street_name": vendor_object.profile.street_name if hasattr(vendor_object, 'profile') else None,
                        "city": vendor_object.profile.city if hasattr(vendor_object, 'profile') else None,
                        "state": vendor_object.profile.state if hasattr(vendor_object, 'profile') else None,
                        "country": vendor_object.profile.country if hasattr(vendor_object, 'profile') else None,
                        "zip_code": vendor_object.profile.zip_code if hasattr(vendor_object, 'profile') else None
                    },
                    "vendor_profile": {
                        "company_name": vendor_object.vendor_profile.company_name if hasattr(vendor_object, 'vendor_profile') else None,
                        "company_description": vendor_object.vendor_profile.company_description if hasattr(vendor_object, 'vendor_profile') else None,
                        "company_website": vendor_object.vendor_profile.company_website if hasattr(vendor_object, 'vendor_profile') else None,
                        "company_logo": vendor_object.vendor_profile.company_logo if hasattr(vendor_object, 'vendor_profile') else None
                    }
                }
                logger.debug("Vendor data: %s", data)
                return Response({"data": data}, status=status.HTTP_200_OK)

            vendor_ids = Vendor.objects.values_list("vendor_id", flat=True)
            vendors = CustomUser.objects.filter(id__in=vendor_ids, is_active=True).select_related("profile", "vendor_profile")

            vendors_list = []
            for vendor_object in vendors:
                # logger.debug("Processing vendor: %s", book_vendor.vendor_id)

                # vendor_object = CustomUser.objects.select_related("profile", "vendor_profile").get(id=book_vendor.vendor_id, is_active=True)
                logger.debug("Processing vendor object: %s", vendor_object)
                data = {
                    "id": vendor_object.vendor_profile.id,
                    "first_name": vendor_object.first_name,
                    "last_name": vendor_object.last_name,
                    "email": vendor_object.email,
                    "is_active": vendor_object.is_active
                }
                vendors_list.append(data)
                logger.debug("Vendor data: %s", data)
            return Response({"data": vendors_list}, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            logger.error("No active vendors found")
            return Response({"error": "No active vendors found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Error retrieving vendors: %s", str(e))
            return Response({"error": "An error occurred while retrieving vendors" + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)          

class BookCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        try:
            genre = request.data.get('genre')
            genre_object = Genre.objects.filter(genre = genre.upper().strip()).first()
            logger.debug("Genre object retrieved: %s", genre_object)
            if not genre_object:
                genre_description = request.data.get('genre_description')
                genre_object = Genre.objects.create(genre = genre.upper().strip(), description= genre_description)
                logger.debug("Genre object created: %s", genre_object)
            
            authors = request.data['authors']
            author_object = Author.objects.filter(id = authors).first()
            logger.debug("Author object retrieved: %s", author_object)
            if not author_object:
                return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
            
            vendor = request.data.get('vendor')
            vendor_object = Vendor.objects.filter(id=vendor).first()
            logger.debug("Vendor object retrieved: %s", vendor_object)
            if not vendor_object:
                return Response({"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # BookTitles = Book.objects.all()
            # for b in BookTitles:
            #    logger.debug(f"Bookdata {b.title},{b.authors}") 
            book_title = request.data.get('title').upper().strip()
            logger.info(f"book title retrieved {book_title}")
            book = Book.objects.filter(title=book_title).first()
            logger.info(f'book already exists {book}')
            if book:
                logger.info(f'book already exists, pass this condition {book}')
                pass
            else: 
                book_data = {
                    "title": request.data.get('title').upper().strip(),
                    "authors": author_object,
                    "genre": genre_object,
                    "original_publication_date": request.data.get('original_publication_date')  if request.data.get('original_publication_date') else datetime.now(),
                    "description": request.data.get('description')
                }
                book = Book.objects.create(**book_data)
                logger.debug("Book object created: %s", book)
            edition_data = {
                "book": book,
                "language": request.data.get('language').upper().strip(),
                "isbn": request.data.get('isbn'),
                "publication_date": datetime.now(),
                "number_of_pages": request.data.get('number_of_pages'),
                "cover_image": request.data.get('cover_image'),
                "price": request.data.get('price'),
                "vendor": vendor_object,
                "stock": request.data.get('stock', 0)
            }
            try:
                language = BookEditions.objects.get(book = book,language = request.data.get('language').upper().strip())
                if language:
                    return Response({"message":"language to this book already exists "}, status= status.HTTP_400_BAD_REQUEST)
            except: 
                book_edition = BookEditions.objects.create(**edition_data)
                logger.debug("Book edition object created: %s", book_edition)
                return Response({"message": "Book and edition created successfully", "book_id": book.id, "edition_id": book_edition.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("Error creating book and edition: %s", str(e))
            return Response({"error": "An error occurred while creating the book and edition: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class BookListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            
            page = int(request.data.get("page", 1))   # default = page 1
            page_size = 10
            offset = (page - 1) * page_size
            limit = offset + page_size

            books = (
                Book.objects.all()
                .select_related("authors__author", "genre")
                .prefetch_related("editions__vendor__vendor")
                .order_by("original_publication_date")[offset:limit])
            logger.debug("Retrieved books: %s", books)

            books_list = []
            for book in books:
                logger.debug("Processing book: %s", book.id)
                editions = []
                for edition in book.editions.all():
                    editions.append({
                        "id": edition.id,
                        "language": edition.language,
                        "isbn": edition.isbn,
                        "publication_date": edition.publication_date,
                        "number_of_pages": edition.number_of_pages,
                        "cover_image": edition.cover_image.url if edition.cover_image else None,
                        "price": edition.price,
                        "stock": edition.stock,
                        "vendor": {
                            "id": edition.vendor.id,
                            "first_name": edition.vendor.vendor.first_name if hasattr(edition.vendor, 'vendor') else None,
                            "last_name": edition.vendor.vendor.last_name if hasattr(edition.vendor, 'vendor') else None,
                            "email": edition.vendor.vendor.email if hasattr(edition.vendor, 'vendor') else None,
                            "company_name": edition.vendor.company_name
                        } if edition.vendor else None
                    })
                data = {
                    "id": book.id,
                    "title": book.title,
                    "authors": {
                        "id": book.authors.id,
                        "first_name": book.authors.author.first_name if hasattr(book.authors, 'author') else None,
                        "last_name": book.authors.author.last_name if hasattr(book.authors, 'author') else None,
                        "email": book.authors.author.email if hasattr(book.authors, 'author') else None,
                        "bio": book.authors.bio
                    } if book.authors else None,
                    "genre": {
                        "id": book.genre.id,
                        "genre": book.genre.genre,
                    } if book.genre else None,
                    "original_publication_date": book.original_publication_date,
                    "description": book.description,
                    "editions": editions
                }
                logger.debug("Book data: %s", data)
                books_list.append(data)

            if not books_list:
                return Response({"message": "No books found"}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"data" : books_list},status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error("Error retrieving books: %s", str(e))
            return Response({"error": "An error occurred while retrieving books: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CreateOrders(APIView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = OrderSerializer(data=request.data)
            if serializer.is_valid():
                
                book_id = serializer.validated_date['book']
                book_edition= serializer.validated_data['language']
                try:
                    book_object = Book.objects.get(id = book_id)
                    edition = BookEditions.objects.get(book =book_object, language = book_edition)
                except Exception as e:
                    return Response({"error":"Book Not Found"}, status= status.HTTP_400_BAD_REQUEST)
                
                order= Order.objects.create(
                    total_amount = serializer.validated_data['total_amount'],
                    status = serializer.validated_data['status']
                )
                oder_item = OrderItem.objects.create(
                    edition = edition,
                    order = order,
                    unit_price = serializer.validated_data['unit_price'],
                    discount_amount = serializer.validated_data['discount_amount']    
                )
                return Response({"message":"order has been created"}, status = status.HTTP_200_OK)
            
            return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "An error occurred while retrieving books: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

