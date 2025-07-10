"""Utility functions for generating HTML pages for coffee shops."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Cache for city extraction to avoid repeated API calls
_city_cache = {}


def save_shop_images(shop_data: Dict[str, Any], city_dir: Path) -> List[str]:
    """Save shop images as separate files and return their relative paths.
    
    Args:
        shop_data: Dictionary containing enriched coffee shop data
        city_dir: Path to the city directory where images should be saved
        
    Returns:
        List of relative paths to saved image files
    """
    photos = shop_data.get('photos', [])[:10]  # Limit to 10 photos
    if not photos:
        return []
    
    # Create images subdirectory within the city folder
    images_dir = city_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    name = shop_data.get('name', 'Unknown Coffee Shop')
    # Create a safe base name for images
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    
    saved_images = []
    
    for i, photo in enumerate(photos):
        if 'photo_bytes' in photo:
            try:
                # Create filename
                filename = f"{safe_name}_{i+1}.jpg"
                file_path = images_dir / filename
                
                # Save image bytes to file
                with open(file_path, 'wb') as f:
                    f.write(photo['photo_bytes'])
                
                # Store relative path from city directory
                relative_path = f"images/{filename}"
                saved_images.append(relative_path)
                
                logger.info(f"Saved image: {file_path}")
                
            except Exception as e:
                logger.error(f"Error saving image {i+1} for {name}: {e}")
                continue
    
    return saved_images


def generate_html_for_shop(shop_data: Dict[str, Any], image_paths: List[str] = None) -> str:
    """Generate HTML content for a single coffee shop.
    
    Args:
        shop_data: Dictionary containing enriched coffee shop data
        image_paths: List of relative paths to saved image files
        
    Returns:
        HTML string with shop information
    """
    name = shop_data.get('name', 'Unknown Coffee Shop')
    address = shop_data.get('formatted_address', 'Address not available')
    rating = shop_data.get('rating', 'N/A')
    rating_count = shop_data.get('user_ratings_total', 0)
    phone = shop_data.get('formatted_phone_number', '')
    website = shop_data.get('website', '')
    
    # Get reviews
    generated_reviews = shop_data.get('generated_reviews', {})
    english_review = generated_reviews.get('en', '')
    chinese_review = generated_reviews.get('zh', '')
    
    # Generate photo HTML using saved image files
    photo_html = ""
    if image_paths:
        photo_html = '<div class="photos-section">\n'
        photo_html += '<h3>📸 Photos</h3>\n'
        photo_html += '<div class="photo-grid">\n'
        
        for i, image_path in enumerate(image_paths):
            photo_html += f'<img src="{image_path}" alt="Photo {i+1}" class="photo">\n'
        
        photo_html += '</div>\n'
        photo_html += '</div>\n'
    
    # Generate opening hours
    opening_hours = shop_data.get('opening_hours', {})
    hours_html = ""
    if opening_hours and 'weekday_text' in opening_hours:
        hours_html = '<div class="hours-section">\n'
        hours_html += '<h3>⏰ Opening Hours</h3>\n'
        hours_html += '<ul>\n'
        for day in opening_hours['weekday_text']:
            hours_html += f'<li>{day}</li>\n'
        hours_html += '</ul>\n'
        hours_html += '</div>\n'
    
    # Generate contact info
    contact_html = ""
    if phone or website:
        contact_html = '<div class="contact-section">\n'
        contact_html += '<h3>📞 Contact Information</h3>\n'
        if phone:
            contact_html += f'<p><strong>Phone:</strong> {phone}</p>\n'
        if website:
            contact_html += f'<p><strong>Website:</strong> <a href="{website}" target="_blank">{website}</a></p>\n'
        contact_html += '</div>\n'
    
    # Generate reviews section
    reviews_html = ""
    if english_review or chinese_review:
        reviews_html = '<div class="reviews-section">\n'
        reviews_html += '<h3>📝 Work & Study Review</h3>\n'
        
        if english_review:
            reviews_html += '<div class="review-block">\n'
            reviews_html += '<h4>🇺🇸 English Review</h4>\n'
            reviews_html += f'<p>{english_review}</p>\n'
            reviews_html += '</div>\n'
        
        if chinese_review:
            reviews_html += '<div class="review-block">\n'
            reviews_html += '<h4>🇨🇳 中文评论</h4>\n'
            reviews_html += f'<p>{chinese_review}</p>\n'
            reviews_html += '</div>\n'
        
        reviews_html += '</div>\n'
    
    # Create the complete HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
            background-color: #f9f9f9;
        }}
        
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        h3 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        h4 {{
            color: #7f8c8d;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        .rating {{
            font-size: 1.2em;
            color: #f39c12;
            margin: 10px 0;
        }}
        
        .address {{
            font-size: 1.1em;
            color: #555;
            margin: 15px 0;
            padding: 10px;
            background: #ecf0f1;
            border-radius: 5px;
        }}
        
        .photo-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .photo {{
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
        
        .photo-placeholder {{
            width: 100%;
            height: 200px;
            background: #bdc3c7;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #7f8c8d;
            font-style: italic;
        }}
        
        .review-block {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #3498db;
        }}
        
        .review-block p {{
            margin: 0;
            text-align: justify;
        }}
        
        .hours-section ul {{
            list-style: none;
            padding: 0;
        }}
        
        .hours-section li {{
            background: #ecf0f1;
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 4px;
        }}
        
        .contact-section p {{
            margin: 10px 0;
        }}
        
        .contact-section a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        .contact-section a:hover {{
            text-decoration: underline;
        }}
        
        /* Copy-friendly styles */
        @media print {{
            body {{
                background: white;
                color: black;
            }}
            
            .container {{
                box-shadow: none;
                border: 1px solid #ccc;
            }}
        }}
        
        /* Make text easily selectable */
        * {{
            -webkit-user-select: text;
            -moz-user-select: text;
            -ms-user-select: text;
            user-select: text;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>☕ {name}</h1>
        
        <div class="rating">
            ⭐ {rating}/5 ({rating_count} reviews)
        </div>
        
        <div class="address">
            📍 {address}
        </div>
        
        {contact_html}
        
        {hours_html}
        
        {reviews_html}
        
        {photo_html}
    </div>
</body>
</html>"""
    
    return html_content


