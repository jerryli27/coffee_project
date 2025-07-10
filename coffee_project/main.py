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

from anthropic_utils import ReviewGenerator
from google_maps_utils import (CoffeeShopProcessor,
                               create_coffee_shop_dataframe, export_to_geojson,
                               process_coffee_shop_list)
from html_utils import generate_html_files, generate_index_html


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process a coffee shop list and enrich it with Google Maps metadata"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="ignore/",
        help=(
            "Output path for the enriched coffee shop data. The dataframe will be saved as a parquet file named "
            "'enriched_coffee_shops.parquet' under the output path."
        )
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default="coffee_project/places_list/example_short_list.csv",
        help="Input CSV file path with coffee shop list (default: coffee_project/places_list/example_short_list.csv)"
    )
    parser.add_argument(
        "--geojson",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Also export data as GeoJSON file"
    )
    parser.add_argument(
        "--quiet",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Suppress detailed output, only show essential information"
    )
    parser.add_argument(
        "--generate_reviews",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate AI-powered reviews for each coffee shop (requires ANTHROPIC_API_KEY)"
    )
    parser.add_argument(
        "--generate_html",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate HTML files for each coffee shop"
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
    
    # Generate reviews if requested
    if args.generate_reviews:
        if not args.quiet:
            print("\n" + "="*50)
            print("Generating AI-powered reviews")
            print("="*50)
        
        try:
            review_generator = ReviewGenerator()
            print("🤖 Generating reviews with Anthropic AI...")
            
            # Generate reviews for all coffee shops
            enriched_shops = review_generator.generate_reviews_for_list(enriched_shops)
            
            print(f"✅ Generated reviews for {len(enriched_shops)} coffee shops!")
            
            if not args.quiet:
                # Display sample review for the first shop
                shop = enriched_shops[0]
                reviews = shop.get('generated_reviews', {})
                print(f"\n📝 Sample review for '{shop['name']}':")
                print(f"   🇺🇸 English: {reviews.get('en', 'N/A')[:100]}...")
                print(f"   🇨🇳 中文: {reviews.get('zh', 'N/A')[:100]}...")
                
        except ValueError as e:
            print(f"❌ Error initializing review generator: {e}")
            print("\nTo fix this:")
            print("1. Get an Anthropic API key from: https://console.anthropic.com/")
            print("2. Set the API key as an environment variable:")
            print("   export ANTHROPIC_API_KEY='your_api_key_here'")
            print("   or create a .env file with: ANTHROPIC_API_KEY=your_api_key_here")
            print("3. Continuing without review generation...")
    
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
    
    # Create output directory
    output_path = Path(args.output_path, os.path.splitext(os.path.basename(args.input_file))[0])
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    parquet_file = output_path / "enriched_coffee_shops.parquet"
    df.to_parquet(parquet_file)
    print(f"💾 Saved enriched data to {parquet_file}")
    
    # Export to GeoJSON if requested and we have location data
    if args.geojson and 'latitude' in df.columns and 'longitude' in df.columns:
        geojson_file = output_path / "enriched_coffee_shops.geojson"
        export_to_geojson(df, geojson_file)
        print(f"🗺️ Exported GeoJSON to {geojson_file}")
    elif args.geojson:
        print("⚠️ Cannot export GeoJSON: missing latitude/longitude data")
    
    # Generate HTML files if requested
    if args.generate_html:
        if not args.quiet:
            print("\n" + "="*50)
            print("Generating HTML files")
            print("="*50)
        
        print("🌐 Generating HTML files and saving images for each coffee shop...")
        html_files_by_city = generate_html_files(enriched_shops, str(output_path))
        
        if html_files_by_city:
            total_files = sum(len(files) for files in html_files_by_city.values())
            print(f"✅ Generated {total_files} HTML files with images in {len(html_files_by_city)} cities")
            
            # Generate index HTML
            index_file = generate_index_html(enriched_shops, str(output_path), html_files_by_city)
            print(f"📄 Generated index file: {index_file}")
            
            if not args.quiet:
                print(f"🔗 Open {index_file} in your browser to view all coffee shops")
                print(f"🏙️ Cities: {', '.join(sorted(html_files_by_city.keys()))}")
        else:
            print("⚠️ No HTML files were generated")
    
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
        print("   📸 Photo references and photo bytes")
        print("   💰 Price level information")
        print("   📝 Your original notes and tags")
        if args.generate_reviews:
            print("   🤖 AI-generated reviews in English and Chinese")
        if args.generate_html:
            print("   🌐 Individual HTML pages for each coffee shop")
        
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


if __name__ == "__main__":
    main() 