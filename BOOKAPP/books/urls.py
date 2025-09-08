from django.urls import path
from .views import AuthorView, AuthorListView, VendorView, VendorListView, BookListView,BookCreateView, CreateOrders
urlpatterns = [
    path('createauthor/', AuthorView.as_view(), name='author_create'),
    path('getauthors/', AuthorListView.as_view(), name='author_list'),
    path('createvendor/', VendorView.as_view(), name='vendor_create'),
    path('getvendors/', VendorListView.as_view(), name='vendor_list'),
    # URL like /getbooks/page/1/
    path('getbooks/', BookListView.as_view(), name='book_list_paginated'),
    path('createbook/', BookCreateView.as_view(), name='book_create'),
    path('createorder/', CreateOrders.as_view(), name= 'order_create')
    
]