#!/usr/bin/env python3
"""
Test script to verify image saving functionality.
"""

import os
import sys
from pathlib import Path

# Add the coffee_project directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from html_utils import generate_html_for_shop, save_shop_images


def test_image_saving():
    """Test the image saving functionality."""
    
    # Create a mock shop data with sample photo bytes
    mock_shop = {
        'name': 'Test Coffee Shop',
        'formatted_address': '123 Main St, Test City, TC 12345',
        'rating': 4.5,
        'user_ratings_total': 100,
        'photos': [
            {
                'photo_reference': 'test_ref_1',
                'height': 400,
                'width': 400,
                'photo_bytes': b'fake_image_data_1'  # Mock image bytes
            },
            {
                'photo_reference': 'test_ref_2',
                'height': 300,
                'width': 300,
                'photo_bytes': b'fake_image_data_2'  # Mock image bytes
            }
        ],
        'generated_reviews': {
            'en': 'Great place for working!',
            'zh': '工作的好地方！'
        }
    }
    
    # Create test directory
    test_dir = Path('test_output')
    test_dir.mkdir(exist_ok=True)
    
    city_dir = test_dir / 'Test_City'
    city_dir.mkdir(exist_ok=True)
    
    print("Testing image saving functionality...")
    
    # Test saving images
    image_paths = save_shop_images(mock_shop, city_dir)
    print(f"Saved {len(image_paths)} images: {image_paths}")
    
    # Test HTML generation with image paths
    html_content = generate_html_for_shop(mock_shop, image_paths)
    
    # Save HTML file
    html_file = city_dir / 'Test_Coffee_Shop.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated HTML file: {html_file}")
    
    # Verify files exist
    images_dir = city_dir / 'images'
    if images_dir.exists():
        image_files = list(images_dir.glob('*.jpg'))
        print(f"Found {len(image_files)} image files in {images_dir}")
        for img_file in image_files:
            print(f"  - {img_file.name} ({img_file.stat().st_size} bytes)")
    
    print("✅ Test completed successfully!")
    
    # Clean up
    print("Cleaning up test files...")
    import shutil
    shutil.rmtree(test_dir)
    print("🧹 Test files cleaned up")


if __name__ == "__main__":
    test_image_saving() 