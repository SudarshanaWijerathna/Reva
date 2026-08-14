import os
import re
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Reva, an Intelligent Real Estate Virtual Assistant for the Sri Lankan property market.
Your mission is to guide users with property valuations, dynamic ML predictions, LSTM 5-quarter price forecasts, RL agent recommendations, and User Portfolio Management for Housing, Land, and Rental markets.

CRITICAL INSTRUCTIONS & RESPONSE FORMATS:

1. IF user wants to ADD a property to their portfolio (e.g. "add a property", "add my house", "I bought a house in Moratuwa", "add rental property", "add land to portfolio"):
   Extract any available details and respond EXACTLY in one of these single-line formats:
   - For Housing:
     [TRIGGER_ADD_HOUSING_FORM] | <Location> | <PurchasePrice> | <PurchaseDate> | <LandSizePerches> | <HouseSizeSqft> | <Floors> | <BuiltYear> | <Condition>
   - For Rental:
     [TRIGGER_ADD_RENTAL_FORM] | <Location> | <PurchasePrice> | <PurchaseDate> | <MonthlyRent> | <OccupancyStatus> | <LeaseStart> | <LeaseEnd> | <TenantType>
   - For Land:
     [TRIGGER_ADD_LAND_FORM] | <Location> | <PurchasePrice> | <PurchaseDate> | <LandSizePerches> | <ZoningType> | <RoadAccess>
   (Fill known fields or use "None" for unspecified fields)

2. IF user asks to VIEW or SHOW their portfolio / properties (e.g. "show my properties", "view my portfolio", "what properties do I have", "my portfolio"):
   Respond EXACTLY with: [TRIGGER_VIEW_PORTFOLIO]

3. IF user requests a HOUSE price prediction/valuation (e.g. "house price prediction", "estimate a house in Moratuwa with 3 bedrooms", "how much is my 4 room house in Colombo"):
   Extract any available details and respond EXACTLY in this single-line format:
   [TRIGGER_HOUSE_FORM] | <District> | <SubLocation> | <HouseSqft> | <LandPerches> | <Bedrooms> | <Bathrooms> | <QualityTier> | <RoadWidthFt> | <FacilitiesCSV> | <MissingFields>
   - District: Colombo, Gampaha, Kalutara (or "None")
   - SubLocation: Piliyandala, Talawatugoda, Malabe, Athurugiriya, Nugegoda, Kottawa, Homagama, Battaramulla, Dehiwala, Maharagama, Moratuwa, Negombo, Kadawatha, Ja-Ela, Wattala, Gampaha City, Kiribathgoda, Ragama, Panadura, Horana, Bandaragama, Kalutara City, Wadduwa, Matugama (or "None")
   - QualityTier: normal, semi_luxury, luxury (or "None")
   - FacilitiesCSV: comma-separated list from [water, electricity, main_road, carpet_road, private_lane, hot_water, solar_power, brand_new, fully_furnished, air_conditioned, cctv, garden, pantry, servant_room] (or "None")
   - MissingFields: short description of missing fields, or "None"

4. IF user requests a LAND price prediction/valuation (e.g. "land valuation", "estimate 15 perches in Maharagama", "land price"):
   Extract any available details and respond EXACTLY in this single-line format:
   [TRIGGER_LAND_FORM] | <District> | <LocationText> | <LandSizePerches> | <DistanceToTownM> | <UtilitiesCSV> | <MissingFields>
   - District: Colombo, Gampaha, Kandy, Galle (or "None")
   - UtilitiesCSV: comma-separated list from [Main road, Electricity, Clear deed, Water, Bank loan, Near town] (or "None")
   - MissingFields: short description of missing fields, or "None"

5. IF user requests a RENTAL price prediction (e.g. "rental price", "apartment rent in Colombo 5", "house for rent"):
   Extract any available details and respond EXACTLY in this single-line format:
   [TRIGGER_RENTAL_FORM] | <Location> | <District> | <PropertyType> | <Bedrooms> | <Bathrooms> | <FurnishingStatus> | <MissingFields>
   - Location: Colombo 5, Colombo 3, Colombo 2, Dehiwala, Nugegoda, Rajagiriya, Battaramulla (or town name / "None")
   - District: Colombo, Gampaha, Kalutara (or "None")
   - PropertyType: Apartment, House, Office space, Annex, Room, Building, Shop space, Warehouse, Villa (or "None")
   - FurnishingStatus: furnished, semi-furnished, unfurnished (or "None")
   - MissingFields: short description of missing fields, or "None"

