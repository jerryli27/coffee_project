"""Utility functions to process coffee shop lists and get Google Maps metadata."""

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import geopandas as gpd
import googlemaps
import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoffeeShopProcessor:
    """A client for processing coffee shop lists and enriching them with Google Maps data."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Google Maps client.
        
        Args:
            api_key: Google Maps API key. If not provided, will try to load from
                    environment variable GOOGLE_MAPS_API_KEY.
        """
        if api_key is None:
            api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        
        if not api_key:
            raise ValueError(
                "Google Maps API key not found. Please set GOOGLE_MAPS_API_KEY "
                "environment variable or pass api_key parameter."
            )
        
        self.client = googlemaps.Client(key=api_key)
    
    def parse_coffee_shop_csv(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """Parse a CSV file containing coffee shop information.
        
        Args:
            csv_file_path: Path to the CSV file
            
        Returns:
            List of dictionaries with parsed coffee shop data
        """
        try:
            df = pd.read_csv(csv_file_path)
            logger.info(f"Loaded {len(df)} entries from {csv_file_path}")
            
            coffee_shops = []
            for idx, row in df.iterrows():
                # Skip empty rows
                if pd.isna(row.get('Title')) and pd.isna(row.get('URL')):
                    continue
                
                shop_data = {
                    'original_title': row.get('Title', ''),
                    'note': row.get('Note', ''),
                    'url': row.get('URL', ''),
                    'tags': row.get('Tags', ''),
                    'comment': row.get('Comment', ''),
                }
                
                # Extract place ID from URL
                place_id = self._extract_place_id_from_url(row.get('URL', ''))
                if place_id:
                    shop_data['place_id'] = place_id
                    coffee_shops.append(shop_data)
                else:
                    logger.warning(f"Could not extract place ID from URL: {row.get('URL', '')}")
            
            logger.info(f"Successfully parsed {len(coffee_shops)} coffee shops with valid place IDs")
            return coffee_shops
            
        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            return []
    
    def _extract_place_id_from_url(self, url: str) -> Optional[str]:
        """Extract place ID from a Google Maps URL by searching for the place name.
        
        Args:
            url: Google Maps URL
            
        Returns:
            Place ID if found, None otherwise
        """
        if not url:
            return None
        
        try:
            # Extract place name from the URL and search for it
            place_name = self._extract_place_name_from_url(url)
            if place_name:
                return self._find_place_id_by_name(place_name)
            
            logger.warning(f"Could not extract place name from URL: {url}")
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting place ID from URL {url}: {e}")
            return None
    
    def _extract_place_name_from_url(self, url: str) -> Optional[str]:
        """Extract place name from Google Maps URL.
        
        Args:
            url: Google Maps URL
            
        Returns:
            Place name if found, None otherwise
        """
        try:
            # Look for place name in the URL path
            match = re.search(r'/place/([^/]+)', url)
            if match:
                # URL decode and clean up the place name
                place_name = match.group(1).replace('+', ' ').replace('%20', ' ')
                # Remove any trailing parameters
                place_name = place_name.split('?')[0]
                return place_name
            return None
        except Exception as e:
            logger.warning(f"Error extracting place name from URL {url}: {e}")
            return None
    
    def _find_place_id_by_name(self, place_name: str) -> Optional[str]:
        """Find place ID by searching for the place name.
        
        Args:
            place_name: Name of the place to search for
            
        Returns:
            Place ID if found, None otherwise
        """
        try:
            # Use the find_place API to get place ID
            find_result = self.client.find_place(
                input=place_name,
                input_type='textquery',
                fields=['place_id']
            )
            
            if find_result.get('candidates'):
                place_id = find_result['candidates'][0]['place_id']
                logger.info(f"Found place ID {place_id} for '{place_name}'")
                return place_id
            
            return None
            
        except Exception as e:
            logger.warning(f"Error finding place ID for '{place_name}': {e}")
            return None
    
    def get_photo_bytes(self, photo_reference: str, max_width: int = 400, max_height: int = 400) -> Optional[bytes]:
        """Download photo bytes from Google Maps API.
        
        Args:
            photo_reference: Photo reference string from place details
            max_width: Maximum width of the photo (default 400)
            max_height: Maximum height of the photo (default 400)
            
        Returns:
            Photo bytes if successful, None otherwise
        """
        try:
            # Construct the photo API URL
            url = "https://maps.googleapis.com/maps/api/place/photo"
            params = {
                'photo_reference': photo_reference,
                'maxwidth': max_width,
                'maxheight': max_height,
                'key': self.client.key
            }
            
            # Make request to get photo
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Successfully downloaded photo ({len(response.content)} bytes)")
                return response.content
            else:
                logger.warning(f"Failed to download photo: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading photo: {e}")
            return None
    
    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a place.
        
        Args:
            place_id: Google Places ID
            
        Returns:
            Dictionary with detailed place information
        """
        try:
            # Request comprehensive place details
            fields = [
                'place_id', 'name', 'formatted_address', 'geometry',
                'rating', 'user_ratings_total', 'price_level',
                'opening_hours', 'formatted_phone_number', 'website',
                'photo', 'reviews', 'type', 'business_status',
                'url', 'utc_offset', 'vicinity'
            ]
            
            result = self.client.place(
                place_id=place_id,
                fields=fields
            )
            
            return result.get('result', {})
            
        except Exception as e:
            logger.error(f"Error getting place details for {place_id}: {e}")
            return None
    
    def enrich_coffee_shops(self, coffee_shops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich coffee shop data with detailed Google Maps information.
        
        Args:
            coffee_shops: List of coffee shop data with place IDs
            
        Returns:
            List of enriched coffee shop data
        """
        enriched_shops = []
        
        for shop in coffee_shops:
            place_id = shop.get('place_id')
            if not place_id:
                logger.warning(f"No place ID found for shop: {shop.get('original_title', 'Unknown')}")
                continue
                
            logger.info(f"Enriching data for: {shop.get('original_title', 'Unknown')}")
            
            # Get detailed information from Google Maps
            details = self.get_place_details(place_id)
            if details:
                # Merge original data with detailed information
                enriched_shop = {**shop, **details}
                
                # Download photos if available
                if 'photos' in details and details['photos']:
                    photo_bytes_list = []
                    for photo in details['photos']:
                        photo_bytes = self.get_photo_bytes(
                            photo['photo_reference'], max_height=photo['height'], max_width=photo['width']
                        )
                        if photo_bytes:
                            photo_bytes_list.append({**photo, 'photo_bytes': photo_bytes})
                        else:
                            logger.warning(f"Could not download photo for reference: {photo['photo_reference']}")
                    enriched_shop['photos'] = photo_bytes_list
                
                enriched_shops.append(enriched_shop)
                
                # Add delay to respect API rate limits
                time.sleep(0.1)
            else:
                logger.warning(f"Could not get details for place ID: {place_id}")
        
        logger.info(f"Successfully enriched {len(enriched_shops)} coffee shops")
        return enriched_shops


def create_coffee_shop_dataframe(coffee_shops: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert coffee shop data to a structured DataFrame.
    
    Args:
        coffee_shops: List of coffee shop dictionaries
        
    Returns:
        DataFrame with structured coffee shop data
    """
    if not coffee_shops:
        return pd.DataFrame()
    
    # Extract key information
    processed_data = []
    
    for shop in coffee_shops:
        try:
            # Basic information
            data = {
                'place_id': shop.get('place_id'),
                'name': shop.get('name'),
                'original_title': shop.get('original_title', ''),
                'formatted_address': shop.get('formatted_address'),
                'vicinity': shop.get('vicinity'),
                'rating': shop.get('rating'),
                'user_ratings_total': shop.get('user_ratings_total'),
                'price_level': shop.get('price_level'),
                'phone': shop.get('formatted_phone_number'),
                'website': shop.get('website'),
                'business_status': shop.get('business_status'),
                'google_url': shop.get('url'),
                'original_url': shop.get('url', ''),  # Original URL from CSV
                'note': shop.get('note', ''),
                'tags': shop.get('tags', ''),
                'comment': shop.get('comment', ''),
                'types': ', '.join(shop.get('type', [])),
            }
            
            # Location data
            if 'geometry' in shop:
                location = shop['geometry']['location']
                data['latitude'] = location.get('lat')
                data['longitude'] = location.get('lng')
            
            # Opening hours
            if 'opening_hours' in shop:
                opening_hours = shop['opening_hours']
                data['open_now'] = opening_hours.get('open_now')
                data['hours'] = '\n'.join(opening_hours.get('weekday_text', []))
            
            # Photo
            if 'photo' in shop:
                data['photo_count'] = len(shop['photo'])
                data['photo_reference'] = shop['photo'][0].get('photo_reference') if shop['photo'] else None
            
            # Reviews summary
            if 'reviews' in shop:
                reviews = shop['reviews']
                data['review_count'] = len(reviews)
                data['recent_review'] = reviews[0].get('text', '')[:200] + '...' if reviews else ''
            
            # Generated reviews
            if 'generated_reviews' in shop:
                generated_reviews = shop['generated_reviews']
                data['generated_review_en'] = generated_reviews.get('en', '')
                data['generated_review_zh'] = generated_reviews.get('zh', '')
            
            processed_data.append(data)
            
        except Exception as e:
            logger.warning(f"Error processing shop data: {e}")
            continue
    
    df = pd.DataFrame(processed_data)
    logger.info(f"Created DataFrame with {len(df)} coffee shops")
    
    return df


def export_to_geojson(df: pd.DataFrame, output_file: str) -> None:
    """Export coffee shop data to GeoJSON format.
    
    Args:
        df: DataFrame with coffee shop data (must have latitude/longitude)
        output_file: Path to output GeoJSON file
    """
    try:
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df.longitude, df.latitude),
            crs="EPSG:4326"
        )
        
        # Export to GeoJSON
        gdf.to_file(output_file, driver='GeoJSON')
        logger.info(f"Exported {len(gdf)} places to {output_file}")
        
    except Exception as e:
        logger.error(f"Error exporting to GeoJSON: {e}")


def process_coffee_shop_list(csv_file_path: str, 
                           output_csv: Optional[str] = None,
                           output_geojson: Optional[str] = None,
                           generate_reviews: bool = False,
                           generate_html: bool = False,
                           output_path: Optional[str] = None) -> pd.DataFrame:
    """Process a coffee shop list and enrich it with Google Maps data.
    
    Args:
        csv_file_path: Path to the CSV file with coffee shop list
        output_csv: Optional path to save enriched data as CSV
        output_geojson: Optional path to save enriched data as GeoJSON
        generate_reviews: Whether to generate AI-powered reviews
        generate_html: Whether to generate HTML files for each coffee shop
        output_path: Optional directory path for HTML files
        
    Returns:
        DataFrame with enriched coffee shop data
    """
    # Initialize processor
    processor = CoffeeShopProcessor()
    
    # Parse the CSV file
    coffee_shops = processor.parse_coffee_shop_csv(csv_file_path)
    
    if not coffee_shops:
        logger.error("No coffee shops found in the CSV file")
        return pd.DataFrame()
    
    # Enrich with Google Maps data
    enriched_shops = processor.enrich_coffee_shops(coffee_shops)
    
    # Generate reviews if requested
    if generate_reviews:
        try:
            from anthropic_utils import ReviewGenerator
            review_generator = ReviewGenerator()
            enriched_shops = review_generator.generate_reviews_for_list(enriched_shops)
            logger.info("Generated AI-powered reviews for all coffee shops")
        except ImportError:
            logger.warning("Could not import ReviewGenerator - skipping review generation")
        except Exception as e:
            logger.error(f"Error generating reviews: {e}")
    
    # Generate HTML files if requested
    if generate_html and output_path:
        try:
            from html_utils import generate_html_files, generate_index_html
            html_files_by_city = generate_html_files(enriched_shops, output_path)
            if html_files_by_city:
                generate_index_html(enriched_shops, output_path, html_files_by_city)
                total_files = sum(len(files) for files in html_files_by_city.values())
                logger.info(f"Generated {total_files} HTML files in {len(html_files_by_city)} cities in {output_path}")
        except ImportError:
            logger.warning("Could not import HTML utils - skipping HTML generation")
        except Exception as e:
            logger.error(f"Error generating HTML files: {e}")
    
    # Create DataFrame
    df = create_coffee_shop_dataframe(enriched_shops)
    
    # Save outputs
    if output_csv:
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved enriched data to {output_csv}")
    
    if output_geojson and 'latitude' in df.columns and 'longitude' in df.columns:
        export_to_geojson(df, output_geojson)
        logger.info(f"Saved GeoJSON to {output_geojson}")
    
    return df