def extract_city_from_address(address: str) -> str:
    """Extract city name from a formatted address using Claude.
    
    Args:
        address: Formatted address string
        
    Returns:
        City name or 'Unknown_City' if not found
    """
    if not address:
        return 'Unknown_City'
    
    # Check cache first
    if address in _city_cache:
        return _city_cache[address]
    
    try:
        # Get Anthropic API key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not found, falling back to simple parsing")
            city = _fallback_city_extraction(address)
            _city_cache[address] = city
            return city
        
        # Initialize Claude client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Create prompt for city extraction
        prompt = f"""Extract the city name from this address: "{address}"

Return ONLY the city name, nothing else. If you cannot determine the city, return "Unknown_City".
Make the city name suitable for use as a folder name (replace spaces with underscores, remove special characters).

Examples:
- "123 Main St, New York, NY 10001, USA" -> "New_York"
- "456 Oak Ave, Los Angeles, CA, United States" -> "Los_Angeles"
- "789 Pine Rd, London, UK" -> "London"
- "321 Elm St, San Francisco, California" -> "San_Francisco"

Address: {address}
City name:"""

        # Call Claude API
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=50,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract city name from response
        city_name = response.content[0].text.strip()
        
                 # Validate the response
        if city_name and city_name != "Unknown_City" and len(city_name) > 1:
            # Clean up the city name
            clean_city = "".join(c for c in city_name if c.isalnum() or c in ('_', '-')).strip()
            if clean_city:
                logger.info(f"Extracted city '{clean_city}' from address: {address}")
                # Cache the result
                _city_cache[address] = clean_city
                return clean_city
        
        logger.warning(f"Could not extract city from address: {address}")
        # Cache the negative result too
        _city_cache[address] = 'Unknown_City'
        return 'Unknown_City'
        
    except Exception as e:
        logger.warning(f"Error extracting city from address '{address}': {e}")
        # Use fallback and cache the result
        city = _fallback_city_extraction(address)
        _city_cache[address] = city
        return city


def _fallback_city_extraction(address: str) -> str:
    """Fallback method for extracting city from address without Claude.
    
    Args:
        address: Formatted address string
        
    Returns:
        City name or 'Unknown_City' if not found
    """
    try:
        # Split by comma and look for the city (usually second-to-last or third-to-last part)
        parts = [part.strip() for part in address.split(',')]
        
        if len(parts) >= 2:
            # Try to find the city - typically comes before state/country
            # Look for patterns like "City, State" or "City, Country"
            for i in range(len(parts) - 1):
                part = parts[i]
                # Skip postal codes and numbers
                if not part.isdigit() and not any(char.isdigit() for char in part[:3]):
                    # Clean up the city name
                    city = "".join(c for c in part if c.isalnum() or c in (' ', '-', '_')).strip()
                    if city and len(city) > 2:  # Valid city name
                        return city.replace(' ', '_')
        
        # Fallback: use the first non-numeric part
        for part in parts:
            clean_part = "".join(c for c in part if c.isalnum() or c in (' ', '-', '_')).strip()
            if clean_part and not clean_part.isdigit() and len(clean_part) > 2:
                return clean_part.replace(' ', '_')
    
    except Exception as e:
        logger.warning(f"Error in fallback city extraction from address '{address}': {e}")
    
    return 'Unknown_City'


