#!/usr/bin/env python3
"""
Validate and fix asset format for PocketOption API compatibility
"""

import re
from pocketoptionapi_async.constants import ASSETS

def convert_html_to_api_format(asset_name):
    """Convert HTML asset name to PocketOption API format"""
    if not asset_name:
        return None
    
    # Remove spaces and convert to uppercase
    asset = asset_name.upper().replace(" ", "")
    
    # Handle OTC assets
    if asset.endswith("OTC"):
        # Remove OTC and add _otc suffix
        base_asset = asset[:-3]  # Remove "OTC"
        # Convert slashes to nothing (EUR/USD -> EURUSD)
        base_asset = base_asset.replace("/", "")
        return f"{base_asset}_otc"
    else:
        # Regular assets - just remove slashes
        return asset.replace("/", "")

def validate_assets():
    """Validate current assets and show correct format"""
    print("=" * 80)
    print("🔍 VALIDATING ASSET FORMATS")
    print("=" * 80)
    
    # Original extracted assets from HTML
    html_assets = [
        "AED/CNY OTC", "AUD/CAD OTC", "AUD/CHF OTC", "AUD/JPY OTC", "AUD/NZD OTC",
        "AUD/USD OTC", "BHD/CNY OTC", "CAD/CHF OTC", "CAD/JPY OTC", "CHF/JPY OTC",
        "CHF/NOK OTC", "EUR/CHF OTC", "EUR/GBP OTC", "EUR/HUF OTC", "EUR/JPY OTC",
        "EUR/NZD OTC", "EUR/TRY OTC", "EUR/USD OTC", "GBP/AUD OTC", "GBP/JPY OTC",
        "GBP/USD OTC", "JOD/CNY OTC", "KES/USD OTC", "LBP/USD OTC", "MAD/USD OTC",
        "NGN/USD OTC", "NZD/JPY OTC", "NZD/USD OTC", "OMR/CNY OTC", "QAR/CNY OTC",
        "SAR/CNY OTC", "TND/USD OTC", "UAH/USD OTC", "USD/ARS OTC", "USD/BDT OTC",
        "USD/BRL OTC", "USD/CAD OTC", "USD/CHF OTC", "USD/CLP OTC", "USD/CNH OTC",
        "USD/COP OTC", "USD/DZD OTC", "USD/EGP OTC", "USD/IDR OTC", "USD/INR OTC",
        "USD/JPY OTC", "USD/MXN OTC", "USD/MYR OTC", "USD/PHP OTC", "USD/PKR OTC",
        "USD/RUB OTC", "USD/SGD OTC", "USD/THB OTC", "ZAR/USD OTC", "EUR/RUB OTC",
        "USD/VND OTC", "YER/USD OTC",
        "AUD/CAD", "AUD/CHF", "AUD/JPY", "AUD/USD", "CAD/CHF", "CAD/JPY",
        "CHF/JPY", "EUR/AUD", "EUR/CAD", "EUR/CHF", "EUR/GBP", "EUR/JPY",
        "EUR/USD", "GBP/AUD", "GBP/CAD", "GBP/CHF", "GBP/JPY", "GBP/USD",
        "USD/CAD", "USD/CHF", "USD/JPY"
    ]
    
    print(f"📊 Total assets to convert: {len(html_assets)}")
    print("\n" + "=" * 80)
    print("🔄 CONVERSION RESULTS")
    print("=" * 80)
    
    converted_assets = {}
    major_pairs = {'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD'}
    
    for i, html_asset in enumerate(html_assets, 1):
        api_format = convert_html_to_api_format(html_asset)
        converted_assets[api_format] = i
        
        # Check if it's a major pair that shouldn't have _otc
        if api_format and api_format.endswith('_otc'):
            base = api_format[:-4]
            if base in major_pairs:
                status = "⚠️ Major pair - consider removing _otc"
            else:
                status = "✅ Correct OTC format"
        elif api_format in major_pairs:
            status = "✅ Correct major pair format"
        else:
            status = "✅ Regular format"
        
        print(f"{i:2d}. {html_asset:<20} -> {api_format:<15} {status}")
    
    return converted_assets

