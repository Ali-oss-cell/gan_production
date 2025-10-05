from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from faker import Faker
import requests
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction

from users.models import BaseUser
from profiles.models import (
    TalentUserProfile, BackGroundJobsProfile, TalentMedia,
    VisualWorker, ExpressiveWorker, HybridWorker, Band, BandMedia
)
# SharedMediaPost import removed as not needed

class Command(BaseCommand):
    help = 'Generate test users with fake data and Lorem Picsum images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--talent-count',
            type=int,
            default=100,
            help='Number of talent users to create'
        )
        parser.add_argument(
            '--background-count', 
            type=int,
            default=100,
            help='Number of background users to create'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing test users before creating new ones'
        )

    def __init__(self):
        super().__init__()
        self.fake = Faker(['en_US', 'en_GB', 'es_ES', 'fr_FR', 'de_DE'])
        
        # Talent specializations
        self.musician_skills = [
            'Guitar', 'Piano', 'Drums', 'Bass', 'Violin', 'Saxophone', 
            'Trumpet', 'Flute', 'Cello', 'Harmonica'
        ]
        
        self.dance_styles = [
            'Ballet', 'Hip-Hop', 'Contemporary', 'Jazz', 'Salsa', 
            'Breakdancing', 'Tap', 'Ballroom', 'Modern', 'Folk'
        ]
        
        self.singing_genres = [
            'Pop', 'Rock', 'Classical', 'R&B', 'Jazz', 'Country', 
            'Opera', 'Blues', 'Folk', 'Electronic'
        ]
        
        self.acting_types = [
            'Theater', 'Film', 'Television', 'Voice-over', 'Commercial', 
            'Musical Theater', 'Improv', 'Stand-up Comedy'
        ]
        
        # Background specializations
        self.model_types = [
            'Fashion', 'Commercial', 'Fitness', 'Portrait', 'Editorial', 
            'Runway', 'Plus-size', 'Alternative', 'Glamour'
        ]
        
        self.extra_types = [
            'Film Extra', 'TV Extra', 'Commercial Extra', 'Event Staff', 
            'Background Actor', 'Crowd Work', 'Photo Double'
        ]
        
        self.voice_types = [
            'Animation', 'Commercial', 'Audiobook', 'Documentary', 
            'Video Game', 'E-learning', 'IVR', 'Radio'
        ]
        
        self.stunt_types = [
            'Fight Scenes', 'Car Stunts', 'Wire Work', 'Falls', 
            'Fire Stunts', 'Water Work', 'Motorcycle', 'Parkour'
        ]
        
        # Shared media categories
        self.shared_categories = ['featured', 'inspiration', 'trending']
        
        # Equipment and specialization items
        self.equipment_items = {
            'musician': ['Guitar', 'Piano', 'Microphone', 'Audio Interface', 'Studio Monitors'],
            'dancer': ['Dance Shoes', 'Mirrors', 'Barres', 'Sound System', 'Costumes'],
            'singer': ['Microphone', 'Headphones', 'Recording Booth', 'Sheet Music', 'Piano'],
            'actor': ['Scripts', 'Props', 'Costumes', 'Makeup Kit', 'Lighting Equipment'],
            'model': ['Camera', 'Lighting Kit', 'Backdrop', 'Props', 'Wardrobe'],
            'extra': ['Wardrobe', 'Props', 'Makeup', 'Scripts', 'Call Sheets'],
            'voice_actor': ['Microphone', 'Audio Interface', 'Headphones', 'Soundproofing', 'Scripts'],
            'stunt_performer': ['Safety Gear', 'Harnesses', 'Mats', 'Props', 'Protective Equipment']
        }

    def handle(self, *args, **options):
        talent_count = options['talent_count']
        background_count = options['background_count']
        clear_existing = options['clear_existing']
        
        if clear_existing:
            self.stdout.write('Clearing existing test users...')
            self.clear_test_users()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Creating {talent_count} talent users and {background_count} background users...'
            )
        )
        
        with transaction.atomic():
            # Create talent users
            self.create_talent_users(talent_count)
            
            # Create background users  
            self.create_background_users(background_count)
            
            # Note: Shared media creation removed as requested
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {talent_count + background_count} test users with enhanced media!'
            )
        )

    def clear_test_users(self):
        """Clear existing test users (those with test emails)"""
        test_users = BaseUser.objects.filter(email__contains='testuser')
        count = test_users.count()
        test_users.delete()
        self.stdout.write(f'Deleted {count} existing test users')

    def download_image(self, width=200, height=200, user_id=None):
        """Download image from Lorem Picsum"""
        try:
            # Use user_id as seed for consistent images per user
            seed = user_id or random.randint(1, 1000)
            url = f'https://picsum.photos/{width}/{height}?random={seed}'
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return ContentFile(response.content, name=f'profile_{seed}.jpg')
        except Exception as e:
            self.stdout.write(f'Error downloading image: {e}')
        return None

    def create_base_user(self, user_type='talent'):
        """Create a base user with common fields"""
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        email = f'testuser_{user_type}_{random.randint(1000, 9999)}@{self.fake.free_email_domain()}'
        
        # Random verification status (60% verified)
        email_verified = random.random() < 0.6
        
        user = BaseUser.objects.create_user(
            email=email,
            password='testpass123',
            first_name=first_name,
            last_name=last_name,
            phone=self.fake.phone_number()[:20],  # Limit length to match model
            date_of_birth=self.fake.date_of_birth(minimum_age=18, maximum_age=65),
            gender=random.choice(['Male', 'Female', 'Other', 'Prefer not to say']),  # Match model choices
            email_verified=email_verified,
            is_talent=(user_type == 'talent'),
            is_background=(user_type == 'background'),
            is_active=True
        )
        
        return user

    def create_talent_users(self, count):
        """Create talent users with profiles"""
        talent_types = ['musician', 'dancer', 'singer', 'actor']
        users_per_type = count // len(talent_types)
        
        for i, talent_type in enumerate(talent_types):
            type_count = users_per_type + (1 if i < count % len(talent_types) else 0)
            
            for j in range(type_count):
                user = self.create_base_user('talent')
                self.create_talent_profile(user, talent_type)
                
                if j % 10 == 0:
                    self.stdout.write(f'Created {j + 1} {talent_type} users...')

    def create_talent_profile(self, user, talent_type):
        """Create talent profile based on type"""
        # Download profile picture
        profile_image = self.download_image(200, 200, user.id)
        
        # Create base talent profile
        profile = TalentUserProfile.objects.create(
            user=user,
            aboutyou=self.fake.text(max_nb_chars=500),
            city=self.fake.city()[:25],  # Limit to 25 characters
            country=self.fake.country()[:25],  # Limit to 25 characters
            phone=self.fake.phone_number()[:20],  # Limit to 20 characters
            date_of_birth=self.fake.date_of_birth(minimum_age=18, maximum_age=65),
            gender=random.choice(['Male', 'Female', 'Other']),
            profile_complete=random.choice([True, False]),
            is_verified=random.random() < 0.3,  # 30% verified
            account_type=random.choice(['free', 'premium', 'platinum'])
        )
        
        if profile_image:
            profile.profile_picture.save(f'profile_{user.id}.jpg', profile_image)
        
        # Create specialized profiles
        self.create_specialized_talent_profile(user, profile, talent_type)
        
        # Create some media for the profile
        self.create_talent_media(profile, talent_type)

    def create_specialized_talent_profile(self, user, profile, talent_type):
        """Create specialized talent profiles"""
        if talent_type == 'musician':
            VisualWorker.objects.create(
                profile=profile,
                primary_category='composer',
                years_experience=random.randint(1, 20),
                experience_level=random.choice(['beginner', 'intermediate', 'professional', 'expert']),
                portfolio_link=f'https://{self.fake.domain_name()}',
                availability=random.choice(['full_time', 'part_time', 'weekends', 'flexible']),
                rate_range=random.choice(['low', 'mid', 'high', 'negotiable']),
                willing_to_relocate=random.choice([True, False])
            )
        
        elif talent_type == 'dancer':
            ExpressiveWorker.objects.create(
                profile=profile,
                performer_type='dancer',
                years_experience=random.randint(1, 15),
                height=random.uniform(150.0, 190.0),
                weight=random.uniform(45.0, 90.0),
                hair_color=random.choice(['blonde', 'brown', 'black', 'red', 'gray', 'other']),
                hair_type=random.choice(['straight', 'wavy', 'curly', 'coily', 'bald', 'other']),
                skin_tone=random.choice(['fair', 'light', 'medium', 'olive', 'brown', 'dark']),
                eye_color=random.choice(['blue', 'green', 'brown', 'hazel', 'black', 'other']),
                eye_size=random.choice(['small', 'medium', 'large']),
                eye_pattern=random.choice(['normal', 'protruding', 'sunken', 'almond', 'round', 'other']),
                face_shape=random.choice(['oval', 'round', 'square', 'heart', 'diamond', 'long', 'other']),
                forehead_shape=random.choice(['broad', 'narrow', 'rounded', 'straight', 'other']),
                lip_shape=random.choice(['thin', 'full', 'heart', 'round', 'bow', 'other']),
                eyebrow_pattern=random.choice(['arched', 'straight', 'curved', 'thick', 'thin', 'other']),
                voice_type=random.choice(['normal', 'thin', 'rough', 'deep', 'soft', 'nasal', 'other']),
                body_type=random.choice(['athletic', 'slim', 'muscular', 'average', 'plus_size', 'other']),
                availability=random.choice(['full_time', 'part_time', 'evenings', 'weekends'])
            )
        
        elif talent_type == 'singer':
            HybridWorker.objects.create(
                profile=profile,
                hybrid_type='specialty_performer',
                years_experience=random.randint(1, 25),
                height=random.uniform(150.0, 190.0),
                weight=random.uniform(45.0, 90.0),
                hair_color=random.choice(['blonde', 'brown', 'black', 'red', 'gray', 'other']),
                hair_type=random.choice(['straight', 'wavy', 'curly', 'coily', 'bald', 'other']),
                eye_color=random.choice(['blue', 'green', 'brown', 'hazel', 'black', 'other']),
                eye_size=random.choice(['small', 'medium', 'large']),
                eye_pattern=random.choice(['normal', 'protruding', 'sunken', 'almond', 'round', 'other']),
                face_shape=random.choice(['oval', 'round', 'square', 'heart', 'diamond', 'long', 'other']),
                forehead_shape=random.choice(['broad', 'narrow', 'rounded', 'straight', 'other']),
                lip_shape=random.choice(['thin', 'full', 'heart', 'round', 'bow', 'other']),
                eyebrow_pattern=random.choice(['arched', 'straight', 'curved', 'thick', 'thin', 'other']),
                voice_type=random.choice(['normal', 'thin', 'rough', 'deep', 'soft', 'nasal', 'other']),
                skin_tone=random.choice(['fair', 'light', 'medium', 'olive', 'brown', 'dark']),
                body_type=random.choice(['athletic', 'slim', 'muscular', 'average', 'plus_size', 'other']),
                fitness_level=random.choice(['beginner', 'intermediate', 'advanced', 'elite']),
                risk_levels=random.choice(['low', 'moderate', 'high', 'extreme']),
                availability=random.choice(['full_time', 'part_time', 'evenings', 'weekends']),
                willing_to_relocate=random.choice([True, False])
            )
        
        elif talent_type == 'actor':
            ExpressiveWorker.objects.create(
                profile=profile,
                performer_type='actor',
                years_experience=random.randint(1, 30),
                height=random.uniform(150.0, 190.0),
                weight=random.uniform(45.0, 90.0),
                hair_color=random.choice(['blonde', 'brown', 'black', 'red', 'gray', 'other']),
                hair_type=random.choice(['straight', 'wavy', 'curly', 'coily', 'bald', 'other']),
                skin_tone=random.choice(['fair', 'light', 'medium', 'olive', 'brown', 'dark']),
                eye_color=random.choice(['blue', 'green', 'brown', 'hazel', 'black', 'other']),
                eye_size=random.choice(['small', 'medium', 'large']),
                eye_pattern=random.choice(['normal', 'protruding', 'sunken', 'almond', 'round', 'other']),
                face_shape=random.choice(['oval', 'round', 'square', 'heart', 'diamond', 'long', 'other']),
                forehead_shape=random.choice(['broad', 'narrow', 'rounded', 'straight', 'other']),
                lip_shape=random.choice(['thin', 'full', 'heart', 'round', 'bow', 'other']),
                eyebrow_pattern=random.choice(['arched', 'straight', 'curved', 'thick', 'thin', 'other']),
                voice_type=random.choice(['normal', 'thin', 'rough', 'deep', 'soft', 'nasal', 'other']),
                body_type=random.choice(['athletic', 'slim', 'muscular', 'average', 'plus_size', 'other']),
                availability=random.choice(['full_time', 'part_time', 'evenings', 'weekends'])
            )

    def create_talent_media(self, profile, talent_type):
        """Create media files for talent profiles"""
        media_count = random.randint(5, 12)  # More media per user
        
        # Create different types of media based on talent type
        media_types = self.get_talent_media_types(talent_type)
        
        for i in range(media_count):
            media_info = random.choice(media_types)
            media_type = media_info['type']
            title_prefix = media_info['title']
            
            # Download appropriate image based on content type
            if media_info['category'] == 'performance':
                media_file = self.download_image(800, 600, f"{profile.id}_perf_{i}")
            elif media_info['category'] == 'equipment':
                media_file = self.download_image(600, 400, f"{profile.id}_equip_{i}")
            elif media_info['category'] == 'studio':
                media_file = self.download_image(900, 600, f"{profile.id}_studio_{i}")
            else:  # portfolio
                media_file = self.download_image(800, 800, f"{profile.id}_port_{i}")
            
            if media_file:
                TalentMedia.objects.create(
                    talent=profile,
                    name=f"{title_prefix} {i+1}",
                    media_info=media_info['description'],
                    media_type=media_type,
                    media_file=media_file,
                    is_test_video=False
                )

    def get_talent_media_types(self, talent_type):
        """Get media types specific to talent type"""
        if talent_type == 'musician':
            return [
                {'type': 'image', 'category': 'performance', 'title': 'Original Song', 'description': 'Original composition and performance'},
                {'type': 'video', 'category': 'performance', 'title': 'Live Performance', 'description': 'Live performance video'},
                {'type': 'image', 'category': 'equipment', 'title': 'Studio Setup', 'description': 'Professional recording equipment'},
                {'type': 'image', 'category': 'performance', 'title': 'Concert Photo', 'description': 'Performance on stage'},
                {'type': 'image', 'category': 'portfolio', 'title': 'Demo Track', 'description': 'Professional demo recording'},
                {'type': 'image', 'category': 'studio', 'title': 'Recording Session', 'description': 'Behind the scenes in studio'}
            ]
        elif talent_type == 'dancer':
            return [
                {'type': 'video', 'category': 'performance', 'title': 'Dance Routine', 'description': 'Choreographed dance performance'},
                {'type': 'image', 'category': 'performance', 'title': 'Stage Performance', 'description': 'Professional stage performance'},
                {'type': 'video', 'category': 'portfolio', 'title': 'Solo Piece', 'description': 'Individual dance showcase'},
                {'type': 'image', 'category': 'studio', 'title': 'Rehearsal Space', 'description': 'Dance studio practice session'},
                {'type': 'image', 'category': 'equipment', 'title': 'Dance Gear', 'description': 'Professional dance equipment and attire'}
            ]
        elif talent_type == 'singer':
            return [
                {'type': 'image', 'category': 'performance', 'title': 'Vocal Performance', 'description': 'Professional vocal recording'},
                {'type': 'video', 'category': 'performance', 'title': 'Music Video', 'description': 'Professional music video'},
                {'type': 'image', 'category': 'performance', 'title': 'Concert Shot', 'description': 'Live concert performance'},
                {'type': 'image', 'category': 'portfolio', 'title': 'Cover Song', 'description': 'Professional cover performance'},
                {'type': 'image', 'category': 'studio', 'title': 'Recording Studio', 'description': 'Professional recording session'}
            ]
        else:  # actor
            return [
                {'type': 'video', 'category': 'performance', 'title': 'Acting Reel', 'description': 'Professional acting demo reel'},
                {'type': 'image', 'category': 'performance', 'title': 'Theater Photo', 'description': 'Stage performance photograph'},
                {'type': 'video', 'category': 'portfolio', 'title': 'Monologue', 'description': 'Solo acting performance'},
                {'type': 'image', 'category': 'equipment', 'title': 'Costume Collection', 'description': 'Professional wardrobe and props'},
                {'type': 'image', 'category': 'studio', 'title': 'On Set', 'description': 'Behind the scenes on film set'}
            ]

    def create_background_users(self, count):
        """Create background users with profiles"""
        background_types = ['model', 'extra', 'voice_actor', 'stunt_performer']
        users_per_type = count // len(background_types)
        
        for i, bg_type in enumerate(background_types):
            type_count = users_per_type + (1 if i < count % len(background_types) else 0)
            
            for j in range(type_count):
                user = self.create_base_user('background')
                self.create_background_profile(user, bg_type)
                
                if j % 10 == 0:
                    self.stdout.write(f'Created {j + 1} {bg_type} users...')

    def create_background_profile(self, user, bg_type):
        """Create background profile based on type"""
        # Download profile picture
        profile_image = self.download_image(200, 200, user.id)
        
        # Get specialization based on type
        if bg_type == 'model':
            specialization = random.choice(self.model_types)
        elif bg_type == 'extra':
            specialization = random.choice(self.extra_types)
        elif bg_type == 'voice_actor':
            specialization = random.choice(self.voice_types)
        else:  # stunt_performer
            specialization = random.choice(self.stunt_types)
        
        profile = BackGroundJobsProfile.objects.create(
            user=user,
            country=self.fake.country()[:25],  # Limit to 25 characters
            date_of_birth=self.fake.date_of_birth(minimum_age=18, maximum_age=65),
            gender=random.choice(['Male', 'Female', 'Other']),
            account_type=random.choice(['back_ground_jobs', 'free'])
        )
        
        if profile_image:
            profile.profile_picture.save(f'bg_profile_{user.id}.jpg', profile_image)
        
        # Create some portfolio images
        self.create_background_media(profile, bg_type)

    def create_background_media(self, profile, bg_type):
        """Create portfolio items for background profiles"""
        media_count = random.randint(6, 15)  # More items per background user
        
        # Get item types specific to background type
        item_types = self.get_background_item_types(bg_type)
        
        for i in range(media_count):
            item_info = random.choice(item_types)
            
            # Download appropriate image based on item type
            if item_info['category'] == 'headshot':
                portfolio_image = self.download_image(400, 600, f"{profile.id}_headshot_{i}")
            elif item_info['category'] == 'portfolio':
                portfolio_image = self.download_image(800, 600, f"{profile.id}_portfolio_{i}")
            elif item_info['category'] == 'equipment':
                portfolio_image = self.download_image(600, 400, f"{profile.id}_equipment_{i}")
            elif item_info['category'] == 'workspace':
                portfolio_image = self.download_image(900, 600, f"{profile.id}_workspace_{i}")
            else:  # comp_card
                portfolio_image = self.download_image(600, 900, f"{profile.id}_comp_{i}")
            
            if portfolio_image:
                # Note: Adjust this based on your actual background media model
                # For now, we'll create a simple representation
                self.create_background_portfolio_item(profile, item_info, portfolio_image, i)

    def get_background_item_types(self, bg_type):
        """Get portfolio item types specific to background type"""
        if bg_type == 'model':
            return [
                {'category': 'headshot', 'title': 'Professional Headshot', 'description': 'High-quality professional headshot'},
                {'category': 'portfolio', 'title': 'Fashion Shot', 'description': 'Fashion photography portfolio piece'},
                {'category': 'portfolio', 'title': 'Commercial Photo', 'description': 'Commercial modeling photograph'},
                {'category': 'comp_card', 'title': 'Comp Card', 'description': 'Professional modeling comp card'},
                {'category': 'equipment', 'title': 'Photography Gear', 'description': 'Professional photography equipment'},
                {'category': 'workspace', 'title': 'Photo Studio', 'description': 'Professional photography studio setup'}
            ]
        elif bg_type == 'extra':
            return [
                {'category': 'headshot', 'title': 'Casting Headshot', 'description': 'Professional casting headshot'},
                {'category': 'portfolio', 'title': 'Set Photo', 'description': 'Behind the scenes on film set'},
                {'category': 'portfolio', 'title': 'Wardrobe Test', 'description': 'Costume and wardrobe fitting'},
                {'category': 'equipment', 'title': 'Wardrobe Collection', 'description': 'Professional wardrobe pieces'},
                {'category': 'workspace', 'title': 'Film Set', 'description': 'Professional film set environment'}
            ]
        elif bg_type == 'voice_actor':
            return [
                {'category': 'headshot', 'title': 'Voice Actor Headshot', 'description': 'Professional voice actor headshot'},
                {'category': 'equipment', 'title': 'Home Studio', 'description': 'Professional home recording studio'},
                {'category': 'equipment', 'title': 'Microphone Setup', 'description': 'Professional microphone and audio equipment'},
                {'category': 'workspace', 'title': 'Recording Booth', 'description': 'Professional recording booth setup'},
                {'category': 'portfolio', 'title': 'Script Collection', 'description': 'Voice acting scripts and materials'}
            ]
        else:  # stunt_performer
            return [
                {'category': 'headshot', 'title': 'Stunt Headshot', 'description': 'Professional stunt performer headshot'},
                {'category': 'portfolio', 'title': 'Action Shot', 'description': 'Professional stunt performance photo'},
                {'category': 'equipment', 'title': 'Safety Gear', 'description': 'Professional stunt safety equipment'},
                {'category': 'equipment', 'title': 'Stunt Props', 'description': 'Professional stunt performance props'},
                {'category': 'workspace', 'title': 'Training Facility', 'description': 'Professional stunt training facility'},
                {'category': 'portfolio', 'title': 'Wire Work', 'description': 'Professional wire work performance'}
            ]

    def create_background_portfolio_item(self, profile, item_info, image_file, index):
        """Create a portfolio item for background user (placeholder implementation)"""
        # This is a placeholder - you might want to create actual media records
        # or portfolio items based on your background user media model
        # For now, we'll just save the image to the profile if possible
        try:
            # If your BackGroundJobsProfile has a media field or related model, use it here
            # Example: BackgroundMedia.objects.create(profile=profile, ...)
            pass
        except Exception as e:
            # Silently handle if media model doesn't exist yet
            pass
