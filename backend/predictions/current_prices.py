import re
import requests
from bs4 import BeautifulSoup


# ============================================================================================
# WEB SCRAPER FOR SRI LANKA PROPERTY PRICES
# Extracts sales, rental, and land prices for all provinces and districts
# ============================================================================================

# ============================================================================================
# PROVINCES AND DISTRICTS MAPPING
# ============================================================================================

PROVINCES_DISTRICTS = {
    "Colombo": ["colombo", "kalutara"],
    "Western Province (apart from Colombo city)": ["gampaha", "kalutara"],
    "Southern province": ["galle", "matara", "hambantota"],
    "Central province": ["kandy", "matale", "nuwara eliya"],
    "North West province": ["kurunegala", "puttalam"],
    "North Central province": ["polonnaruwa", "anuradhapura"],
    "Uva province": ["badulla", "monaragala"],
    "Sabaragamuwa province": ["ratnapura", "kegalle"],
    "Eastern province": ["batticaloa", "ampara", "trincomalee"],
    "Northern Province": ["jaffna", "mullaitivu", "vavuniya", "mannar", "kilinochchi"],
    "Sri Lanka Overall": ["national average"]
}


def get_districts_for_province(province_name: str) -> list:
    """Get list of districts for a given province"""
    for province, districts in PROVINCES_DISTRICTS.items():
        if province.lower() in province_name.lower() or province_name.lower() in province.lower():
            return districts
    return []


def get_province_for_district(district: str) -> str:
    """Get province name for a given district"""
    for province, districts in PROVINCES_DISTRICTS.items():
        if district.lower() in [d.lower() for d in districts]:
            return province
    return None


def convert_district_targets_to_province_targets(district_targets: list) -> list:
    """
    Convert district-based targets to province-based targets
    Example: ['Kandy Sale', 'Colombo Rental'] -> ['Central province House Sale price', ...]
    
    Args:
        district_targets: List of targets in format 'District Type' or 'District Price Type'
                         Examples: 'Kandy Sale', 'Colombo Rental', 'Galle Land'
    
    Returns:
        list: List of province-based targets ready for extraction
    """
    province_targets = set()
    
    for target in district_targets:
        parts = target.split()
        if len(parts) < 2:
            continue
        
        # First part is district, rest is type
        district_name = parts[0]
        type_desc = ' '.join(parts[1:]).lower()
        
        # Find the province for this district
        province = get_province_for_district(district_name)
        if not province:
            continue
        
        # Convert to province-based targets
        if 'sale' in type_desc:
            province_targets.add(f"{province} House Sale price")
        elif 'rental' in type_desc or 'rent' in type_desc:
            province_targets.add(f"{province} House Rental price")
        elif 'land' in type_desc:
            province_targets.add(f"{province} Residential Land price")
    
    # Always add fallback targets for filling missing data
    fallback_targets = [
        'Overall Residential Land price',
        'Sri Lanka Overall House Sale price',
        'Sri Lanka Overall House Rental price',
        'Colombo House Rental price'
    ]
    
    return list(province_targets) + fallback_targets


def expand_to_districts(province_name: str, value: str) -> dict:
    """
    Expand a province price to all its districts
    
    Args:
        province_name: Name of the province
        value: Price value (with units like "1.53 million Per perch")
    
    Returns:
        dict: Dictionary with district names as keys and numeric values as values
    """
    districts = get_districts_for_province(province_name)
    numeric_value = parse_price_value(value)
    return {district: numeric_value for district in districts}


def parse_price_value(value_str: str) -> float:
    """
    Parse price value from string and convert to actual number
    Examples: "1.53 million Per perch" -> 1530000, "657,000" -> 657000
    """
    value_str = str(value_str).replace("Per perch", "").replace("Per acre", "").strip()
    value_str = value_str.replace(",", "")
    
    if "million" in value_str.lower():
        value_str = value_str.lower().replace("million", "").strip()
        try:
            return round(float(value_str) * 1_000_000)
        except ValueError:
            return 0.0
    
    try:
        return round(float(value_str))
    except ValueError:
        return 0.0


def format_price_display(value: float) -> str:
    """Format numeric price value for display with commas"""
    return f"{round(value):,}"


