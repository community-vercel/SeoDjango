from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField
from django.utils.timezone import now, timedelta

class Website(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField(unique=True)
    verified = models.BooleanField(default=False)
    verification_file = models.ImageField(upload_to='verification_files/', null=True, blank=True)
    verification_meta = models.CharField(max_length=820)
    verification_method = models.CharField(max_length=10, choices=[('meta', 'Meta'), ('file', 'File')], default='meta')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=39, default='pending')

    def __str__(self):
        return self.url
class CrawlHistory(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    @classmethod
    def can_crawl(cls, website):
        """Check if the website can be crawled today."""
        start_of_day = now().replace(hour=0, minute=0, second=0, microsecond=0)
        crawls_today = cls.objects.filter(website=website, timestamp__gte=start_of_day).count()
        return crawls_today < 5

class Page(models.Model):
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='pages')
    url = models.URLField(unique=True)
    status = models.CharField(max_length=50)
    title = models.CharField(max_length=3476, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    h1 = models.TextField(blank=True, null=True)
    h2 = models.TextField(blank=True, null=True)
    h3 = models.TextField(blank=True, null=True)
    og_title = models.CharField(max_length=512, blank=True, null=True)  # Open Graph Title
    og_description = models.TextField(blank=True, null=True)  # Open Graph Description
    canonical_url = models.URLField(blank=True, null=True)  # Canonical URL
    structured_data = models.TextField(blank=True, null=True)  # JSON-LD or Schema.org structured data
    seo_score = models.FloatField(blank=True, null=True)  # SEO score for the page
    accessibility_score = models.FloatField(blank=True, null=True)  # Accessibility score
    readability_score = models.FloatField(blank=True, null=True)  # Readability score
    extracted_images = JSONField(blank=True, null=True)  # List of image URLs
    extracted_scripts = JSONField(blank=True, null=True)  # List of script URLs
    ai_suggestions = JSONField(blank=True, null=True)  # AI-generated suggestions
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url
class CrawlHistory(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE)
    page=models.ForeignKey(Page,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    @classmethod
    def can_crawl(cls, website):
        """Check if the website can be crawled today."""
        start_of_day = now().replace(hour=0, minute=0, second=0, microsecond=0)
        crawls_today = cls.objects.filter(website=website, timestamp__gte=start_of_day).count()
        return crawls_today < 5

class LighthouseReport(models.Model):
    website = models.ForeignKey(Website, related_name="lighthouse_reports", on_delete=models.CASCADE)
    form_factor = models.CharField(max_length=10, choices=[('mobile', 'Mobile'), ('desktop', 'Desktop')])
    performance_score = models.FloatField()
    seo_score = models.FloatField()
    accessibility_score = models.FloatField()
    pwa_score = models.FloatField()

    # Detailed metrics
    first_contentful_paint = models.CharField(max_length=20)
    largest_contentful_paint = models.CharField(max_length=20)
    total_blocking_time = models.CharField(max_length=20)
    cumulative_layout_shift = models.CharField(max_length=20)
    speed_index = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Lighthouse Report for {self.website.url} ({self.form_factor})"