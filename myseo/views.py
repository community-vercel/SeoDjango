from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Website,LighthouseReport
from .serializers import WebsiteSerializer, CrawlHistorySerializer
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import permissions, status
from .models import Website
from .serializers import WebsiteSerializer
from django.contrib.auth.views import PasswordResetConfirmView
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import os
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import requests
from django.http import JsonResponse
from django.utils import timezone
from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now
import requests
from .models import Website
from django.conf import settings
from bs4 import BeautifulSoup
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Website, Page,CrawlHistory
from .serializers import PageSerializer
from urllib.parse import urljoin, urlparse
import time
import re
from collections import deque
from requests.exceptions import RequestException
from django.utils.timezone import now
from django.contrib.auth.views import PasswordResetConfirmView

import requests
from bs4 import BeautifulSoup
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Website
from .serializers import WebsiteSerializer
import subprocess
import json

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_website(request):
    if request.method == 'POST':
        url = request.data.get('url')
        verification_method = request.data.get('verification_method')
        verification_meta = request.data.get('verification_token', '')
        verification_file = request.FILES.get('verification_file')

        # Check if the website already exists for the user
        if Website.objects.filter(user=request.user, url=url).exists():
            return Response({'detail': 'This website has already been added.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the website based on verification method
        if verification_method == 'file' and verification_file:
            website = Website.objects.create(
                user=request.user,
                url=url,
                verification_method='file',
                verification_file=verification_file
            )
        else:
            website = Website.objects.create(
                user=request.user,
                url=url,
                verification_method='meta',
                verification_meta=verification_meta,
            )

        return Response(WebsiteSerializer(website).data, status=status.HTTP_201_CREATED)    
    return Response({'detail': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_websites(request):
    websites = Website.objects.filter(user=request.user)  # Filter by logged-in user
    serializer = WebsiteSerializer(websites, many=True)   # Serialize the queryset
    return Response(serializer.data, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_website(request, website_id):
    try:
        website = Website.objects.get(id=website_id, user=request.user)  # Ensure the user owns the website
    except Website.DoesNotExist:
        return Response({"detail": "Website not found or you're not authorized to view it."}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(WebsiteSerializer(website).data, status=status.HTTP_200_OK)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_website(request, website_id):
    try:
        website = Website.objects.get(id=website_id, user=request.user)  # Ensure the user owns the website
    except Website.DoesNotExist:
        return Response({"detail": "Website not found or you're not authorized to update it."}, status=status.HTTP_404_NOT_FOUND)
    
    # Update fields based on provided data
    url = request.data.get('url', website.url)
    verification_method = request.data.get('verification_method', website.verification_method)
    verification_meta = request.data.get('verification_meta', website.verification_meta)
    verification_file = request.FILES.get('verification_file', website.verification_file)

    # Update the website instance
    website.url = url
    website.verification_method = verification_method
    website.verification_meta = verification_meta if verification_method == 'meta' else website.verification_meta
    website.verification_file = verification_file if verification_method == 'file' else website.verification_file
    
    # Save the updated website
    website.save()

    # Return the updated website data
    return Response(WebsiteSerializer(website).data, status=status.HTTP_200_OK)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_website(request, website_id):
    try:
        website = Website.objects.get(id=website_id, user=request.user)  # Ensure the user owns the website
    except Website.DoesNotExist:
        return Response({"detail": "Website not found or you're not authorized to delete it."}, status=status.HTTP_404_NOT_FOUND)
    
    website.delete()  # Delete the website
    return Response({"detail": "Website deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    user = User.objects.create_user(username=username, email=email, password=password)
    print('hi')
    print(user)
    token = Token.objects.create(user=user)
    print(token)
    return Response({'token': token.key}, status=status.HTTP_201_CREATED)

@csrf_exempt
@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
@csrf_exempt
@api_view(['POST'])
def password_reset_request(request):
    if request.method == 'POST':
        email = request.data.get('email')
       
        user = User.objects.filter(email=email).first()
     
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"ortal.sharplogicians.com/reset/{uid}/{token}"

            send_mail(
                'Password Reset Request',
                f'Click the link below to reset your password:\n{reset_url}',
                'your_email@gmail.com',
                [email],
                fail_silently=False,
            )
            return JsonResponse({'message': 'Password reset link sent to your email.'})

        return JsonResponse({'error': 'Email not registered.'}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class API_PasswordResetConfirmView(PasswordResetConfirmView):

   
    def post(self, request, uidb64, token, *args, **kwargs):
        # Use the built-in form to validate uid/token and set the new password.
        form = self.get_form()
        print(form)
        if form.is_valid():
            self.user = form.save()
            return JsonResponse({'message': 'Password has been reset successfully.'})
        else:
            return JsonResponse(form.errors, status=400)
class ProfessionalWebCrawlAPIView(APIView):
    """
    API to perform web crawling on a specific website with a daily crawl limit.
    """

    def get(self, request, website_id):
        try:
            # Fetch website details
            website = Website.objects.get(id=website_id)

            # Check crawl limit
            if not CrawlHistory.can_crawl(website):
                return Response(
                    {"error": "Daily crawl limit reached (5 per day) please try again tomorrow."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # Check if URL is valid
            base_url = website.url
            if not base_url.startswith(("http://", "https://")):
                return Response({"error": "Invalid website URL."}, status=status.HTTP_400_BAD_REQUEST)

            # Perform the crawl
            crawled_pages = self.crawl_website(base_url)

            # Save crawl history for this crawl session
            # crawl_history = CrawlHistory.objects.create(website=website)

            pages_data = []
            for page in crawled_pages:
                # Save or update page information
                page_obj, created = Page.objects.update_or_create(
                    website=website,
                    url=page['url'],
                    defaults={
                        "status": page['status'],
                        "title": page.get('title', ''),
                        "description": page.get('description', ''),
                        "keywords": page.get('keywords', ''),
                        "h1": page.get('h1', ''),
                        "h2": page.get('h2', ''),
                        "h3": page.get('h3', ''),
                    },
                )

                # Create a new CrawlHistory record for the page
                # CrawlHistory.objects.create(website=website, page=page_obj, timestamp=crawl_history.timestamp)
                CrawlHistory.objects.create(website=website, page=page_obj, timestamp=timezone.now())

                pages_data.append(page_obj)

            serializer = PageSerializer(pages_data, many=True)
            return Response({"pages": serializer.data}, status=status.HTTP_200_OK)

        except Website.DoesNotExist:
            return Response({"error": "Website not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def crawl_website(self, base_url, max_depth=2):
        """
        Perform crawling starting from the base URL.

        Args:
            base_url (str): The starting point for crawling.
            max_depth (int): Depth of crawling.

        Returns:
            list: A list of crawled pages with their URLs and statuses.
        """
        visited = set()
        to_visit = deque([(base_url, 0)])
        crawled_pages = []
        domain = urlparse(base_url).netloc

        while to_visit:
            current_url, depth = to_visit.popleft()
            if current_url in visited or depth > max_depth:
                continue

            visited.add(current_url)
            try:
                response = requests.get(current_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    links = soup.find_all("a", href=True)
                    for link in links:
                        full_url = urljoin(current_url, link["href"])
                        if domain in urlparse(full_url).netloc and full_url not in visited:
                            to_visit.append((full_url, depth + 1))

                    # Extract page details
                    page_title = soup.title.string if soup.title else "No title"
                    meta_description = soup.find("meta", attrs={"name": "description"})
                    meta_description = meta_description["content"] if meta_description else "No description"
                    meta_keywords = soup.find("meta", attrs={"name": "keywords"})
                    meta_keywords = meta_keywords["content"] if meta_keywords else "No keywords"
                    h1_tags = [h1.get_text() for h1 in soup.find_all("h1")]
                    h2_tags = [h2.get_text() for h2 in soup.find_all("h2")]
                    h3_tags = [h3.get_text() for h3 in soup.find_all("h3")]

                    crawled_pages.append({
                        "url": current_url,
                        "status": "success",
                        "title": page_title,
                        "description": meta_description,
                        "keywords": meta_keywords,
                        "h1": h1_tags,
                        "h2": h2_tags,
                        "h3": h3_tags,
                    })
                else:
                    crawled_pages.append({"url": current_url, "status": f"HTTP {response.status_code}"})
            except RequestException as e:
                crawled_pages.append({"url": current_url, "status": f"Error: {str(e)}"})

            # Respect crawl delay
            time.sleep(1)

        return crawled_pages
class CrawlHistoryAPIView(APIView):
    """
    API to retrieve the crawl history for all websites or a specific website.
    """

    def get(self, request):
        website_id = request.query_params.get('website_id')

        try:
            if website_id:
                # Filter crawl histories by specific website
                website = Website.objects.get(id=website_id)
                crawl_histories = CrawlHistory.objects.filter(website=website).order_by('-timestamp')[:5]

            # Serialize the crawl history data
                serializer = CrawlHistorySerializer(crawl_histories, many=True)
                return Response({"crawl_history": serializer.data}, status=status.HTTP_200_OK)

            else:
                # Retrieve all crawl histories
                histories = CrawlHistory.objects.all()

            serializer = CrawlHistorySerializer(histories, many=True)
            return Response({"histories": serializer.data}, status=status.HTTP_200_OK)

        except Website.DoesNotExist:
            return Response({"error": "Website not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WebsiteViewSet(viewsets.ModelViewSet):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically assign the user to the website during creation
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def lighthouse(self, request, pk=None):
        website = self.get_object()
        url = website.url
        form_factor = request.query_params.get('form_factor', 'mobile').lower()
        if form_factor not in ['mobile', 'desktop']:
            return Response({'error': 'Invalid form_factor. Use "mobile" or "desktop".'}, status=status.HTTP_400_BAD_REQUEST)



        try:
            node_path = r"C:\node-v20.18.3-win-x64\node.exe"
            lighthouse_path = r"C:\node-v20.18.3-win-x64\lighthouse.cmd"
            
            # Use a minimal Puppeteer script that waits for the page to load but not too long
            puppeteer_script = '''
                const puppeteer = require('puppeteer');
                const args = process.argv.slice(2);

                (async () => {
                    const browser = await puppeteer.launch({
                        args: ['--no-sandbox', '--disable-setuid-sandbox']
                    });
                    const page = await browser.newPage();
                    const url = args[0];

                    await page.goto(url, { waitUntil: 'networkidle0', timeout: 70000 });  // Wait for DOMContentLoaded only
                    await browser.close();
                })();
            '''

            # Save Puppeteer script to a temporary file
            puppeteer_script_path = 'puppeteer_script.js'
            with open(puppeteer_script_path, 'w') as script_file:
                script_file.write(puppeteer_script)
                
         

            # Run Puppeteer to pre-load the page
            subprocess.run(
                ['node', puppeteer_script_path, url],
                check=True,
                timeout=300  # Set timeout to 30 seconds for Puppeteer
            )

            # Run Lighthouse with minimal options to speed up the analysis
            result = subprocess.run(
                [
                    lighthouse_path,
                    url,
                    '--output=json',
                    '--quiet',
                    '--only-categories=performance,seo,accessibility,pwa',  # Add pwa and best-practices categories
                    f'--emulated-form-factor={form_factor}',  # Use mobile or desktop form factor
                    '--chrome-flags=--headless --disable-gpu --no-sandbox --disable-software-rasterizer',
                    '--max-wait-for-load=30000',  # Reduce load wait time to 10 seconds
                ],
                capture_output=True,
                text=True,
                timeout=300,  # Set a strict timeout of 30 seconds for Lighthouse
            )

            if result.returncode != 0:
                return Response({'error': result.stderr}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if not result.stdout:
                return Response({'error': 'No output from Lighthouse'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            lighthouse_report = json.loads(result.stdout)

            # Extract key metrics
            metrics = {
                'performance': lighthouse_report.get('categories', {}).get('performance', {}).get('score'),
                'seo': lighthouse_report.get('categories', {}).get('seo', {}).get('score'),
                'accessibility': lighthouse_report.get('categories', {}).get('accessibility', {}).get('score'),
                'pwa': lighthouse_report.get('categories', {}).get('pwa', {}).get('score'),
                # 'best-practices': lighthouse_report.get('categories', {}).get('best-practices', {}).get('score'),
          
            }
            audit_metrics = lighthouse_report.get('audits', {})
            detailed_metrics = {
                'first_contentful_paint': audit_metrics.get('first-contentful-paint', {}).get('displayValue'),
                'largest_contentful_paint': audit_metrics.get('largest-contentful-paint', {}).get('displayValue'),
                'total_blocking_time': audit_metrics.get('total-blocking-time', {}).get('displayValue'),
                'cumulative_layout_shift': audit_metrics.get('cumulative-layout-shift', {}).get('displayValue'),
                'speed_index': audit_metrics.get('speed-index', {}).get('displayValue'),
            }
            lighthouse_report_obj = LighthouseReport.objects.create(
                website=website,
                form_factor=form_factor,
                performance_score=metrics['performance'],
                seo_score=metrics['seo'],
                accessibility_score=metrics['accessibility'],
                pwa_score='3',
                first_contentful_paint=detailed_metrics['first_contentful_paint'],
                largest_contentful_paint=detailed_metrics['largest_contentful_paint'],
                total_blocking_time=detailed_metrics['total_blocking_time'],
                cumulative_layout_shift=detailed_metrics['cumulative_layout_shift'],
                speed_index=detailed_metrics['speed_index']
            )

            response_data = {
            'form_factor': form_factor,

            'scores': metrics,
            'metrics': detailed_metrics,
            'report_id': lighthouse_report_obj.id  # Include the report ID in the response

        }

        # return Response(response_data, status=status.HTTP_200_OK)


            return Response(response_data, status=status.HTTP_200_OK)

        except subprocess.TimeoutExpired:
            return Response({'error': 'Lighthouse or Puppeteer timed out while analyzing the page.'}, status=status.HTTP_504_GATEWAY_TIMEOUT)

        except subprocess.CalledProcessError as e:
            return Response({'error': f'Puppeteer failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WebsiteViewSets(viewsets.ModelViewSet):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically assign the user to the website during creation
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def seo_audit(self, request, pk=None):
        website = self.get_object()
        url = website.url

        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract meta tags
            meta_tags = {
                'title': soup.title.string if soup.title else 'N/A',
                'description': soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else 'N/A',
                'keywords': soup.find('meta', attrs={'name': 'keywords'})['content'] if soup.find('meta', attrs={'name': 'keywords'}) else 'N/A',
                'robots': soup.find('meta', attrs={'name': 'robots'})['content'] if soup.find('meta', attrs={'name': 'robots'}) else 'N/A',
                'og_title': soup.find('meta', attrs={'property': 'og:title'})['content'] if soup.find('meta', attrs={'property': 'og:title'}) else 'N/A',
                'og_description': soup.find('meta', attrs={'property': 'og:description'})['content'] if soup.find('meta', attrs={'property': 'og:description'}) else 'N/A',
            }

            # Extract headings
            headings = {
                'h1': ', '.join([h1.get_text() for h1 in soup.find_all('h1')]),
                'h2': ', '.join([h2.get_text() for h2 in soup.find_all('h2')]),
                'h3': ', '.join([h3.get_text() for h3 in soup.find_all('h3')])
            }

            # Extract content quality metrics
            text_content = soup.get_text()
            word_count = len(text_content.split())
            keyword_density = self.calculate_keyword_density(text_content, meta_tags['keywords'])
            readability = self.calculate_readability(text_content)

            content_quality = {
                'wordCount': word_count,
                'keywordDensity': keyword_density,
                'readability': readability
            }

            # Extract image optimization metrics
            images = soup.find_all('img')
            image_optimization = {
                'totalImages': len(images),
                'missingAlt': len([img for img in images if not img.has_attr('alt')]),
                'optimizedAlt': len([img for img in images if img.has_attr('alt')])
            }

            # Extract URL structure metrics
            url_structure = {
                'urlLength': len(url),
                'hasHttps': 'Yes' if url.startswith('https') else 'No',
                'hasTrailingSlash': 'Yes' if url.endswith('/') else 'No'
            }

            # Extract internal linking metrics
            internal_links = [a['href'] for a in soup.find_all('a', href=True) if url in a['href']]
            internal_linking = {
                'internalLinksCount': len(internal_links),
                'internalLinks': internal_links
            }

            # Extract technical SEO metrics
            technical_seo = {
                'pageSpeed': self.calculate_page_speed(url),
                'mobileFriendliness': self.check_mobile_friendliness(url),
                'schemaMarkup': 'Implemented' if soup.find('script', type='application/ld+json') else 'Not Implemented',
                'robotsTxt': self.check_robots_txt(url),
                'xmlSitemaps': self.check_sitemap(url),
                'brokenLinks': self.find_broken_links(soup, url)
            }

            # Extract security metrics
            security = {
                'https': 'Enabled' if url.startswith('https') else 'Disabled',
                'httpSecurityHeaders': self.check_http_security_headers(url)
            }

            # Extract accessibility metrics
            accessibility = {
                'ariaRoles': 'Implemented' if soup.find_all(attrs={'aria-role': True}) else 'Not Implemented',
                'contrastRatio': self.check_color_contrast(soup)
            }

            audit_data = {
                'metaTags': meta_tags,
                'headings': headings,
                'contentQuality': content_quality,
                'imageOptimization': image_optimization,
                'urlStructure': url_structure,
                'internalLinking': internal_linking,
                'technicalSeo': technical_seo,
                'security': security,
                'accessibility': accessibility
            }

            return Response(audit_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def calculate_keyword_density(self, text_content, keywords):
        """ Calculate the keyword density for the page """
        if not keywords:
            return 'N/A'
        keyword_list = keywords.split(',')
        word_count = len(text_content.split())
        keyword_count = sum(text_content.lower().count(keyword.lower()) for keyword in keyword_list)
        return f"{(keyword_count / word_count) * 100:.2f}%" if word_count > 0 else 'N/A'

    def calculate_readability(self, text_content):
        """ Calculate readability score (Flesch–Kincaid or other method) """
        # Placeholder for actual readability scoring logic
        # This could use a library like textstat or similar to calculate readability
        return 'Good'  # Placeholder

    def check_robots_txt(self, url):
        """ Check if the website has a robots.txt file """
        robots_url = f"{url}/robots.txt"
        try:
            response = requests.get(robots_url)
            return 'Configured' if response.status_code == 200 else 'Not Configured'
        except:
            return 'Not Configured'

    def check_sitemap(self, url):
        """ Check if the website has a sitemap.xml file """
        sitemap_url = f"{url}/sitemap.xml"
        try:
            response = requests.get(sitemap_url)
            return 'Present' if response.status_code == 200 else 'Not Present'
        except:
            return 'Not Present'

    def calculate_page_speed(self, url):
        """ Placeholder for actual page speed calculation logic """
        # You can integrate Lighthouse or another tool to check page speed
        return 'Fast'  # Placeholder

    def check_mobile_friendliness(self, url):
        """ Placeholder for actual mobile friendliness check """
        return 'Responsive'  # Placeholder

    def find_broken_links(self, soup, base_url):
        """ Find broken links on the page """
        broken_links = []
        links = [a['href'] for a in soup.find_all('a', href=True)]
        for link in links:
            if not link.startswith('http') or link.startswith(base_url):
                continue
            try:
                response = requests.get(link, timeout=5)
                if response.status_code >= 400:
                    broken_links.append(link)
            except requests.RequestException:
                broken_links.append(link)
        return broken_links

    def check_http_security_headers(self, url):
        """ Check for the presence of important HTTP security headers """
        try:
            response = requests.head(url, timeout=5)
            headers = response.headers
            security_headers = ['Strict-Transport-Security', 'Content-Security-Policy', 'X-Content-Type-Options', 'X-Frame-Options']
            missing_headers = [header for header in security_headers if header not in headers]
            return 'Implemented' if not missing_headers else f'Missing: {", ".join(missing_headers)}'
        except requests.RequestException:
            return 'Not Configured'

    def check_color_contrast(self, soup):
        """ Check for color contrast compliance (dummy logic) """
        return 'Good'  # P
    
@api_view(['GET','POST']) 
def get_latest_lighthouse_reports(request,website_id):
    try:
        # website_id=request.POST.get('id')
        reports = LighthouseReport.objects.filter(website_id=website_id).order_by('-created_at')[:5]

        data = []
        for report in reports:
            data.append({
                'id': report.id,
                'website': report.website.url if report.website else None,
                'performance_score': report.performance_score,
                'seo_score': report.seo_score,
                'form_factor':report.form_factor,
                'accessibility_score': report.accessibility_score,
                'first_contentful_paint': report.first_contentful_paint,
                'largest_contentful_paint': report.largest_contentful_paint,
                'total_blocking_time': report.total_blocking_time,
                'cumulative_layout_shift': report.cumulative_layout_shift,
                'speed_index': report.speed_index,
                'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # Format date
            })

        return JsonResponse(data, safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@api_view(['GET', 'POST'])
def get_history(request, website_id):  # Changed 'website_id' to match the URL parameter
    try:
        if website_id:
            # Filter crawl histories by the specific website using the website_id
            website = Website.objects.get(id=website_id)
            crawl_histories = CrawlHistory.objects.filter(website=website)

            serializer = CrawlHistorySerializer(crawl_histories, many=True)
            return Response({"crawl_history": serializer.data}, status=status.HTTP_200_OK)

        else:
            # Retrieve all crawl histories
            histories = CrawlHistory.objects.all()
            serializer = CrawlHistorySerializer(histories, many=True)
            return Response({"histories": serializer.data}, status=status.HTTP_200_OK)

    except Website.DoesNotExist:
        return Response({"error": "Website not found."}, status=status.HTTP_404_NOT_FOUND)
    
@shared_task
def check_website_status():
    websites = Website.objects.all()

    for website in websites:
        try:
            response = requests.get(website.url, timeout=10)
            
            # If website is up (status code 200)
            if response.status_code == 200:
                if website.status != 'live':
                    website.status = 'live'
                    website.save()

                    # Send email notification about website being live
                    send_mail(
                        'Your Website is Live',
                        f'Good news! Your website {website.url} is back online.',
                        settings.DEFAULT_FROM_EMAIL,
                        [website.user.email],
                        fail_silently=False,
                    )

            else:
                if website.status != 'down':
                    website.status = 'down'
                    website.save()

                    # Send email notification about website being down
                    send_mail(
                        'Your Website is Down',
                        f'Alert! Your website {website.url} is down.',
                        settings.DEFAULT_FROM_EMAIL,
                        [website.user.email],
                        fail_silently=False,
                    )
        except requests.RequestException:
            # If any exception occurs while trying to connect, assume the site is down
            if website.status != 'down':
                website.status = 'down'
                website.save()

                # Send email notification about website being down
                send_mail(
                    'Your Website is Down',
                    f'Alert! Your website {website.url} is down.',
                    settings.DEFAULT_FROM_EMAIL,
                    [website.user.email],
                    fail_silently=False,
                )