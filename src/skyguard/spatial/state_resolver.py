"""
SkyGuard AI — Indian AWS Station State & Subdivision Resolver
Maps Indian AWS stations to authentic States, Union Territories, or Meteorological Subdivisions
using city name dictionaries and geographic bounding boxes.
"""

from typing import Dict, Optional

KNOWN_STATION_MAP: Dict[str, str] = {
    # Delhi & NCR
    "DELHI": "Delhi (NCR)",
    "SAFDARJUNG": "Delhi (NCR)",
    "PALAM": "Delhi (NCR)",
    "AYANAGAR": "Delhi (NCR)",
    "RIDGE": "Delhi (NCR)",
    "LODHI": "Delhi (NCR)",

    # Maharashtra
    "MUMBAI": "Maharashtra",
    "BOMBAY": "Maharashtra",
    "SANTACRUZ": "Maharashtra",
    "COLABA": "Maharashtra",
    "PUNE": "Maharashtra",
    "NAGPUR": "Maharashtra",
    "AURANGABAD": "Maharashtra",
    "NASHIK": "Maharashtra",
    "NASIK": "Maharashtra",
    "AKOLA": "Maharashtra",
    "SOLAPUR": "Maharashtra",
    "SHOLAPUR": "Maharashtra",
    "AMRAOTI": "Maharashtra",
    "AMRAVATI": "Maharashtra",
    "AHMADNAGAR": "Maharashtra",
    "AHMEDNAGAR": "Maharashtra",
    "KOLHAPUR": "Maharashtra",
    "JALGAON": "Maharashtra",
    "RATNAGIRI": "Maharashtra",
    "MAHABALESHWAR": "Maharashtra",
    "DHANUSHKODI": "Tamil Nadu",
    "DABOLIM": "Goa",
    "MARMAGAO": "Goa",
    "PANJIM": "Goa",
    "GOA": "Goa",

    # Karnataka
    "BANGALORE": "Karnataka",
    "BENGALURU": "Karnataka",
    "HAL": "Karnataka",
    "KEMPEGOWDA": "Karnataka",
    "MANGALORE": "Karnataka",
    "MYSORE": "Karnataka",
    "BELGAUM": "Karnataka",
    "HUBLI": "Karnataka",
    "DHARWAD": "Karnataka",
    "GULBARGA": "Karnataka",
    "KALABURAGI": "Karnataka",
    "BELLARY": "Karnataka",
    "BALLARI": "Karnataka",
    "BIJAPUR": "Karnataka",
    "VIJAYAPURA": "Karnataka",
    "SHIMOGA": "Karnataka",
    "HASSAN": "Karnataka",
    "CHITRADURGA": "Karnataka",

    # Tamil Nadu & Puducherry
    "CHENNAI": "Tamil Nadu",
    "MEENAMBAKKAM": "Tamil Nadu",
    "MADRAS": "Tamil Nadu",
    "COIMBATORE": "Tamil Nadu",
    "MADURAI": "Tamil Nadu",
    "TIRUCHIRAPALLI": "Tamil Nadu",
    "TRICHY": "Tamil Nadu",
    "SALEM": "Tamil Nadu",
    "KODAIKANAL": "Tamil Nadu",
    "OOTY": "Tamil Nadu",
    "UDHAGAMANDALAM": "Tamil Nadu",
    "CUDDALORE": "Tamil Nadu",
    "NAGAPATTINAM": "Tamil Nadu",
    "ATIRAMAPATTINAM": "Tamil Nadu",
    "TUTICORIN": "Tamil Nadu",
    "THOOTHUKUDI": "Tamil Nadu",
    "KANYAKUMARI": "Tamil Nadu",
    "PUDUCHERRY": "Puducherry",
    "PONDICHERRY": "Puducherry",
    "KARAIKAL": "Puducherry",

    # West Bengal
    "KOLKATA": "West Bengal",
    "CALCUTTA": "West Bengal",
    "ALIPORE": "West Bengal",
    "DUM DUM": "West Bengal",
    "BAGDOGRA": "West Bengal",
    "DARJEELING": "West Bengal",
    "ASANSOL": "West Bengal",
    "SILIGURI": "West Bengal",
    "BAGATI": "West Bengal",
    "BALURGHAT": "West Bengal",
    "BANKURA": "West Bengal",
    "BERHAMPORE": "West Bengal",
    "CANNING": "West Bengal",
    "COOCH BEHAR": "West Bengal",
    "JALPAIGURI": "West Bengal",
    "MALDA": "West Bengal",
    "MIDNAPORE": "West Bengal",
    "SHANTINIKETAN": "West Bengal",
    "DIGHA": "West Bengal",

    # Telangana
    "HYDERABAD": "Telangana",
    "BEGUMPET": "Telangana",
    "HAKIMPET": "Telangana",
    "ADILABAD": "Telangana",
    "NIZAMABAD": "Telangana",
    "WARANGAL": "Telangana",
    "RAMAGUNDAM": "Telangana",
    "KHAMMAM": "Telangana",
    "MEDAK": "Telangana",
    "MAHABUBNAGAR": "Telangana",

    # Gujarat
    "AHMEDABAD": "Gujarat",
    "SURAT": "Gujarat",
    "VADODARA": "Gujarat",
    "BARODA": "Gujarat",
    "RAJKOT": "Gujarat",
    "BHAVNAGAR": "Gujarat",
    "BHUJ": "Gujarat",
    "KANDLA": "Gujarat",
    "AMRELI": "Gujarat",
    "PORBANDAR": "Gujarat",
    "VERAVAL": "Gujarat",
    "DEESA": "Gujarat",
    "VALSAD": "Gujarat",
    "DWARKA": "Gujarat",
    "OKHA": "Gujarat",

    # Rajasthan
    "JAIPUR": "Rajasthan",
    "JODHPUR": "Rajasthan",
    "UDAIPUR": "Rajasthan",
    "BIKANER": "Rajasthan",
    "AJMER": "Rajasthan",
    "KOTA": "Rajasthan",
    "JAISALMER": "Rajasthan",
    "ALWAR": "Rajasthan",
    "BARMER": "Rajasthan",
    "CHURU": "Rajasthan",
    "GANGANAGAR": "Rajasthan",
    "SRI GANGANAGAR": "Rajasthan",
    "PILANI": "Rajasthan",
    "MOUNT ABU": "Rajasthan",
    "BHILWARA": "Rajasthan",
    "DUNGARPUR": "Rajasthan",

    # Uttar Pradesh
    "LUCKNOW": "Uttar Pradesh",
    "KANPUR": "Uttar Pradesh",
    "VARANASI": "Uttar Pradesh",
    "BENARES": "Uttar Pradesh",
    "AGRA": "Uttar Pradesh",
    "ALLAHABAD": "Uttar Pradesh",
    "PRAYAGRAJ": "Uttar Pradesh",
    "MEERUT": "Uttar Pradesh",
    "BAREILLY": "Uttar Pradesh",
    "GORAKHPUR": "Uttar Pradesh",
    "ALIGARH": "Uttar Pradesh",
    "JHANSI": "Uttar Pradesh",
    "AYODHA": "Uttar Pradesh",
    "AYODHYA": "Uttar Pradesh",
    "FAIZABAD": "Uttar Pradesh",
    "BAHRAICH": "Uttar Pradesh",
    "BANDA": "Uttar Pradesh",
    "HARDOI": "Uttar Pradesh",
    "MORADABAD": "Uttar Pradesh",
    "MUZAFFARNAGAR": "Uttar Pradesh",
    "NAJIBABAD": "Uttar Pradesh",
    "ORAI": "Uttar Pradesh",
    "SULTANPUR": "Uttar Pradesh",

    # Madhya Pradesh
    "BHOPAL": "Madhya Pradesh",
    "INDORE": "Madhya Pradesh",
    "GWALIOR": "Madhya Pradesh",
    "JABALPUR": "Madhya Pradesh",
    "UJJAIN": "Madhya Pradesh",
    "SATNA": "Madhya Pradesh",
    "REWA": "Madhya Pradesh",
    "KHAJURAHO": "Madhya Pradesh",
    "SAGAR": "Madhya Pradesh",
    "GUNA": "Madhya Pradesh",
    "HOSHANGABAD": "Madhya Pradesh",
    "NARMADAPURAM": "Madhya Pradesh",
    "KHANDWA": "Madhya Pradesh",
    "KHARGONE": "Madhya Pradesh",
    "RATLAM": "Madhya Pradesh",
    "SEHORE": "Madhya Pradesh",
    "BETUL": "Madhya Pradesh",
    "CHHINDWARA": "Madhya Pradesh",
    "MANDLA": "Madhya Pradesh",
    "SHEOPUR": "Madhya Pradesh",

    # Bihar
    "PATNA": "Bihar",
    "GAYA": "Bihar",
    "BHAGALPUR": "Bihar",
    "MUZAFFARPUR": "Bihar",
    "PURNEA": "Bihar",
    "PURNAEA": "Bihar",
    "DARBHANGA": "Bihar",
    "CHHAPRA": "Bihar",
    "MOTIHARI": "Bihar",
    "SUPAUL": "Bihar",

    # Jharkhand
    "RANCHI": "Jharkhand",
    "JAMSHEDPUR": "Jharkhand",
    "DHANBAD": "Jharkhand",
    "BOKARO": "Jharkhand",
    "DEOGHAR": "Jharkhand",
    "DALTONGANJ": "Jharkhand",
    "MEDININAGAR": "Jharkhand",
    "HAZARIBAGH": "Jharkhand",

    # Odisha
    "BHUBANESWAR": "Odisha",
    "CUTTACK": "Odisha",
    "PURI": "Odisha",
    "BALASORE": "Odisha",
    "ROURKELA": "Odisha",
    "GOPALPUR": "Odisha",
    "CHANDBALI": "Odisha",
    "ANGUL": "Odisha",
    "SAMBALPUR": "Odisha",
    "JHARSUGUDA": "Odisha",
    "KORAPUT": "Odisha",
    "BHAWANIPATNA": "Odisha",
    "KEONJHARGARH": "Odisha",
    "PARADEEP": "Odisha",

    # Chhattisgarh
    "RAIPUR": "Chhattisgarh",
    "BILASPUR": "Chhattisgarh",
    "JAGDALPUR": "Chhattisgarh",
    "AMBIKAPUR": "Chhattisgarh",
    "DURG": "Chhattisgarh",
    "PENDRA": "Chhattisgarh",

    # Kerala
    "KOCHI": "Kerala",
    "COCHIN": "Kerala",
    "THIRUVANANTHAPURAM": "Kerala",
    "TRIVANDRUM": "Kerala",
    "KOZHIKODE": "Kerala",
    "CALICUT": "Kerala",
    "KANNUR": "Kerala",
    "PALAKKAD": "Kerala",
    "ALAPPUZHA": "Kerala",
    "ALLEPPEY": "Kerala",
    "KOTTAYAM": "Kerala",
    "PUNALUR": "Kerala",
    "VELLANIKKARA": "Kerala",

    # Andhra Pradesh
    "VISAKHAPATNAM": "Andhra Pradesh",
    "VIZAG": "Andhra Pradesh",
    "VIJAYAWADA": "Andhra Pradesh",
    "TIRUPATI": "Andhra Pradesh",
    "RAJAHMUNDRY": "Andhra Pradesh",
    "KURNOOL": "Andhra Pradesh",
    "ANANTAPUR": "Andhra Pradesh",
    "KADAPA": "Andhra Pradesh",
    "NELLORE": "Andhra Pradesh",
    "AROGYAVARAM": "Andhra Pradesh",
    "MACHILIPATNAM": "Andhra Pradesh",
    "BAPATLA": "Andhra Pradesh",
    "ONGOLE": "Andhra Pradesh",
    "KAKINADA": "Andhra Pradesh",

    # Jammu & Kashmir and Ladakh
    "SRINAGAR": "Jammu & Kashmir",
    "JAMMU": "Jammu & Kashmir",
    "BANIHAL": "Jammu & Kashmir",
    "BATOTE": "Jammu & Kashmir",
    "GULMARG": "Jammu & Kashmir",
    "PAHALGAM": "Jammu & Kashmir",
    "QAZIGUND": "Jammu & Kashmir",
    "KUPWARA": "Jammu & Kashmir",
    "KOKERNAG": "Jammu & Kashmir",
    "LEH": "Ladakh",
    "KARGIL": "Ladakh",
    "THOISE": "Ladakh",

    # Himachal Pradesh
    "SHIMLA": "Himachal Pradesh",
    "DHARAMSHALA": "Himachal Pradesh",
    "DHARAMSALA": "Himachal Pradesh",
    "MANALI": "Himachal Pradesh",
    "KULLU": "Himachal Pradesh",
    "BHUNTAR": "Himachal Pradesh",
    "SUNDERNAGAR": "Himachal Pradesh",
    "KALPA": "Himachal Pradesh",
    "SOLAN": "Himachal Pradesh",

    # Uttarakhand
    "DEHRADUN": "Uttarakhand",
    "PANTNAGAR": "Uttarakhand",
    "MUKTESHWAR": "Uttarakhand",
    "TEHRI": "Uttarakhand",
    "JOSHIMATH": "Uttarakhand",
    "ROORKEE": "Uttarakhand",

    # Punjab & Haryana & Chandigarh
    "AMRITSAR": "Punjab",
    "LUDHIANA": "Punjab",
    "PATIALA": "Punjab",
    "PATHANKOT": "Punjab",
    "BATHINDA": "Punjab",
    "AMBALA": "Haryana",
    "HISAR": "Haryana",
    "KARNAL": "Haryana",
    "ROHTAK": "Haryana",
    "GURUGRAM": "Haryana",
    "GURGAON": "Haryana",
    "CHANDIGARH": "Chandigarh",

    # North East
    "GUWAHATI": "Assam",
    "DIBRUGARH": "Assam",
    "SILCHAR": "Assam",
    "TEZPUR": "Assam",
    "JORHAT": "Assam",
    "NORTH LAKHIMPUR": "Assam",
    "DHUBRI": "Assam",
    "SHILLONG": "Meghalaya",
    "CHERAPUNJI": "Meghalaya",
    "SOHRA": "Meghalaya",
    "AGARTALA": "Tripura",
    "KAILASHAHAR": "Tripura",
    "IMPHAL": "Manipur",
    "AIZAWL": "Mizoram",
    "KOHIMA": "Nagaland",
    "DIMAPUR": "Nagaland",
    "ITANAGAR": "Arunachal Pradesh",
    "PASIGHAT": "Arunachal Pradesh",
    "GANGTOK": "Sikkim",

    # Island Territories
    "PORT BLAIR": "Andaman & Nicobar",
    "CAR NICOBAR": "Andaman & Nicobar",
    "HUT BAY": "Andaman & Nicobar",
    "MAYA BANDAR": "Andaman & Nicobar",
    "NANCOWRY": "Andaman & Nicobar",
    "AGATTI": "Lakshadweep",
    "AMINI": "Lakshadweep",
    "MINICOY": "Lakshadweep",
}


