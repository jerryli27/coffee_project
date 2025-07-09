#!/usr/bin/env python3
"""
Example script demonstrating how to process a coffee shop list
and enrich it with Google Maps metadata.
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

# Add the coffee_project directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from google_maps_utils import (CoffeeShopProcessor,
                               create_coffee_shop_dataframe, export_to_geojson,
                               process_coffee_shop_list)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process a coffee shop list and enrich it with Google Maps metadata"
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="enriched_coffee_shops.csv",
        help="Output CSV file path for the enriched coffee shop data (default: enriched_coffee_shops.csv)"
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default="coffee_project/places_list/example_short_list.csv",
        help="Input CSV file path with coffee shop list (default: coffee_project/places_list/example_short_list.csv)"
    )
    parser.add_argument(
        "--geojson",
        action="store_true",
        help="Also export data as GeoJSON file"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output, only show essential information"
    )
    return parser.parse_args()


def main():
    """Main function demonstrating the coffee shop list processing workflow."""
    
    args = parse_arguments()
    
    # Initialize the processor
    # Make sure to set your GOOGLE_MAPS_API_KEY environment variable
    try:
        processor = CoffeeShopProcessor()
        if not args.quiet:
            print("✅ Coffee shop processor initialized successfully")
    except ValueError as e:
        print(f"❌ Error initializing processor: {e}")
        print("\nTo fix this:")
        print("1. Get a Google Maps API key from: https://developers.google.com/maps/gmp-get-started")
        print("2. Enable the Places API for your project")
        print("3. Set the API key as an environment variable:")
        print("   export GOOGLE_MAPS_API_KEY='your_api_key_here'")
        print("   or create a .env file with: GOOGLE_MAPS_API_KEY=your_api_key_here")
        return
    
    # Process the coffee shop list
    if not args.quiet:
        print("\n" + "="*50)
        print("Processing coffee shop list")
        print("="*50)
    
    # Check if the input file exists
    if not os.path.exists(args.input_file):
        print(f"❌ Input file not found: {args.input_file}")
        print("Please make sure the file exists or specify a different file with --input_file")
        return
    
    print(f"🔍 Processing coffee shop list from: {args.input_file}")
    
    # Parse the CSV file
    coffee_shops = processor.parse_coffee_shop_csv(args.input_file)
    
    if not coffee_shops:
        print("❌ No coffee shops found in the CSV file")
        return
    
    print(f"✅ Found {len(coffee_shops)} coffee shops with valid place IDs!")
    
    if not args.quiet:
        # Display basic information about parsed shops
        print("\n📋 Parsed coffee shops:")
        for i, shop in enumerate(coffee_shops, 1):
            print(f"{i}. {shop['original_title']}")
            print(f"   🔗 URL: {shop['url'][:60]}...")
            print(f"   🆔 Place ID: {shop.get('place_id', 'N/A')}")
            if shop.get('note'):
                print(f"   📝 Note: {shop['note']}")
    
    # Enrich with Google Maps data
    if not args.quiet:
        print("\n" + "="*50)
        print("Enriching with Google Maps data")
        print("="*50)
    
    print("🔍 Getting detailed information from Google Maps...")
    
    # Enrich with detailed Google Maps information
    enriched_shops = processor.enrich_coffee_shops(coffee_shops)
    
    if not enriched_shops:
        print("❌ No shops were successfully enriched")
        return
    
    print(f"✅ Successfully enriched {len(enriched_shops)} coffee shops!")
    
    if not args.quiet:
        # Display detailed information for the first shop
        shop = enriched_shops[0]
        print(f"\n📋 Detailed info for: {shop['name']}")
        print(f"   📍 Address: {shop.get('formatted_address', 'N/A')}")
        print(f"   ⭐ Rating: {shop.get('rating', 'N/A')} ({shop.get('user_ratings_total', 'N/A')} reviews)")
        print(f"   📞 Phone: {shop.get('formatted_phone_number', 'N/A')}")
        print(f"   🌐 Website: {shop.get('website', 'N/A')}")
        print(f"   💰 Price Level: {shop.get('price_level', 'N/A')}")
        print(f"   🏢 Status: {shop.get('business_status', 'N/A')}")
        
        if 'opening_hours' in shop:
            print(f"   ⏰ Open now: {shop['opening_hours'].get('open_now', 'N/A')}")
            hours = shop['opening_hours'].get('weekday_text', [])
            if hours:
                print("   📅 Hours:")
                for hour in hours[:3]:  # Show first 3 days
                    print(f"      {hour}")
        
        if 'reviews' in shop:
            reviews = shop['reviews']
            print(f"   📝 Recent reviews ({len(reviews)} shown):")
            for review in reviews[:2]:  # Show first 2 reviews
                print(f"      ⭐ {review['rating']}/5 - {review['text'][:80]}...")
    
    # Create structured DataFrame
    if not args.quiet:
        print("\n" + "="*50)
        print("Creating structured DataFrame")
        print("="*50)
    
    df = create_coffee_shop_dataframe(enriched_shops)
    
    if df.empty:
        print("❌ Could not create DataFrame")
        return
    
    print(f"✅ Created DataFrame with {len(df)} coffee shops")
    
    if not args.quiet:
        print(f"📊 Columns: {', '.join(df.columns)}")
        
        # Display summary statistics
        print(f"\n📈 Summary Statistics:")
        print(f"   Average rating: {df['rating'].mean():.2f}")
        print(f"   Rating range: {df['rating'].min():.1f} - {df['rating'].max():.1f}")
        print(f"   Shops with websites: {df['website'].notna().sum()}")
        print(f"   Shops with phone numbers: {df['phone'].notna().sum()}")
        print(f"   Shops currently open: {df['open_now'].sum() if 'open_now' in df else 'N/A'}")
        
        # Display first few rows
        print(f"\n📋 Sample data (first 3 rows):")
        sample_columns = ['name', 'original_title', 'rating', 'vicinity', 'website']
        available_columns = [col for col in sample_columns if col in df.columns]
        print(df[available_columns].head(3).to_string(index=False))
    
    # Save to CSV
    df.to_csv(args.output_file, index=False)
    print(f"💾 Saved enriched data to {args.output_file}")
    
    # Export to GeoJSON if requested and we have location data
    if args.geojson and 'latitude' in df.columns and 'longitude' in df.columns:
        geojson_file = args.output_file.replace('.csv', '.geojson')
        export_to_geojson(df, geojson_file)
        print(f"🗺️ Exported GeoJSON to {geojson_file}")
    elif args.geojson:
        print("⚠️ Cannot export GeoJSON: missing latitude/longitude data")
    
    if not args.quiet:
        # Show what data is available for post generation
        print("\n" + "="*50)
        print("Data available for post generation")
        print("="*50)
        
        print("🎯 For each coffee shop, you now have access to:")
        print("   📍 Location data (address, coordinates)")
        print("   ⭐ Rating and review information")
        print("   📞 Contact information (phone, website)")
        print("   ⏰ Opening hours")
        print("   📸 Photo references")
        print("   💰 Price level information")
        print("   📝 Your original notes and tags")
        
        print(f"\n📊 Available data fields:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")
        
        # Show a detailed example of one coffee shop's data
        shop_data = df.iloc[0]
        print(f"\n📋 Complete data for '{shop_data['name']}':")
        for field, value in shop_data.items():
            if pd.notna(value) and value != '':
                print(f"   {field}: {value}")
        
        print("\n" + "="*50)
        print("✨ Processing completed!")
        print("="*50)
        print("\nNext steps:")
        print("1. Use the enriched CSV data to build your post generator")
        print("2. Access ratings, reviews, and photos for engaging content")
        print("3. Use location data to create location-specific posts")
        print("4. Leverage opening hours and contact info for practical content")
        print("5. Build automated workflows around this enriched data!")


if __name__ == "__main__":
    main() 