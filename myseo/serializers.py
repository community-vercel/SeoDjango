from rest_framework import serializers
from .models import Website, Page,CrawlHistory

from django.contrib.auth.models import User

class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = ['id', 'url', 'verified', 'verification_file', 'verification_method', 'verification_meta', 'created_at', 'updated_at', 'status']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = [
            "id",
            "website",
            "url",
            "status",
            "title",
            "description",
            "keywords",
            "h1",
            "h2",
            "h3",
            "og_title",
            "og_description",
            "canonical_url",
            "structured_data",
            "seo_score",
            "accessibility_score",
            "readability_score",
            "extracted_images",
            "extracted_scripts",
            "ai_suggestions",
            "created_at",
        ]


class CrawlHistorySerializer(serializers.ModelSerializer):
    website = WebsiteSerializer(read_only=True)
    page = PageSerializer(read_only=True)
    website_url = serializers.CharField(source='website.url', read_only=True)
    page_url = serializers.CharField(source='page.url', read_only=True)

    class Meta:
        model = CrawlHistory
        fields = ['id', 'website', 'website_url', 'page', 'page_url', 'timestamp']