6. IF user asks for a price trend graph / visualization:
   Reply EXACTLY with: [TRIGGER_GRAPH]

7. FOR PORTFOLIO QUESTIONS (e.g. "How much profit have I made?", "Which property is performing best?", "Should I sell my house?", "What is my total portfolio value?"):
   Use the injected USER REAL ESTATE PORTFOLIO context to give precise, calculated, and professional financial feedback. Reference exact asset locations, purchase prices, valuations, and profits.
"""



def _heuristic_pattern_matcher(
    text: str,
    memory_context: List[str] = None,
    last_prediction_context: Optional[str] = None,
    portfolio_context: Optional[str] = None,
) -> Optional[str]:
    low = text.lower()

    # 1. Check for VIEW PORTFOLIO request
    is_view_portfolio = any(p in low for p in [
        "view portfolio", "view my portfolio", "show portfolio", "show my portfolio", 
        "my portfolio", "my properties", "show my properties", "view my properties", 
        "list my properties", "what properties do i have", "my owned assets", "check my portfolio",
        "portfolio overview", "my real estate portfolio", "see my properties", "see my portfolio"
    ]) or (
        ("portfolio" in low or "properties" in low or "assets" in low) and
        any(w in low for w in ["show", "view", "list", "display", "see", "check", "overview"]) and
        not any(w in low for w in ["add", "register", "save", "predict", "estimate"])
    )

    if is_view_portfolio:
        return "[TRIGGER_VIEW_PORTFOLIO]"


    # 2. Check for ADD PROPERTY requests
    is_add_intent = any(w in low for w in ["add ", "register ", "save ", "i bought", "i own", "purchased", "new property"])
    
    if is_add_intent:
        # Check if rental
        if any(w in low for w in ["rental", "rent", "apartment", "annex"]):
            loc = "Colombo" if "colombo" in low else "Gampaha" if "gampaha" in low else "Moratuwa" if "moratuwa" in low else "Colombo"
            price_match = re.search(r'(?:lkr|rs\.?|price)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:m|million|lakh|lakhs)?', low)
            purchase_price = "None"
            return f"[TRIGGER_ADD_RENTAL_FORM] | {loc} | {purchase_price} | None | None | occupied | None | None | family"

        # Check if land
        if any(w in low for w in ["land", "plot", "bare land"]):
            loc = "Colombo" if "colombo" in low else "Gampaha" if "gampaha" in low else "Maharagama" if "maharagama" in low else "Colombo"
            perch_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:perch|perches|p)', low)
            size = perch_match.group(1) if perch_match else "10"
            return f"[TRIGGER_ADD_LAND_FORM] | {loc} | None | None | {size} | residential | Carpeted Road"

        # Otherwise default to housing
        if any(w in low for w in ["house", "housing", "villa", "property", "home", "building"]):
            loc = "Moratuwa" if "moratuwa" in low else "Colombo" if "colombo" in low else "Gampaha" if "gampaha" in low else "Colombo"
            sqft_match = re.search(r'(\d+)\s*(?:sqft|sq\s*ft)', low)
            sqft = sqft_match.group(1) if sqft_match else "1500"
            perch_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:perch|perches|p)', low)
            perches = perch_match.group(1) if perch_match else "10"
            return f"[TRIGGER_ADD_HOUSING_FORM] | {loc} | None | None | {perches} | {sqft} | 1 | 2023 | good"

    # 3. Check for questions about PORTFOLIO profit/performance
    is_portfolio_question = any(
        phrase in low for phrase in [
            "portfolio value", "portfolio profit", "how much profit", "total profit",
            "my assets", "my performance", "which property is performing", "which should i sell",
            "portfolio summary", "portfolio health", "how is my portfolio"
        ]
    )
    if is_portfolio_question and portfolio_context:
        return f"Here is an overview of your portfolio:\n\n{portfolio_context}\n\nAsk me anytime for specific predictions or recommendations on any of these assets!"

    # 4. Check for questions about prediction memory or follow-ups
    is_question_about_past = any(
        phrase in low for phrase in [
            "what was", "what were", "what did i", "previous", "earlier", 
            "why did", "why buy", "why sell", "why hold", "why this", 
            "explain", "tell me about the last", "last prediction", "last estimate"
        ]
    )

    if is_question_about_past:
        if last_prediction_context:
            return f"Here is the context from your recent prediction:\n\n{last_prediction_context}\n\nOur models generated this based on historical transaction indices, localized demand factors, and RL momentum signals."
        elif memory_context:
            return f"Here are your previous calculation records:\n\n" + "\n\n".join(memory_context)

    if any(w in low for w in ["graph", "chart", "trend", "visualiz"]):
        return "[TRIGGER_GRAPH]"


    # Check for House
    if any(w in low for w in ["house", "housing", "villa", "cottage", "bungalow", "sqft", "bedroom", "bed room"]):

        # Extract district
        district = "Colombo" if "colombo" in low else "Gampaha" if "gampaha" in low else "Kalutara" if "kalutara" in low else "None"
        
        # Sublocations
        sub_locs = [
            "Piliyandala", "Talawatugoda", "Malabe", "Athurugiriya", "Nugegoda", 
            "Kottawa", "Homagama", "Battaramulla", "Dehiwala", "Maharagama", 
            "Moratuwa", "Negombo", "Kadawatha", "Ja-Ela", "Wattala", 
            "Gampaha City", "Kiribathgoda", "Ragama", "Panadura", "Horana", 
            "Bandaragama", "Kalutara City", "Wadduwa", "Matugama"
        ]
        sub_location = "None"
        for s in sub_locs:
            if s.lower() in low:
                sub_location = s
                break

        # Sqft
        sqft_match = re.search(r'(\d+)\s*(?:sqft|sq\s*ft|square\s*feet)', low)
        sqft = sqft_match.group(1) if sqft_match else "None"

        # Perches
        perch_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:perch|perches|p)', low)
        perches = perch_match.group(1) if perch_match else "None"

        # Bedrooms
        bed_match = re.search(r'(\d+)\s*(?:bed|bedroom|br|rooms)', low)
        bedrooms = bed_match.group(1) if bed_match else "None"

        # Bathrooms
        bath_match = re.search(r'(\d+)\s*(?:bath|bathroom|ba)', low)
        bathrooms = bath_match.group(1) if bath_match else "None"

        # Quality tier
        tier = "luxury" if "luxury" in low else "semi_luxury" if "semi" in low else "normal"

        # Facilities
        facs = []
        if "water" in low: facs.append("water")
        if "electricity" in low or "power" in low: facs.append("electricity")
        if "main road" in low: facs.append("main_road")
        if "ac" in low or "a/c" in low or "air condition" in low: facs.append("air_conditioned")
        if "cctv" in low: facs.append("cctv")
        if "garden" in low: facs.append("garden")
        if "furnish" in low: facs.append("fully_furnished")
        fac_csv = ",".join(facs) if facs else "None"

        missing = []
        if sqft == "None": missing.append("House size")
        if bedrooms == "None": missing.append("Bedrooms")
        if district == "None": missing.append("District")
        missing_str = ", ".join(missing) if missing else "None"

        return f"[TRIGGER_HOUSE_FORM] | {district} | {sub_location} | {sqft} | {perches} | {bedrooms} | {bathrooms} | {tier} | None | {fac_csv} | {missing_str}"

    # Check for Rental
    if any(w in low for w in ["rent", "rental", "apartment", "lease", "monthly rent"]):
        district = "Colombo" if "colombo" in low else "Gampaha" if "gampaha" in low else "Kalutara" if "kalutara" in low else "None"
        
        # Location
        loc = "None"
        for candidate in ["Colombo 5", "Colombo 3", "Colombo 2", "Colombo 7", "Dehiwala", "Nugegoda", "Rajagiriya", "Battaramulla", "Moratuwa", "Mount Lavinia"]:
            if candidate.lower() in low:
                loc = candidate
                break

        # Property type
        p_type = "Apartment" if "apartment" in low or "flat" in low else "House" if "house" in low else "Office space" if "office" in low else "Apartment"
        
        # Furnishing
        furn = "furnished" if "furnish" in low and "unfurnish" not in low and "semi" not in low else "semi-furnished" if "semi" in low else "unfurnished" if "unfurnish" in low else "furnished"

        # Beds & Baths
        bed_match = re.search(r'(\d+)\s*(?:bed|bedroom|br)', low)
        beds = bed_match.group(1) if bed_match else "None"
        bath_match = re.search(r'(\d+)\s*(?:bath|bathroom|ba)', low)
        baths = bath_match.group(1) if bath_match else "None"

        missing = []
        if loc == "None": missing.append("Location")
        if beds == "None": missing.append("Bedrooms")
        missing_str = ", ".join(missing) if missing else "None"

        return f"[TRIGGER_RENTAL_FORM] | {loc} | {district} | {p_type} | {beds} | {baths} | {furn} | {missing_str}"

    # Check for Land
    if any(w in low for w in ["land", "plot", "bare land", "perch", "perches"]):
        district = "Colombo" if "colombo" in low else "Gampaha" if "gampaha" in low else "Kandy" if "kandy" in low else "Galle" if "galle" in low else "None"

        # Location text
        loc_text = "None"
        for candidate in ["Maharagama", "Piliyandala", "Homagama", "Kottawa", "Malabe", "Kiribathgoda", "Kadawatha", "Negombo", "Panadura", "Horana"]:
            if candidate.lower() in low:
                loc_text = candidate
                break

        perch_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:perch|perches|p)', low)
        size = perch_match.group(1) if perch_match else "None"

        dist_match = re.search(r'(\d+)\s*(?:m|meters|km)', low)
        dist = dist_match.group(1) if dist_match else "None"

        utils = []
        if "main road" in low: utils.append("Main road")
        if "electricity" in low: utils.append("Electricity")
        if "water" in low: utils.append("Water")
        if "deed" in low or "clear" in low: utils.append("Clear deed")
        if "bank" in low or "loan" in low: utils.append("Bank loan")
        if "town" in low: utils.append("Near town")
        util_csv = ", ".join(utils) if utils else "None"

        missing = []
        if size == "None": missing.append("Land size")
        if district == "None": missing.append("District")
        missing_str = ", ".join(missing) if missing else "None"

        return f"[TRIGGER_LAND_FORM] | {district} | {loc_text} | {size} | {dist} | {util_csv} | {missing_str}"

    return None


def generate_chat_reply(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    memory_context: List[str] = None,
    last_prediction_context: Optional[str] = None,
    portfolio_context: Optional[str] = None,
) -> str:
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()

    # Build context prompt
    context_blocks = []
    if portfolio_context:
        context_blocks.append("--- USER REAL ESTATE PORTFOLIO ---\n" + portfolio_context)

    if memory_context:
        context_blocks.append("--- PREVIOUS RELEVANT PREDICTIONS & MEMORY ---\n" + "\n".join(memory_context))

    if last_prediction_context:
        context_blocks.append("--- MOST RECENT PREDICTION IN THIS CHAT ---\n" + last_prediction_context)

    # Prepare chat history text
    history_text = ""
    if conversation_history:
        history_lines = []
        for msg in conversation_history[-6:]:
            role = "User" if msg.get("sender") == "user" else "Reva"
            history_lines.append(f"{role}: {msg.get('text', '')}")
        history_text = "\n".join(history_lines)

    prompt_parts = []
    if context_blocks:
        prompt_parts.append("\n\n".join(context_blocks))
    if history_text:
        prompt_parts.append(f"--- RECENT CONVERSATION HISTORY ---\n{history_text}")
    prompt_parts.append(f"User Question/Input: {user_message}")
    full_prompt = "\n\n".join(prompt_parts)

    if gemini_key:
        # 1. Try google.genai client
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=gemini_key)
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
            )
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
                config=config,
            )
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            logger.warning("Error with google.genai: %s", e)

        # 2. Try legacy google.generativeai
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=gemini_key)
            model = legacy_genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT,
            )
            res = model.generate_content(full_prompt)
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            logger.warning("Error with legacy google.generativeai: %s", e)

        # 3. Direct REST API fallback
        try:
            import requests
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"temperature": 0.2}
            }
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
        except Exception as e:
            logger.warning("Error with REST fallback: %s", e)

    # Heuristic pattern matcher fallback
    pattern_reply = _heuristic_pattern_matcher(
        user_message,
        memory_context=memory_context,
        last_prediction_context=last_prediction_context,
        portfolio_context=portfolio_context,
    )
    if pattern_reply:
        return pattern_reply


    return (
        "Hello! I am Rēva, your Intelligent Real Estate Assistant. "
        "You can ask me for a **House price prediction**, **Rental price valuation**, "

        "or **Land price estimation**, or request **Price trend graphs** and **RL investment recommendations**!"
    )