import re

def resolve_station_state(station_name: str, latitude: float, longitude: float) -> str:
    """
    Resolves the authentic Indian State, Union Territory, or Meteorological Subdivision
    for a given AWS station name and geographic coordinates.
    """
    name_upper = (station_name or "").upper()

    # 1. Direct dictionary match with word boundary on known Indian city/observatory names
    for key, state_name in KNOWN_STATION_MAP.items():
        if re.search(r'\b' + re.escape(key) + r'\b', name_upper):
            return state_name

    # 2. High-confidence coordinate regional bounding fallback
    if latitude >= 33.0:
        return "Jammu & Kashmir / Ladakh"
    elif latitude >= 30.5:
        if longitude < 76.5:
            return "Punjab"
        elif longitude < 77.8:
            return "Himachal Pradesh"
        else:
            return "Uttarakhand"
    elif latitude >= 28.0:
        if longitude < 74.0:
            return "Rajasthan"
        elif longitude < 77.0:
            return "Haryana"
        elif longitude < 77.5:
            return "Delhi (NCR)"
        elif longitude < 84.5:
            return "Uttar Pradesh"
        else:
            return "Bihar / North East"
    elif latitude >= 24.0:
        if longitude < 74.0:
            return "Rajasthan"
        elif longitude < 82.0:
            return "Madhya Pradesh"
        elif longitude < 85.0:
            return "Uttar Pradesh"
        elif longitude < 88.5:
            return "Jharkhand"
        else:
            return "Assam / North East"
    elif latitude >= 20.0:
        if longitude < 74.0:
            return "Gujarat"
        elif longitude < 81.0:
            return "Maharashtra"
        elif longitude < 84.0:
            return "Chhattisgarh"
        elif longitude < 87.5:
            return "Odisha"
        else:
            return "West Bengal"
    elif latitude >= 15.0:
        if longitude < 74.5:
            return "Goa / Konkan"
        elif longitude < 78.5:
            return "Maharashtra"
        elif longitude < 81.5:
            return "Telangana"
        else:
            return "Andhra Pradesh"
    elif latitude >= 12.0:
        if longitude < 76.0:
            return "Karnataka"
        elif longitude < 78.5:
            return "Karnataka"
        elif longitude < 80.5:
            return "Tamil Nadu"
        else:
            return "Bay of Bengal Region"
    elif latitude >= 8.0:
        if longitude < 77.0:
            return "Kerala"
        elif longitude < 80.5:
            return "Tamil Nadu"
        elif longitude > 91.0:
            return "Andaman & Nicobar"
        else:
            return "Tamil Nadu"

    return "National Mesonet"
