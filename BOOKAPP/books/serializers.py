from rest_framework import serializers
from .models import Book, Author, Vendor
from iam.models import User, profile
import logging
logger = logging.getLogger(__name__)

class AuthorSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Author
        fields = ['id', 'author', 'bio']

    def create(self, validated_data):
        logger.debug("Creating author profile with data: %s", validated_data)

        author = self.context.get('author')
        author_data = validated_data.copy()
        author_data['author'] = author
        author_instance = Author.objects.create(**author_data)
        return author_instance
        

class VendorSerializer(serializers.ModelSerializer):
    vendor = serializers.PrimaryKeyRelatedField(read_only=True)
    company_name = serializers.CharField(required=False, allow_blank=True)
    company_description = serializers.CharField(required=False, allow_blank=True)
    company_website = serializers.URLField(required=False, allow_blank=True)
    company_logo = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Vendor
        fields = ['id', 'vendor', 'company_name', 'company_description', 'company_website', 'company_logo']
    
    def create(self, validated_data):
        logger.debug("Creating vendor profile with data: %s", validated_data)
        vendor_instance= self.context.get('vendor')
        Vendor_data = validated_data.copy()
        Vendor_data['vendor'] = vendor_instance
        vendor_instance = Vendor.objects.create(**Vendor_data)
        logger.debug("Vendor profile created: %s", vendor_instance)
        
        return vendor_instance
    
class OrderSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    status = serializers.ChoiceField(choices = [
        ("pending","Pending"),
        ("paid", "Paid"),
        ("shipped","Shipped"),
        ("canceled","Canceled"),
        ("delivered", "Delivered")])
    book = serializers.IntegerField(required=True)
    language = serializers.CharField(required = True)
    quantity = serializers.IntegerField(required = True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

    
