# coffee_project
An automatic post generator based on your existing coffee shop list with Google Maps metadata enrichment.

## 🚀 Features

- **Process Existing Lists**: Work with your curated coffee shop lists (CSV format)
- **Google Maps URL Parsing**: Extract place IDs from Google Maps URLs
- **Rich Metadata Enrichment**: Get ratings, reviews, hours, photos, and more
- **Photo Downloads**: Automatically download photo bytes from Google Maps
- **AI-Powered Reviews**: Generate work/study-focused reviews in English and Chinese
- **Structured Data Export**: Export to CSV, GeoJSON, and other formats
- **Post Generation Ready**: All data needed for automated content creation

## 📋 Prerequisites

1. **Google Maps API Key**: You'll need a Google Maps API key with the Places API enabled
2. **Anthropic API Key**: For AI-powered review generation (optional)
3. **Python 3.12+**: This project uses modern Python features
4. **Coffee Shop List**: CSV file with your coffee shop URLs from Google Maps

## 🛠️ Setup

### 1. Install Dependencies

```bash
# Assume that you have pyenv and uv installed.
pyenv local 3.12
uv venv .venv --python 3.12 --seed
source .venv/bin/activate
uv sync --frozen
uv pip install -e .
```

### 2. Get Google Maps API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Places API** for your project
4. Create an API key in the "Credentials" section
5. (Optional) Restrict the API key to the Places API for security

### 3. Configure API Keys

Create a `.env` file in the project root:

```bash
# Copy the template
cp config_template.env .env

# Edit the file and add your API keys
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here  # Optional, for AI reviews
```

**For AI-powered reviews**: 
1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. Add it to your `.env` file as shown above

### 4. Prepare Your Coffee Shop List

Create a CSV file with your coffee shop information. The expected format is:

```csv
Title,Note,URL,Tags,Comment
Voyager Craft Coffee - Cupertino,,https://www.google.com/maps/place/Voyager+Craft+Coffee+-+Cupertino/data=!4m2!3m1!1s0x808fb5de47226c47:0x39911f7160fe62a4,,
Sightglass Coffee,,https://www.google.com/maps/place/Sightglass+Coffee/data=!4m2!3m1!1s0x808580af3cd399d1:0xffceeb92a11a5a6d,,
```

Required columns:
- **Title**: Name of the coffee shop
- **URL**: Google Maps URL for the place
- **Note**, **Tags**, **Comment**: Optional additional information

## 🚀 Usage

### Quick Start

Run the example script to see the complete workflow:

```bash
# Basic usage with default files
uv run coffee_project/example_usage.py

# Specify custom input and output files
uv run coffee_project/example_usage.py --input_file my_coffee_shops.csv --output_file my_enriched_data.csv

# Export GeoJSON as well
uv run coffee_project/example_usage.py --output_file results.csv --geojson

# Quiet mode (minimal output)
uv run coffee_project/example_usage.py --output_file results.csv --quiet

# Generate AI-powered reviews (requires ANTHROPIC_API_KEY)
uv run coffee_project/example_usage.py --output_file results.csv --generate_reviews
```

### Command Line Options

- `--input_file`: Path to your CSV file with coffee shop list (default: `coffee_project/places_list/example_short_list.csv`)
- `--output_file`: Output CSV file path for enriched data (default: `enriched_coffee_shops.csv`)
- `--geojson`: Also export data as GeoJSON file
- `--generate_reviews`: Generate AI-powered reviews in English and Chinese (requires ANTHROPIC_API_KEY)
- `--quiet`: Suppress detailed output, only show essential information

### Basic Usage

```python
from coffee_project.google_maps_utils import CoffeeShopProcessor, create_coffee_shop_dataframe

# Initialize the processor
processor = CoffeeShopProcessor()

# Parse your coffee shop list
coffee_shops = processor.parse_coffee_shop_csv("my_coffee_shops.csv")

# Enrich with Google Maps data
enriched_shops = processor.enrich_coffee_shops(coffee_shops)

# Create structured DataFrame
df = create_coffee_shop_dataframe(enriched_shops)

# Save to CSV
df.to_csv("enriched_coffee_shops.csv", index=False)
```

### One-Line Processing

