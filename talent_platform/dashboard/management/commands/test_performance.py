from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import override_settings
from django.utils import timezone
import time
from profiles.models import TalentUserProfile, VisualWorker, ExpressiveWorker, HybridWorker, Band
from dashboard.search_views import (
    TalentUserProfileSearchView, 
    VisualWorkerSearchView, 
    ExpressiveWorkerSearchView, 
    HybridWorkerSearchView,
    BandSearchView
)

class Command(BaseCommand):
    help = 'Test performance improvements for search views'

    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=5,
            help='Number of iterations to run for each test'
        )

    def handle(self, *args, **options):
        iterations = options['iterations']
        
        self.stdout.write(self.style.SUCCESS(f'Testing performance improvements with {iterations} iterations'))
        
        # Test data setup
        self.stdout.write('Setting up test data...')
        
        # Test 1: TalentUserProfile Search
        self.test_talent_profile_search(iterations)
        
        # Test 2: VisualWorker Search
        self.test_visual_worker_search(iterations)
        
        # Test 3: ExpressiveWorker Search
        self.test_expressive_worker_search(iterations)
        
        # Test 4: HybridWorker Search
        self.test_hybrid_worker_search(iterations)
        
        # Test 5: Band Search
        self.test_band_search(iterations)
        
        self.stdout.write(self.style.SUCCESS('Performance testing completed!'))

    def test_talent_profile_search(self, iterations):
        self.stdout.write('\n=== Testing TalentUserProfile Search ===')
        
        view = TalentUserProfileSearchView()
        
        # Test without filters
        times = []
        for i in range(iterations):
            start_time = time.time()
            queryset = view.get_queryset()
            list(queryset[:10])  # Get first 10 results
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        self.stdout.write(f'Average time (no filters): {avg_time:.4f}s')
        
        # Test with filters
        times = []
        for i in range(iterations):
            start_time = time.time()
            queryset = view.get_queryset().filter(
                account_type='gold',
                is_verified=True,
                profile_complete=True
            )
            list(queryset[:10])
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        self.stdout.write(f'Average time (with filters): {avg_time:.4f}s')

    def test_visual_worker_search(self, iterations):
        self.stdout.write('\n=== Testing VisualWorker Search ===')
        
        view = VisualWorkerSearchView()
        
        # Test without filters
        times = []
        for i in range(iterations):
            start_time = time.time()
            queryset = view.get_queryset()
            list(queryset[:10])
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        self.stdout.write(f'Average time (no filters): {avg_time:.4f}s')
        
        # Test with filters
        times = []
        for i in range(iterations):
            start_time = time.time()
            queryset = view.get_queryset().filter(
                primary_category='photographer',
                experience_level='professional',
                years_experience__gte=5
            )
            list(queryset[:10])
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        self.stdout.write(f'Average time (with filters): {avg_time:.4f}s')

    def test_expressive_worker_search(self, iterations):
        self.stdout.write('\n=== Testing ExpressiveWorker Search ===')
        
        view = ExpressiveWorkerSearchView()
        
        # Test without filters
        times = []
        for i in range(iterations):
            start_time = time.time()
            queryset = view.get_queryset()
            list(queryset[:10])
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        self.stdout.write(f'Average time (no filters): {avg_time:.4f}s')
        
        # Test with filters
        times = []
        for i in range(iterations):
            start_time = time.time()
            queryset = view.get_queryset().filter(
                performer_type='actor',
                hair_color='brown',
                eye_color='blue',
                height__gte=170,
                weight__lte=80
            )
            list(queryset[:10])
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        self.stdout.write(f'Average time (with filters): {avg_time:.4f}s')

    def test_hybrid_worker_search(self, iterations):
        self.stdout.write('\n=== Testing HybridWorker Search ===')
        
        view = HybridWorkerSearchView()
        
        # Test without filters
        times = []
        for i in range(iterations):
            start_time = time.time()
            queryset = view.get_queryset()
            list(queryset[:10])
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        self.stdout.write(f'Average time (no filters): {avg_time:.4f}s')
        
        # Test with filters
        times = []
        for i in range(iterations):
            start_time = time.time()
            queryset = view.get_queryset().filter(
                hybrid_type='model',
                fitness_level='advanced',
                risk_levels='moderate',
                height__gte=175,
                weight__lte=75
            )
            list(queryset[:10])
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        self.stdout.write(f'Average time (with filters): {avg_time:.4f}s')

    def test_band_search(self, iterations):
        self.stdout.write('\n=== Testing Band Search ===')
        
        view = BandSearchView()
        
        # Test without filters
        times = []
        for i in range(iterations):
            start_time = time.time()
            queryset = view.get_queryset()
            list(queryset[:10])
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        self.stdout.write(f'Average time (no filters): {avg_time:.4f}s')
        
        # Test with filters
        times = []
        for i in range(iterations):
            start_time = time.time()
            queryset = view.get_queryset().filter(
                band_type='musical',
                member_count__gte=3
            )
            list(queryset[:10])
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        self.stdout.write(f'Average time (with filters): {avg_time:.4f}s') 