def generate_corrected_constants():
    """Generate corrected constants.py content"""
    converted_assets = validate_assets()
    
    print("\n" + "=" * 80)
    print("📝 GENERATING CORRECTED CONSTANTS.PY")
    print("=" * 80)
    
    constants_content = '''"""
Constants and configuration for the PocketOption API
"""

from typing import Dict, List
import random

# Asset mappings with their corresponding IDs - Corrected API format
ASSETS: Dict[str, int] = {
'''
    
    # Sort assets by type
    otc_assets = {k: v for k, v in converted_assets.items() if k.endswith('_otc')}
    regular_assets = {k: v for k, v in converted_assets.items() if not k.endswith('_otc')}
    
    # Add OTC assets
    constants_content += "    # OTC Currency Pairs\n"
    for asset, asset_id in sorted(otc_assets.items()):
        constants_content += f'    "{asset}": {asset_id},\n'
    
    constants_content += "\n    # Regular Currency Pairs (Non-OTC)\n"
    for asset, asset_id in sorted(regular_assets.items()):
        constants_content += f'    "{asset}": {asset_id},\n'
    
    constants_content += '''}


# WebSocket regions with their URLs
class Regions:
    """WebSocket region endpoints"""

    _REGIONS = {
        "EUROPA": "wss://api-eu.po.market/socket.io/?EIO=4&transport=websocket",
        "SEYCHELLES": "wss://api-sc.po.market/socket.io/?EIO=4&transport=websocket",
        "HONGKONG": "wss://api-hk.po.market/socket.io/?EIO=4&transport=websocket",
        "SERVER1": "wss://api-spb.po.market/socket.io/?EIO=4&transport=websocket",
        "FRANCE2": "wss://api-fr2.po.market/socket.io/?EIO=4&transport=websocket",
        "UNITED_STATES4": "wss://api-us4.po.market/socket.io/?EIO=4&transport=websocket",
        "UNITED_STATES3": "wss://api-us3.po.market/socket.io/?EIO=4&transport=websocket",
        "UNITED_STATES2": "wss://api-us2.po.market/socket.io/?EIO=4&transport=websocket",
        "DEMO": "wss://demo-api-eu.po.market/socket.io/?EIO=4&transport=websocket",
        "DEMO_2": "wss://try-demo-eu.po.market/socket.io/?EIO=4&transport=websocket",
        "UNITED_STATES": "wss://api-us-north.po.market/socket.io/?EIO=4&transport=websocket",
        "RUSSIA": "wss://api-msk.po.market/socket.io/?EIO=4&transport=websocket",
        "SERVER2": "wss://api-l.po.market/socket.io/?EIO=4&transport=websocket",
        "INDIA": "wss://api-in.po.market/socket.io/?EIO=4&transport=websocket",
        "FRANCE": "wss://api-fr.po.market/socket.io/?EIO=4&transport=websocket",
        "FINLAND": "wss://api-fin.po.market/socket.io/?EIO=4&transport=websocket",
        "SERVER3": "wss://api-c.po.market/socket.io/?EIO=4&transport=websocket",
        "ASIA": "wss://api-asia.po.market/socket.io/?EIO=4&transport=websocket",
        "SERVER4": "wss://api-us-south.po.market/socket.io/?EIO=4&transport=websocket",
    }

    @classmethod
    def get_all(cls, randomize: bool = True) -> List[str]:
        """Get all region URLs"""
        urls = list(cls._REGIONS.values())
        if randomize:
            random.shuffle(urls)
        return urls

    @classmethod
    def get_all_regions(cls) -> Dict[str, str]:
        """Get all regions as a dictionary"""
        return cls._REGIONS.copy()

    from typing import Optional

    @classmethod
    def get_region(cls, region_name: str) -> Optional[str]:
        """Get specific region URL"""
        return cls._REGIONS.get(region_name.upper())

    @classmethod
    def get_demo_regions(cls) -> List[str]:
        """Get demo region URLs"""
        return [url for name, url in cls._REGIONS.items() if "DEMO" in name]


# Global constants
REGIONS = Regions()

# Timeframes (in seconds)
TIMEFRAMES = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
    "1w": 604800,
}

# Connection settings
CONNECTION_SETTINGS = {
    "ping_interval": 20,  # seconds
    "ping_timeout": 10,  # seconds
    "close_timeout": 10,  # seconds
    "max_reconnect_attempts": 5,
    "reconnect_delay": 5,  # seconds
    "message_timeout": 30,  # seconds
}

# API Limits
API_LIMITS = {
    "min_order_amount": 1.0,
    "max_order_amount": 50000.0,
    "min_duration": 5,  # seconds
    "max_duration": 43200,  # 12 hours in seconds
    "max_concurrent_orders": 10,
    "rate_limit": 100,  # requests per minute
}

# Default headers
DEFAULT_HEADERS = {
    "Origin": "https://pocketoption.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}'''
    
    # Save corrected constants
    with open('pocketoptionapi_async/constants_corrected.py', 'w', encoding='utf-8') as f:
        f.write(constants_content)
    
    print("✅ Generated corrected constants file: pocketoptionapi_async/constants_corrected.py")
    
    return converted_assets

def main():
    """Main function"""
    print("🚀 Starting asset format validation...")
    converted_assets = generate_corrected_constants()
    
    print("\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    print(f"✅ Converted {len(converted_assets)} assets to API format")
    print("✅ Generated corrected constants file")
    print("\n🔧 Next steps:")
    print("1. Review the corrected format in constants_corrected.py")
    print("2. Replace the original constants.py if format looks correct")
    print("3. Test with PocketOption API")

if __name__ == "__main__":
    main()