```python
from coffee_project.google_maps_utils import process_coffee_shop_list

# Process everything in one go
df = process_coffee_shop_list(
    csv_file_path="my_coffee_shops.csv",
    output_csv="enriched_output.csv",
    output_geojson="enriched_output.geojson"
)
```

## 📊 Data Fields

The enriched coffee shop data includes:

### Original Data (from your CSV)
- **original_title**: Your original title
- **note**: Your notes
- **tags**: Your tags
- **comment**: Your comments
- **original_url**: Original Google Maps URL

### Google Maps Data
- **name**: Official place name
- **formatted_address**: Full address
- **rating**: Average rating (1-5)
- **user_ratings_total**: Number of reviews
- **price_level**: Price level (0-4)
- **phone**: Phone number
- **website**: Official website
- **business_status**: Operational status
- **latitude/longitude**: Coordinates
- **opening_hours**: Hours of operation
- **photo_references**: Photo data
- **photo_bytes**: Downloaded photo bytes (binary data)
- **recent_reviews**: Review samples

### AI-Generated Content (Optional)
- **generated_review_en**: AI-generated review in English focused on work/study suitability
- **generated_review_zh**: AI-generated review in Chinese focused on work/study suitability

## 🔧 How It Works

### 1. URL Parsing
The system extracts place IDs from Google Maps URLs using multiple methods:
- Direct place_id parameters
- Data parameter parsing
- Place name extraction and search
- URL structure analysis

### 2. Data Enrichment
For each place ID, the system calls the Google Maps Places API to get:
- Detailed business information
- Current ratings and reviews
- Operating hours and contact info
- Photos and additional metadata

### 3. Photo Downloads
The system automatically downloads photo bytes from Google Maps:
- Uses the legacy Photo API for compatibility
- Downloads photos at specified resolution (default 400x400)
- Stores photo bytes directly in the data structure

### 4. AI-Powered Review Generation (Optional)
Using Anthropic's Claude, the system generates specialized reviews:
- Focuses on work/study suitability (WiFi, outlets, long-stay policy)
- Includes practical information (hours, accessibility)
- Generates reviews in both English and Chinese
- Based on existing customer reviews and place metadata

### 5. Data Structure
The final output combines your original data with Google Maps data and AI-generated content in a structured format perfect for:
- Automated post generation
- Content management systems
- Analysis and reporting
- Mapping applications

## 📝 Examples

The `example_usage.py` script demonstrates:

1. **CSV Parsing**: Reading your coffee shop list
2. **URL Processing**: Extracting place IDs from Google Maps URLs
3. **Data Enrichment**: Getting detailed Google Maps information
4. **Data Processing**: Creating structured DataFrames
5. **Export Options**: Saving to CSV and GeoJSON formats

## 🚨 Important Notes

### Google Maps API Considerations

1. **Rate Limits**: The API has usage limits and quotas
2. **Costs**: API calls may incur charges after free tier limits
3. **Place ID Extraction**: Some URL formats may not be supported

### URL Format Requirements

The system works best with Google Maps URLs that contain:
- Place IDs in URL parameters
- Place names in the URL path
- Standard Google Maps URL structure

## 🎯 Perfect for Post Generation

This tool is specifically designed for automated content creation:

- **Rich Context**: Ratings, reviews, and photos for engaging posts
- **Photo Content**: Downloaded photo bytes ready for posting
- **AI-Generated Reviews**: Work/study-focused reviews in multiple languages
- **Location Data**: Coordinates and addresses for location-based content
- **Business Info**: Hours, contact details, and current status
- **Your Personal Touch**: Your original notes and tags preserved
- **Structured Format**: Ready for templating and automation

## 💡 Tips

1. **URL Collection**: Copy URLs directly from Google Maps by clicking "Share" → "Copy link"
2. **Batch Processing**: Process large lists efficiently with rate limiting built-in
3. **Data Validation**: Check the output for any places that couldn't be processed
4. **Regular Updates**: Re-run processing periodically to get updated ratings and reviews

## 🤝 Contributing

Feel free to contribute improvements, bug fixes, or new features!

## 📄 License

This project is for personal use. Please respect Google's Terms of Service when using their APIs.