def generate_html_files(coffee_shops: List[Dict[str, Any]], output_dir: str) -> Dict[str, List[str]]:
    """Generate HTML files for a list of coffee shops, organized by city.
    
    Args:
        coffee_shops: List of enriched coffee shop data
        output_dir: Directory to save HTML files
        
    Returns:
        Dictionary mapping city names to lists of generated HTML file paths
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generated_files_by_city = {}
    
    for shop in coffee_shops:
        try:
            name = shop.get('name', 'Unknown Coffee Shop')
            address = shop.get('formatted_address', '')
            
            # Extract city from address
            city = extract_city_from_address(address)
            
            # Create city directory
            city_dir = output_path / city
            city_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a safe filename
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            filename = f"{safe_name}.html"
            
            # Save images as separate files and get their paths
            image_paths = save_shop_images(shop, city_dir)
            
            # Generate HTML content with image file references
            html_content = generate_html_for_shop(shop, image_paths)
            
            # Save to file in city directory
            file_path = city_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Track files by city
            if city not in generated_files_by_city:
                generated_files_by_city[city] = []
            generated_files_by_city[city].append(str(file_path))
            
            logger.info(f"Generated HTML file: {file_path} (with {len(image_paths)} images)")
            
        except Exception as e:
            logger.error(f"Error generating HTML for {shop.get('name', 'Unknown')}: {e}")
            continue
    
    total_files = sum(len(files) for files in generated_files_by_city.values())
    logger.info(f"Generated {total_files} HTML files with images in {len(generated_files_by_city)} cities in {output_dir}")
    return generated_files_by_city


def generate_index_html(coffee_shops: List[Dict[str, Any]], output_dir: str, html_files_by_city: Dict[str, List[str]]) -> str:
    """Generate an index HTML file with links to all coffee shop pages, organized by city.
    
    Args:
        coffee_shops: List of enriched coffee shop data
        output_dir: Directory where HTML files are saved
        html_files_by_city: Dictionary mapping city names to lists of HTML file paths
        
    Returns:
        Path to the generated index HTML file
    """
    output_path = Path(output_dir)
    index_path = output_path / "index.html"
    
    # Create a mapping from file paths to shop data
    file_to_shop = {}
    for shop in coffee_shops:
        address = shop.get('formatted_address', '')
        city = extract_city_from_address(address)
        name = shop.get('name', 'Unknown Coffee Shop')
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}.html"
        
        # Create the expected file path
        expected_path = str(output_path / city / filename)
        file_to_shop[expected_path] = shop
    
    # Create links organized by city
    cities_html = ""
    for city, file_paths in sorted(html_files_by_city.items()):
        city_display = city.replace('_', ' ')
        cities_html += f"""
        <div class="city-section" id="{city}">
            <h2>📍 {city_display} ({len(file_paths)} coffee shops)</h2>
            <div class="shop-grid">
        """
        
        for file_path in sorted(file_paths):
            shop = file_to_shop.get(file_path)
            if shop:
                name = shop.get('name', 'Unknown Coffee Shop')
                address = shop.get('formatted_address', 'Address not available')
                rating = shop.get('rating', 'N/A')
                
                # Create relative path from index to the shop HTML file
                rel_path = Path(file_path).relative_to(output_path)
                
                cities_html += f"""
                <div class="shop-card">
                    <h3><a href="{rel_path}">{name}</a></h3>
                    <p class="address">📍 {address}</p>
                    <p class="rating">⭐ {rating}/5</p>
                </div>
                """
        
        cities_html += """
            </div>
        </div>
        """
    
    total_shops = len(coffee_shops)
    total_cities = len(html_files_by_city)
    
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coffee Shops Directory</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
            background-color: #f9f9f9;
        }}
        
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #bdc3c7;
            padding-bottom: 10px;
            margin-top: 40px;
            margin-bottom: 20px;
        }}
        
        .city-section {{
            margin-bottom: 40px;
        }}
        
        .shop-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .shop-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            transition: transform 0.2s;
        }}
        
        .shop-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .shop-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        
        .shop-card a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        .shop-card a:hover {{
            text-decoration: underline;
        }}
        
        .address {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin: 5px 0;
        }}
        
        .rating {{
            color: #f39c12;
            font-weight: bold;
            margin: 5px 0;
        }}
        
        .summary {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: #e8f4f8;
            border-radius: 8px;
        }}
        
        .cities-nav {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        
        .cities-nav h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        
        .cities-nav a {{
            color: #3498db;
            text-decoration: none;
            margin-right: 15px;
            padding: 5px 10px;
            border-radius: 4px;
            background: white;
            display: inline-block;
            margin-bottom: 5px;
        }}
        
        .cities-nav a:hover {{
            background: #3498db;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>☕ Coffee Shops Directory</h1>
        
        <div class="summary">
            <p>📊 <strong>{total_shops} coffee shops</strong> across <strong>{total_cities} cities</strong> with detailed information, reviews, and photos</p>
            <p>Click on any coffee shop name to view its detailed page</p>
        </div>
        
        <div class="cities-nav">
            <h3>🗺️ Quick Navigation by City:</h3>
            {' '.join([f'<a href="#{city}">{city.replace("_", " ")}</a>' for city in sorted(html_files_by_city.keys())])}
        </div>
        
        {cities_html}
    </div>
</body>
</html>"""
    
    # Save index file
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    logger.info(f"Generated index HTML file: {index_path}")
    return str(index_path) 