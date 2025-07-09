#!/usr/bin/env python
"""
Check all media types and fields in the profiles app
"""

import os
import sys
import django
from pathlib import Path

# Add the talent_platform directory to Python path
project_dir = Path(__file__).resolve().parent / 'talent_platform'
sys.path.insert(0, str(project_dir))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
django.setup()

from django.conf import settings
from talent_platform.profiles.models import (
    TalentMedia, TalentUserProfile, Band, BandMedia, 
    VisualWorker, ExpressiveWorker, HybridWorker,
    Prop, Costume, Location, Memorabilia, Vehicle, 
    ArtisticMaterial, MusicItem, RareItem, BackGroundJobsProfile
)

def check_all_media_fields():
    """Check all media fields in the profiles app"""
    print("=== ALL MEDIA FIELDS IN PROFILES APP ===\n")
    
    # 1. TalentUserProfile media fields
    print("1. TalentUserProfile Media Fields:")
    print("   - profile_picture (ImageField)")
    print()
    
    # 2. TalentMedia model
    print("2. TalentMedia Model:")
    print("   - media_file (FileField) - supports image/video")
    print("   - thumbnail (ImageField) - for video thumbnails")
    print("   - media_type choices: image, video")
    print()
    
    # 3. Band media fields
    print("3. Band Model:")
    print("   - profile_picture (ImageField)")
    print()
    
    # 4. BandMedia model
    print("4. BandMedia Model:")
    print("   - media_file (FileField) - supports image/video")
    print("   - media_type choices: image, video")
    print()
    
    # 5. Worker profile pictures
    print("5. Worker Profile Pictures:")
    print("   - VisualWorker: face_picture, mid_range_picture, full_body_picture")
    print("   - ExpressiveWorker: face_picture, mid_range_picture, full_body_picture")
    print("   - HybridWorker: face_picture, mid_range_picture, full_body_picture")
    print()
    
    # 6. Background Jobs Item models with images
    print("6. Background Jobs Item Models with Images:")
    print("   - Prop: image (props for movies/shows)")
    print("   - Costume: image (costumes/clothing)")
    print("   - Location: image (venues/spaces)")
    print("   - Memorabilia: image, authenticity_certificate (FileField)")
    print("   - Vehicle: image (cars, trucks, etc.)")
    print("   - ArtisticMaterial: image (art supplies, materials)")
    print("   - MusicItem: image (instruments, equipment)")
    print("   - RareItem: image (collectibles, antiques)")
    print()

def check_media_counts():
    """Check counts of media in database"""
    print("=== MEDIA COUNTS IN DATABASE ===\n")
    
    # TalentMedia counts
    total_media = TalentMedia.objects.count()
    images = TalentMedia.objects.filter(media_type='image').count()
    videos = TalentMedia.objects.filter(media_type='video').count()
    
    print(f"TalentMedia:")
    print(f"  Total: {total_media}")
    print(f"  Images: {images}")
    print(f"  Videos: {videos}")
    print()
    
    # BandMedia counts
    band_media = BandMedia.objects.count()
    band_images = BandMedia.objects.filter(media_type='image').count()
    band_videos = BandMedia.objects.filter(media_type='video').count()
    
    print(f"BandMedia:")
    print(f"  Total: {band_media}")
    print(f"  Images: {band_images}")
    print(f"  Videos: {band_videos}")
    print()
    
    # Profile pictures
    profiles_with_pics = TalentUserProfile.objects.filter(profile_picture__isnull=False).count()
    bands_with_pics = Band.objects.filter(profile_picture__isnull=False).count()
    
    print(f"Profile Pictures:")
    print(f"  TalentUserProfile: {profiles_with_pics}")
    print(f"  Band: {bands_with_pics}")
    print()
    
    # Worker profile pictures
    visual_workers = VisualWorker.objects.count()
    expressive_workers = ExpressiveWorker.objects.count()
    hybrid_workers = HybridWorker.objects.count()
    
    print(f"Worker Profile Pictures:")
    print(f"  VisualWorker: {visual_workers}")
    print(f"  ExpressiveWorker: {expressive_workers}")
    print(f"  HybridWorker: {hybrid_workers}")
    print()
    
    # Background Jobs Items
    props = Prop.objects.count()
    costumes = Costume.objects.count()
    locations = Location.objects.count()
    memorabilia = Memorabilia.objects.count()
    vehicles = Vehicle.objects.count()
    artistic_materials = ArtisticMaterial.objects.count()
    music_items = MusicItem.objects.count()
    rare_items = RareItem.objects.count()
    
    print(f"Background Jobs Items:")
    print(f"  Props: {props}")
    print(f"  Costumes: {costumes}")
    print(f"  Locations: {locations}")
    print(f"  Memorabilia: {memorabilia}")
    print(f"  Vehicles: {vehicles}")
    print(f"  Artistic Materials: {artistic_materials}")
    print(f"  Music Items: {music_items}")
    print(f"  Rare Items: {rare_items}")
    print()

def check_upload_paths():
    """Check upload paths for different media types"""
    print("=== UPLOAD PATHS ===\n")
    
    upload_paths = {
        'profile_pictures': 'profile_pictures/',
        'profile_pictures_face': 'profile_pictures/face/',
        'profile_pictures_mid': 'profile_pictures/mid/',
        'profile_pictures_full': 'profile_pictures/full/',
        'band_profile_pictures': 'band_profile_pictures/',
        'user_media': 'talent_media/user_{user_id}/',
        'band_media': 'band_media/band_{band_id}/',
        'thumbnails': 'thumbnails/',
        'item_images': 'item_images/',
        'certificates': 'certificates/',
    }
    
    for name, path in upload_paths.items():
        print(f"{name}: {path}")
    print()

if __name__ == "__main__":
    check_all_media_fields()
    check_media_counts()
    check_upload_paths()
    print("=== CHECK COMPLETE ===") 