# ============================================================================================
# WEB SCRAPING UTILITIES
# ============================================================================================

# ---------- UTILITIES ----------
def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith(("http://", "https://")):
        return raw
    return f"https://{raw}"


# ---------- FETCH PAGE ----------
def get_url(url: str, session: requests.Session) -> str:
    """Fetch HTML content from URL"""
    normalized = normalize_url(url)
    response = session.get(normalized, timeout=30)
    if response.status_code == 200:
        return response.text
    raise ValueError(f"Unable to fetch {normalized}: status {response.status_code}")


# ============================================================================================
# TABLE EXTRACTION
# ============================================================================================

def extract_tables(soup: BeautifulSoup):
    """Extract tables with headers and rows from HTML"""
    tables_data = []
    for table in soup.find_all("table"):
        table_info = {"headers": [], "rows": [], "column_count": 0, "row_count": 0}
        
        # Extract headers
        thead = table.find("thead")
        if thead:
            header_row = thead.find("tr")
            if header_row:
                for th in header_row.find_all(["th", "td"]):
                    text = th.get_text().strip()
                    if text:
                        # Clean up extra whitespace
                        text = " ".join(text.split())
                        table_info["headers"].append(text)
        
        # Extract rows
        tbody = table.find("tbody")
        rows_container = tbody if tbody else table
        
        for tr in rows_container.find_all("tr"):
            if tr.find_parent("thead"):
                continue
            cells = []
            for td in tr.find_all(["td", "th"]):
                text = td.get_text().strip()
                text = " ".join(text.split())
                cells.append(text)
            if cells:
                table_info["rows"].append(cells)
        
        if not table_info["headers"] and table_info["rows"]:
            table_info["headers"] = [f"Column {i+1}" for i in range(len(table_info["rows"][0]))]
        
        table_info["column_count"] = len(table_info["headers"]) if table_info["headers"] else 0
        table_info["row_count"] = len(table_info["rows"])
        
        if table_info["rows"]:
            tables_data.append(table_info)
    
    return tables_data


# ============================================================================================
# PRICE PROCESSING AND EXTRACTION
# ============================================================================================

def extract_target_values(tables_data: list, targets: list) -> dict:
    """Extract specific target values from tables"""
    extracted_results = {}
    for table in tables_data:
        for row in table['rows']:
            if len(row) == 0:
                continue
            row_type = row[0]
            if len(row) == 2:
                if row_type in targets:
                    extracted_results[row_type] = {"Average Price": row[1]}
            elif len(row) >= 3:
                if row_type in targets:
                    extracted_results[row_type] = {
                        "Average Price": row[1],
                        "Change": row[2]
                    }
    return extracted_results


def fill_insufficient_data(extracted_results: dict) -> dict:
    """Replace 'Insufficient data' values with fallback values"""
    land_fallback = extracted_results.get('Overall Residential Land price', {}).get('Average Price', 'N/A')
    sales_fallback = extracted_results.get('Sri Lanka Overall House Sale price', {}).get('Average Price', 'N/A')
    rental_fallback = extracted_results.get('Sri Lanka Overall House Rental price', {}).get('Average Price', None)
    
    if rental_fallback is None or rental_fallback == 'Insufficient data':
        rental_fallback = extracted_results.get('Colombo House Rental price', {}).get('Average Price', 'N/A')
    
    for key, values in extracted_results.items():
        if isinstance(values, dict) and values.get('Average Price') == 'Insufficient data':
            if 'Residential Land' in key or 'Tea Land' in key or 'Rubber Land' in key or 'Coconut Land' in key:
                if land_fallback != 'N/A':
                    values['Average Price'] = land_fallback
            elif 'Rental price' in key:
                if rental_fallback != 'N/A' and rental_fallback is not None:
                    values['Average Price'] = rental_fallback
            elif 'Sale price' in key:
                if sales_fallback != 'N/A':
                    values['Average Price'] = sales_fallback
    
    return extracted_results



