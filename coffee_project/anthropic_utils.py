"""Utility functions for generating reviews using Anthropic."""

import logging
import os
from typing import Any, Dict, List, Optional
import json
import time

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class ReviewGenerator:
    """A client for generating reviews using Anthropic."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Anthropic client.
        
        Args:
            api_key: Anthropic API key. If not provided, will try to load from
                    environment variable ANTHROPIC_API_KEY.
        """
        if api_key is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. Please set ANTHROPIC_API_KEY "
                "environment variable or pass api_key parameter."
            )
        
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generate_review(self, coffee_shop_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate a review for a coffee shop in English and Mandarin.
        
        Args:
            coffee_shop_data: Dictionary containing enriched coffee shop data
            
        Returns:
            Dictionary with language codes ('en', 'zh') mapped to review text
        """
        try:
            # Extract key information from the coffee shop data
            name = coffee_shop_data.get('name', 'Unknown Place')
            address = coffee_shop_data.get('formatted_address', 'Address not available')
            rating = coffee_shop_data.get('rating', 'N/A')
            rating_count = coffee_shop_data.get('user_ratings_total', 0)
            phone = coffee_shop_data.get('formatted_phone_number', 'N/A')
            website = coffee_shop_data.get('website', 'N/A')
            price_level = coffee_shop_data.get('price_level', 'N/A')
            business_status = coffee_shop_data.get('business_status', 'N/A')
            place_types = coffee_shop_data.get('type', [])
            
            # Opening hours information
            opening_hours = coffee_shop_data.get('opening_hours', {})
            hours_text = '\n'.join(opening_hours.get('weekday_text', [])) if opening_hours else 'Hours not available'
            open_now = opening_hours.get('open_now', False) if opening_hours else False
            
            # Recent reviews for context
            reviews = coffee_shop_data.get('reviews', [])
            recent_reviews = []
            for review in reviews[:5]:  # Get up to 5 recent reviews
                review_text = review.get('text', '')
                review_rating = review.get('rating', 'N/A')
                recent_reviews.append(f"Rating: {review_rating}/5 - {review_text}")
            
            # Create the prompt
            prompt = f"""
You are writing a review for a place that is suitable for work, studying, or reading. Based on the information provided, write a comprehensive review in both English and Mandarin Chinese.

PLACE INFORMATION:
- Name: {name}
- Address: {address}
- Google Rating: {rating}/5 ({rating_count} reviews)
- Place Types: {', '.join(place_types)}

OPENING HOURS:
{hours_text}

RECENT CUSTOMER REVIEWS:
{chr(10).join(recent_reviews) if recent_reviews else 'No recent reviews available'}

REVIEW REQUIREMENTS:
1. Focus on suitability for work, studying, and reading
2. When these attributes are present, include them in the review (don't force it):
   - Can you stay for long periods?
   - Free WiFi availability
   - Power outlets availability
   - Any highlights of the place, e.g. the view, the atmosphere, the food, the drinks, etc.
3. Include practical information but prioritize the tone:
   - Weekend hours and closing times
   - Accessibility and ease of getting there
4. Keep the tone casual. Keep in mind that the writer has been to the place and is writing from a personal experience. Focus on the overall impression of the place.
5. Write simple reviews, 20 to 50 words each.

OUTPUT FORMAT:
Return your response as a JSON object with exactly this structure:
{{
    "zh": "中文评论文本在这里"
}}

Example reviews as writing style references:

伦敦自习咖啡馆推荐 1
Redemption Roasters - Holborn
一直都有位子 离地铁站也就3分钟 想要聊天可以在一楼 想专心工作的下楼有很多位子和插座 wifi也很稳定#伦敦 #咖啡馆 #自习室 #工作使我快乐
伦敦自习咖啡馆推荐2
Shaman at Buckle Street Studios
Shaman 的其他店已经有很多人推过了 有一天路过的时候突然发现这一家
一楼二楼都有很多座位 有插座有网 离地铁站也就3分钟 周末住附近的在家忍不住摸鱼的十分推荐来这儿

#伦敦 #咖啡馆 #自习室 #工作使我快乐
伦敦自习咖啡馆推荐3
这家Harris + Hoole感觉没人推荐过 离UCL近 周围也有好多人学习 写作或者约coffee chat 挺有氛围的
有插座有网有咖啡 夫复何求
#伦敦咖啡  #伦敦自习  #自习室 #适合学习的咖啡厅
"""

            # Call Anthropic API
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                temperature=1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the response
            response_text = response.content[0].text
            logger.info(f"Generated review for {name}")
            # Look for the first "{" and last "}"
            start_index = response_text.find("{")
            end_index = response_text.rfind("}") + 1
            response_json = response_text[start_index:end_index]
            
            # Try to parse as JSON
            try:
                reviews_dict = json.loads(response_json)
                required_languages = ['en', 'zh']
                for lang in required_languages:
                    if lang not in reviews_dict:
                        reviews_dict[lang] = "Review generation failed"
                return reviews_dict
            except json.JSONDecodeError:
                logger.warning(f"Could not parse JSON response: {response_text}")
                return {"en": response_text, "zh": "Review generation failed"}
            
        except Exception as e:
            logger.error(f"Error generating review for {coffee_shop_data.get('name', 'Unknown')}: {e}")
            return {"en": "Review generation failed", "zh": "评论生成失败"}
    
    def generate_reviews_for_list(self, coffee_shops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate reviews for a list of coffee shops.
        
        Args:
            coffee_shops: List of enriched coffee shop data
            
        Returns:
            List of coffee shop data with added reviews
        """
        enriched_shops = []
        
        for shop in coffee_shops:
            logger.info(f"Generating review for: {shop.get('name', 'Unknown')}")
            
            # Generate review
            reviews = self.generate_review(shop)
            
            # Add reviews to the shop data
            enriched_shop = {**shop}
            enriched_shop['generated_reviews'] = reviews
            enriched_shops.append(enriched_shop)
            
            # Add delay to respect API rate limits
            time.sleep(1)
        
        logger.info(f"Generated reviews for {len(enriched_shops)} coffee shops")
        return enriched_shops


def generate_reviews_for_coffee_shops(coffee_shops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convenience function to generate reviews for coffee shops.
    
    Args:
        coffee_shops: List of enriched coffee shop data
        
    Returns:
        List of coffee shop data with added reviews
    """
    generator = ReviewGenerator()
    return generator.generate_reviews_for_list(coffee_shops)