def web_scraper(custom_targets=None):
    """
    Web scraper that extracts tables and specific province data.
    
    Args:
        custom_targets (list): Optional list of targets in district-type format.
                              Examples: ['Kandy Sale', 'Colombo Rental', 'Galle Land']
                              If None, uses default targets (all provinces, all types)
    
    Returns:
        dict: Extracted data organized by sales, rentals, lands with all districts
    """

    sites = [
        "https://www.lankapropertyweb.com/house_prices.php"
    ]
    
    for site in sites:
        try:
            session = requests.Session()
            html = get_url(site, session)
            soup = BeautifulSoup(html, "html.parser")
            tables_data = extract_tables(soup)
            
            # Define targets - convert custom if provided, otherwise use defaults
            if custom_targets:
                # Convert district-type targets to province targets
                targets = convert_district_targets_to_province_targets(custom_targets)
            else:
                targets = [
                    # Sales Prices - All Provinces
                    'Colombo House Sale price',
                    'Colombo Apartment Sale price',
                    'Colombo Commercial Buildings Sale price',
                    'Western Province (apart from Colombo city) House Sale price',
                    'Southern province House Sale price',
                    'Central province House Sale price',
                    'North West province House Sale price',
                    'North Central province House Sale price',
                    'Uva province House Sale price',
                    'Sabaragamuwa province House Sale price',
                    'Eastern province House Sale price',
                    'Northern Province House Sale price',
                    'Sri Lanka Overall House Sale price',
                    # Land Prices - All Provinces
                    'Overall Residential Land price',
                    'Colombo Residential Land price',
                    'Western Province (apart from Colombo city) Residential Land price',
                    'Southern province Residential Land price',
                    'Central province Residential Land price',
                    'North West province Residential Land price',
                    'North Central province Residential Land price',
                    'Uva province Residential Land price',
                    'Sabaragamuwa province Residential Land price',
                    'Eastern province Residential Land price',
                    'Northern Province Residential Land price',
                    'Overall Tea Land price',
                    'Overall Rubber Land price',
                    'Overall Coconut Land price',
                    # Rental Prices - All Provinces
                    'Colombo House Rental price',
                    'Colombo Apartment Rental price',
                    'Western Province (apart from Colombo city) House Rental price',
                    'Southern province House Rental price',
                    'Central province House Rental price',
                    'North West province House Rental price',
                    'North Central province House Rental price',
                    'Uva province House Rental price',
                    'Sabaragamuwa province House Rental price',
                    'Eastern province House Rental price',
                    'Northern Province House Rental price',
                    'Sri Lanka Overall House Rental price'
                ]
            
            # Extract specific targets
            extracted_results = extract_target_values(tables_data, targets)
            
            # Initialize district data structure with all districts from all provinces
            all_districts_data = {"sales": {}, "rentals": {}, "lands": {}}
            all_districts = set()
            for districts in PROVINCES_DISTRICTS.values():
                all_districts.update(districts)
            
            if extracted_results:
                # Fill insufficient data with fallback values
                extracted_results = fill_insufficient_data(extracted_results)
                sales_prices = {}
                land_prices = {}
                rental_prices = {}
                
                # Organize by type
                for item, values in extracted_results.items():
                    if 'Rental price' in item:
                        rental_prices[item] = values
                    elif 'Sale price' in item:
                        sales_prices[item] = values
                    else:
                        land_prices[item] = values
                
                # Process Sales Prices (By District)
                if sales_prices:
                    print("\n--- SALES PRICES (By District) ---")
                    for province, values in sales_prices.items():
                        # Parse numeric value
                        numeric_value = parse_price_value(values['Average Price'])
                        
                        # Expand to districts
                        districts = expand_to_districts(province, values['Average Price'])
                        
                        # Store and display
                        for district, price in districts.items():
                            all_districts_data["sales"][district] = price
                            formatted_price = format_price_display(price)
                            change_str = f" (Change: {values.get('Change', 'N/A')})" if 'Change' in values else ""
                            #print(f"  ✓ {district}: {formatted_price}{change_str}")
                
                # Process Rental Prices
                if rental_prices:
                    print("\n--- RENTAL PRICES (By District) ---")
                    for province, values in rental_prices.items():
                        # Parse numeric value
                        numeric_value = parse_price_value(values['Average Price'])
                        
                        # Expand to districts
                        districts = expand_to_districts(province, values['Average Price'])
                        
                        # Store and display
                        for district, price in districts.items():
                            if district not in all_districts_data["rentals"]:
                                all_districts_data["rentals"][district] = price
                            if all_districts_data["rentals"][district] == 0:
                                all_districts_data["rentals"][district] = price
                            
                            formatted_price = format_price_display(price)
                            change_str = f" (Change: {values.get('Change', 'N/A')})" if 'Change' in values else ""
                            #print(f"  ✓ {district}: {formatted_price}{change_str}")
                
                # Process Land Prices
                if land_prices:
                    print("\n--- LAND PRICES (By District) ---")
                    for item_type, values in land_prices.items():
                        # Parse numeric value
                        numeric_value = parse_price_value(values['Average Price'])
                        
                        # Expand to districts
                        districts = expand_to_districts(item_type, values['Average Price'])
                        
                        # Store and display
                        for district, price in districts.items():
                            if district not in all_districts_data["lands"]:
                                all_districts_data["lands"][district] = price
                            if all_districts_data["lands"][district] == 0:
                                all_districts_data["lands"][district] = price
                            
                            formatted_price = format_price_display(price)
                            change_str = f" (Change: {values.get('Change', 'N/A')})" if 'Change' in values else ""
                            #print(f"  ✓ {district}: {formatted_price}{change_str}")
                
                # Fill missing values for unset categories using fallbacks
                sales_fallback = extracted_results.get('Sri Lanka Overall House Sale price', {}).get('Average Price', None)
                rental_fallback = extracted_results.get('Sri Lanka Overall House Rental price', {}).get('Average Price', None)
                if not rental_fallback or rental_fallback == 'Insufficient data':
                    rental_fallback = extracted_results.get('Colombo House Rental price', {}).get('Average Price', None)
                land_fallback = extracted_results.get('Overall Residential Land price', {}).get('Average Price', None)
                
                # Parse fallback values
                if sales_fallback and sales_fallback != 'Insufficient data':
                    sales_fallback = parse_price_value(sales_fallback)
                if rental_fallback and rental_fallback != 'Insufficient data':
                    rental_fallback = parse_price_value(rental_fallback)
                if land_fallback and land_fallback != 'Insufficient data':
                    land_fallback = parse_price_value(land_fallback)
                
                # Fill any empty districts with fallback values
                for district in all_districts:
                    if district not in all_districts_data["sales"] and sales_fallback:
                        all_districts_data["sales"][district] = sales_fallback
                    if district not in all_districts_data["rentals"] and rental_fallback:
                        all_districts_data["rentals"][district] = rental_fallback
                    if district not in all_districts_data["lands"] and land_fallback:
                        all_districts_data["lands"][district] = land_fallback
            
            return all_districts_data
        
        except ValueError as e:
            print(f"Error: Unable to fetch {site}")
            return {}
        except requests.RequestException as e:
            print(f"Error: Request failed for {site}")
            return {}
        except Exception as e:
            print(f"Error: {str(e)}")
            return {}
'''
# Example usage
if __name__ == "__main__":
     #Option 1: Run with default targets (all provinces, all types)
     result = web_scraper()
     print("\n\n=== RETURNED DICTIONARY (Default Targets) ===")
     print(result)
    
     #Option 2: Run with custom district-type targets
     #3 Format: 'DistrictName Type' where Type is 'Sale', 'Rental', or 'Land'
     #Examples: 'Kandy Sale', 'Colombo Rental', 'Galle Land'

    
     result_custom = web_scraper()

     print(result_custom.get("sales", {}).get("kandy", "N/A"), "Kandy Sale Price")
     print(result_custom.get("lands", {}).get("colombo", "N/A"), "Colombo Land Price")
     print(result_custom.get("rentals", {}).get("galle", "N/A"), "Galle Rental Price")
     print(result_custom.get("sales", {}).get("national average", "N/A"), "National Average Sale Price")
     print(result_custom.get("rentals", {}).get("national average", "N/A"), "National Average Rental Price")
     print(result_custom.get("lands", {}).get("national average", "N/A"), "National Average Land Price")
    '''