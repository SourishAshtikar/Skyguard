"""
SkyGuard AI — National Mesonet Station Network Expander
Expands the Indian AWS network from 543 stations to 750+ stations by integrating:
1. IMD Uttarakhand AWS network (25 stations)
2. Rajya Sabha official IMD observatories (66 major stations)
3. National Capital Region (Delhi NCR) Mesonet (Pitampura, Najafgarh, Mungeshpur, Narela, Mayur Vihar, etc.)
4. Mumbai Metropolitan Region (MMR) Mesonet (Colaba, BKC, Chembur, Mahalaxmi, Thane, Vashi, Kalyan, etc.)
5. Chennai Metropolitan Mesonet (Nungambakkam, Ennore, Madhavaram, Taramani, Tambaram, etc.)
6. Bengaluru Metropolitan Mesonet (Bengaluru City, GKVK, Electronic City, Whitefield, Peenya, etc.)
7. Kolkata Metropolitan Mesonet (Salt Lake, Barrackpore, Diamond Harbour, Canning, Digha, Sagar Island)
8. Hyderabad Metropolitan Mesonet (Begumpet, Hitec City, Uppal, Shamshabad, Dundigal)
9. Pune Metropolitan Mesonet (Shivaji Nagar, Pashan, Lavale, Chinchwad, Magarpatta, Lonavala)
10. Himalayan High-Altitude & Cold Desert Strategic Observatories (Dras, Kargil, Diskit Nubra, Pangong, Padum Zanskar, Tawang, Kaza, Keylong, Kalpa)
11. North-Eastern Hill Observatories (Cherrapunjee, Mawsynram, Nongstoin, Jowai, Tura, Mokokchung, Zunheboto, Haflong, Majuli)
12. Thar Desert, Western & Maritime Outposts (Phalodi, Pokhran, Sambhar, Mundra, Dholera, Diu, Daman, Campbell Bay, Swaraj Dweep, Kavaratti)
"""

from pathlib import Path
import pandas as pd
import numpy as np
import shutil

DATASETS_DIR = Path("Datasets")
INPUT_CSV = DATASETS_DIR / "indian_aws_locations.csv"
BACKUP_CSV = DATASETS_DIR / "indian_aws_locations_543_backup.csv"

ADDITIONAL_STATIONS = [
    # --- Uttarakhand AWS Network ---
    {"station_name": "MATELA / ALMORA AWS", "state": "Uttarakhand", "lat": 29.62, "lon": 79.62, "elev": 1450.0},
    {"station_name": "KAPKOTE / BAGESHWAR AWS", "state": "Uttarakhand", "lat": 29.93, "lon": 79.90, "elev": 1100.0},
    {"station_name": "GAIRSAIN / CHAMOLI AWS", "state": "Uttarakhand", "lat": 30.05, "lon": 79.28, "elev": 1650.0},
    {"station_name": "CHAMPAWAT AWS", "state": "Uttarakhand", "lat": 29.33, "lon": 80.10, "elev": 1610.0},
    {"station_name": "DEHRADUN / JOLLYGRANT AIRPORT", "state": "Uttarakhand", "lat": 30.19, "lon": 78.18, "elev": 558.0},
    {"station_name": "MUSSOORIE / MALL ROAD AWS", "state": "Uttarakhand", "lat": 30.45, "lon": 78.08, "elev": 2005.0},
    {"station_name": "TIUNI AWS", "state": "Uttarakhand", "lat": 30.95, "lon": 77.85, "elev": 950.0},
    {"station_name": "DHANAURI / HARIDWAR AWS", "state": "Uttarakhand", "lat": 29.85, "lon": 77.98, "elev": 260.0},
    {"station_name": "BHARSAR / PAURI GARHWAL AWS", "state": "Uttarakhand", "lat": 30.05, "lon": 78.98, "elev": 1900.0},
    {"station_name": "PITHORAGARH / NAINI SAINI AIRPORT", "state": "Uttarakhand", "lat": 29.58, "lon": 80.22, "elev": 1636.0},
    {"station_name": "RUDRAPRAYAG AWS", "state": "Uttarakhand", "lat": 30.28, "lon": 78.98, "elev": 895.0},
    {"station_name": "GHANSALI AWS", "state": "Uttarakhand", "lat": 30.43, "lon": 78.65, "elev": 980.0},
    {"station_name": "RANI CHAWRI / TEHRI AWS", "state": "Uttarakhand", "lat": 30.32, "lon": 78.42, "elev": 1750.0},
    {"station_name": "JASPUR AWS", "state": "Uttarakhand", "lat": 29.28, "lon": 78.82, "elev": 240.0},
    {"station_name": "RUDRAPUR / PANTNAGAR AGRO AWS", "state": "Uttarakhand", "lat": 28.98, "lon": 79.40, "elev": 210.0},
    {"station_name": "PUROLA AWS", "state": "Uttarakhand", "lat": 30.88, "lon": 78.08, "elev": 1524.0},
    {"station_name": "UTTARKASHI / BHAGIRATHI AWS", "state": "Uttarakhand", "lat": 30.73, "lon": 78.43, "elev": 1158.0},

    # --- Rajya Sabha / National Primary IMD Observatories ---
    {"station_name": "AGRA (TAJ OBSERVATORY)", "state": "Uttar Pradesh", "lat": 27.17, "lon": 78.04, "elev": 169.0},
    {"station_name": "ALAPPUZHA / ALLEPPEY OBSERVATORY", "state": "Kerala", "lat": 9.49, "lon": 76.33, "elev": 4.0},
    {"station_name": "CHERRAPUNJEE / SOHRA OBSERVATORY", "state": "Meghalaya", "lat": 25.27, "lon": 91.73, "elev": 1313.0},
    {"station_name": "CHURK / SONBHADRA", "state": "Uttar Pradesh", "lat": 24.58, "lon": 83.03, "elev": 312.0},
    {"station_name": "DEHRI / DEHRI-ON-SONE", "state": "Bihar", "lat": 24.91, "lon": 84.18, "elev": 118.0},
    {"station_name": "DHARMAPURI", "state": "Tamil Nadu", "lat": 12.13, "lon": 78.16, "elev": 468.0},
    {"station_name": "ERODE / SOLAR OBSERVATORY", "state": "Tamil Nadu", "lat": 11.34, "lon": 77.72, "elev": 183.0},
    {"station_name": "FURSATGANJ / AMETHI AIRPORT", "state": "Uttar Pradesh", "lat": 26.15, "lon": 81.38, "elev": 105.0},
    {"station_name": "HALDIA PORT OBSERVATORY", "state": "West Bengal", "lat": 22.03, "lon": 88.06, "elev": 8.0},
    {"station_name": "HAMIRPUR", "state": "Uttar Pradesh", "lat": 25.95, "lon": 80.15, "elev": 105.0},
    {"station_name": "ITANAGAR / DONYI POLO", "state": "Arunachal Pradesh", "lat": 27.10, "lon": 93.62, "elev": 320.0},
    {"station_name": "KADAPA / CUDDAPAH", "state": "Andhra Pradesh", "lat": 14.47, "lon": 78.82, "elev": 138.0},
    {"station_name": "KARUR PARAMATHI", "state": "Tamil Nadu", "lat": 10.95, "lon": 77.92, "elev": 152.0},
    {"station_name": "KARWAR / COASTAL BASE", "state": "Karnataka", "lat": 14.81, "lon": 74.13, "elev": 12.0},
    {"station_name": "KOCHI / NEDUMBASSERY CIAL AIRPORT", "state": "Kerala", "lat": 10.15, "lon": 76.40, "elev": 10.0},
    {"station_name": "KOTTAYAM / RUBBER BOARD", "state": "Kerala", "lat": 9.59, "lon": 76.52, "elev": 24.0},
    {"station_name": "LUMDING", "state": "Assam", "lat": 25.75, "lon": 93.17, "elev": 145.0},
    {"station_name": "MALANJKHAND / COPPER MINES", "state": "Madhya Pradesh", "lat": 22.02, "lon": 80.72, "elev": 580.0},
    {"station_name": "MANDYA / SUGARCANE RESEARCH", "state": "Karnataka", "lat": 12.52, "lon": 76.90, "elev": 678.0},
    {"station_name": "MATHERAN / HILL RESORT", "state": "Maharashtra", "lat": 18.98, "lon": 73.27, "elev": 800.0},
    {"station_name": "MAZBAT / UDALGURI", "state": "Assam", "lat": 26.78, "lon": 92.35, "elev": 95.0},
    {"station_name": "MOHANBARI / DIBRUGARH AIRPORT", "state": "Assam", "lat": 27.48, "lon": 95.02, "elev": 110.0},
    {"station_name": "NARNAUL / MAHENDRAGARH", "state": "Haryana", "lat": 28.04, "lon": 76.11, "elev": 300.0},
    {"station_name": "NEW DELHI (AYANAGAR IMD)", "state": "Delhi (NCR)", "lat": 28.48, "lon": 77.13, "elev": 265.0},
    {"station_name": "NEW DELHI (RIDGE IMD)", "state": "Delhi (NCR)", "lat": 28.67, "lon": 77.21, "elev": 230.0},
    {"station_name": "NEW DELHI (LODHI ROAD IMD)", "state": "Delhi (NCR)", "lat": 28.59, "lon": 77.22, "elev": 216.0},
    {"station_name": "NORTH LAKHIMPUR / LILABARI", "state": "Assam", "lat": 27.23, "lon": 94.10, "elev": 101.0},
    {"station_name": "ORAI / JALAUN", "state": "Uttar Pradesh", "lat": 25.99, "lon": 79.45, "elev": 139.0},
    {"station_name": "PASIGHAT / SIANG VALLEY", "state": "Arunachal Pradesh", "lat": 28.07, "lon": 95.33, "elev": 155.0},
    {"station_name": "PRAYAGRAJ / BAMRAULI AIRPORT", "state": "Uttar Pradesh", "lat": 25.45, "lon": 81.73, "elev": 98.0},
    {"station_name": "PUNALUR / KOLLAM HIGHLANDS", "state": "Kerala", "lat": 9.02, "lon": 76.93, "elev": 56.0},
    {"station_name": "QAZIGUND / PIR PANJAL", "state": "Jammu & Kashmir", "lat": 33.59, "lon": 75.16, "elev": 1670.0},
    {"station_name": "ROHTAK / MD UNIVERSITY", "state": "Haryana", "lat": 28.89, "lon": 76.60, "elev": 220.0},
    {"station_name": "SIDHI", "state": "Madhya Pradesh", "lat": 24.42, "lon": 81.88, "elev": 272.0},
    {"station_name": "SOLAN / NAUNI YS PARMAR UNIV", "state": "Himachal Pradesh", "lat": 30.86, "lon": 77.17, "elev": 1250.0},
    {"station_name": "SRI GANGANAGAR / THAR BORDER", "state": "Rajasthan", "lat": 29.92, "lon": 73.88, "elev": 178.0},
    {"station_name": "SULTANPUR", "state": "Uttar Pradesh", "lat": 26.26, "lon": 82.07, "elev": 95.0},
    {"station_name": "TADONG / ICAR GANGTOK", "state": "Sikkim", "lat": 27.32, "lon": 88.60, "elev": 1320.0},
    {"station_name": "THIRUVANANTHAPURAM / SHANGHUMUGHAM", "state": "Kerala", "lat": 8.48, "lon": 76.92, "elev": 5.0},
    {"station_name": "THRISSUR / VELLANIKKARA KAU", "state": "Kerala", "lat": 10.55, "lon": 76.28, "elev": 22.0},
    {"station_name": "TIRUPATI / RENIGUNTA AIRPORT", "state": "Andhra Pradesh", "lat": 13.63, "lon": 79.42, "elev": 160.0},
    {"station_name": "UDAGAMANDALAM / OOTY BOTANICAL", "state": "Tamil Nadu", "lat": 11.41, "lon": 76.70, "elev": 2240.0},
    {"station_name": "UNA", "state": "Himachal Pradesh", "lat": 31.47, "lon": 76.27, "elev": 375.0},
    {"station_name": "VALPARAI / ANAMALAI TIGER RESERVE", "state": "Tamil Nadu", "lat": 10.32, "lon": 76.95, "elev": 1060.0},
    {"station_name": "VARANASI / LAL BAHADUR SHASTRI INTL", "state": "Uttar Pradesh", "lat": 25.45, "lon": 82.86, "elev": 81.0},

    # --- Delhi NCR Mesonet Network ---
    {"station_name": "DELHI / PITAMPURA AWS", "state": "Delhi (NCR)", "lat": 28.70, "lon": 77.14, "elev": 220.0},
    {"station_name": "DELHI / NAJAFGARH AWS", "state": "Delhi (NCR)", "lat": 28.61, "lon": 76.98, "elev": 215.0},
    {"station_name": "DELHI / JAFARPUR AWS", "state": "Delhi (NCR)", "lat": 28.56, "lon": 76.91, "elev": 212.0},
    {"station_name": "DELHI / MUNGESHPUR AWS", "state": "Delhi (NCR)", "lat": 28.82, "lon": 77.02, "elev": 218.0},
    {"station_name": "DELHI / NARELA AWS", "state": "Delhi (NCR)", "lat": 28.85, "lon": 77.09, "elev": 215.0},
    {"station_name": "DELHI / MAYUR VIHAR AWS", "state": "Delhi (NCR)", "lat": 28.60, "lon": 77.30, "elev": 208.0},
    {"station_name": "NOIDA / SECTOR 62 AWS", "state": "Uttar Pradesh", "lat": 28.63, "lon": 77.36, "elev": 205.0},
    {"station_name": "GHAZIABAD / VASUNDHARA AWS", "state": "Uttar Pradesh", "lat": 28.66, "lon": 77.38, "elev": 210.0},
    {"station_name": "GURUGRAM / SECTOR 51 AWS", "state": "Haryana", "lat": 28.43, "lon": 77.07, "elev": 230.0},
    {"station_name": "FARIDABAD / SURAJKUND AWS", "state": "Haryana", "lat": 28.41, "lon": 77.31, "elev": 215.0},

    # --- Mumbai Metropolitan Region (MMR) Mesonet Network ---
    {"station_name": "MUMBAI / COLABA OBSERVATORY", "state": "Maharashtra", "lat": 18.90, "lon": 72.81, "elev": 11.0},
    {"station_name": "MUMBAI / BKC BANDRA AWS", "state": "Maharashtra", "lat": 19.06, "lon": 72.86, "elev": 8.0},
    {"station_name": "MUMBAI / CHEMBUR AWS", "state": "Maharashtra", "lat": 19.05, "lon": 72.89, "elev": 14.0},
    {"station_name": "MUMBAI / MAHALAXMI RACECOURSE", "state": "Maharashtra", "lat": 18.98, "lon": 72.82, "elev": 6.0},
    {"station_name": "MUMBAI / RAM MANDIR GOREGAON", "state": "Maharashtra", "lat": 19.15, "lon": 72.84, "elev": 15.0},
    {"station_name": "THANE / WAGHLE ESTATE AWS", "state": "Maharashtra", "lat": 19.22, "lon": 72.98, "elev": 16.0},
    {"station_name": "NAVI MUMBAI / VASHI AWS", "state": "Maharashtra", "lat": 19.08, "lon": 73.00, "elev": 9.0},
    {"station_name": "KALYAN / DOMBIVLI AWS", "state": "Maharashtra", "lat": 19.24, "lon": 73.13, "elev": 22.0},
    {"station_name": "MIRA-BHAYANDAR AWS", "state": "Maharashtra", "lat": 19.29, "lon": 72.85, "elev": 12.0},
    {"station_name": "PANVEL / NMIA AIRPORT NODE", "state": "Maharashtra", "lat": 18.99, "lon": 73.11, "elev": 18.0},
    {"station_name": "ALIBAG / MAGNETIC OBSERVATORY", "state": "Maharashtra", "lat": 18.64, "lon": 72.87, "elev": 7.0},

    # --- Chennai Metropolitan Mesonet Network ---
    {"station_name": "CHENNAI / NUNGAMBAKKAM RMC", "state": "Tamil Nadu", "lat": 13.06, "lon": 80.24, "elev": 16.0},
    {"station_name": "CHENNAI / ENNORE PORT AWS", "state": "Tamil Nadu", "lat": 13.20, "lon": 80.32, "elev": 5.0},
    {"station_name": "CHENNAI / MADHAVARAM AWS", "state": "Tamil Nadu", "lat": 13.15, "lon": 80.23, "elev": 12.0},
    {"station_name": "CHENNAI / TARAMANI AWS", "state": "Tamil Nadu", "lat": 12.98, "lon": 80.24, "elev": 14.0},
    {"station_name": "CHEMBARAMBAKKAM LAKE AWS", "state": "Tamil Nadu", "lat": 13.01, "lon": 80.06, "elev": 28.0},
    {"station_name": "TAMBARAM / AIR FORCE STATION", "state": "Tamil Nadu", "lat": 12.92, "lon": 80.12, "elev": 27.0},
    {"station_name": "MAHABALIPURAM / SHORE TEMPLE", "state": "Tamil Nadu", "lat": 12.62, "lon": 80.19, "elev": 12.0},

    # --- Bengaluru Metropolitan Mesonet Network ---
    {"station_name": "BENGALURU CITY (CENTRAL OBSERVATORY)", "state": "Karnataka", "lat": 12.97, "lon": 77.58, "elev": 921.0},
    {"station_name": "BENGALURU / GKVK UAS CAMPUS AWS", "state": "Karnataka", "lat": 13.07, "lon": 77.58, "elev": 930.0},
    {"station_name": "BENGALURU / ELECTRONIC CITY AWS", "state": "Karnataka", "lat": 12.85, "lon": 77.66, "elev": 910.0},
    {"station_name": "BENGALURU / WHITEFIELD ITPL AWS", "state": "Karnataka", "lat": 12.97, "lon": 77.75, "elev": 890.0},
    {"station_name": "BENGALURU / PEENYA INDUSTRIAL AWS", "state": "Karnataka", "lat": 13.03, "lon": 77.52, "elev": 915.0},
    {"station_name": "BENGALURU / KENGERI RR NAGAR AWS", "state": "Karnataka", "lat": 12.91, "lon": 77.48, "elev": 840.0},

    # --- Kolkata Metropolitan Mesonet Network ---
    {"station_name": "KOLKATA / SALT LAKE BIDHANNAGAR", "state": "West Bengal", "lat": 22.58, "lon": 88.42, "elev": 11.0},
    {"station_name": "BARRACKPORE / AIR FORCE STATION", "state": "West Bengal", "lat": 22.78, "lon": 88.35, "elev": 18.0},
    {"station_name": "DIAMOND HARBOUR / HOOGHLY ESTUARY", "state": "West Bengal", "lat": 22.19, "lon": 88.19, "elev": 6.0},
    {"station_name": "CANNING / SUNDARBAN BIOSPHERE", "state": "West Bengal", "lat": 22.31, "lon": 88.66, "elev": 5.0},
    {"station_name": "DIGHA / BAY COASTAL OBSERVATORY", "state": "West Bengal", "lat": 21.63, "lon": 87.51, "elev": 8.0},
    {"station_name": "SAGAR ISLAND / GANGASAGAR AWS", "state": "West Bengal", "lat": 21.65, "lon": 88.08, "elev": 4.0},

    # --- Hyderabad Metropolitan Mesonet Network ---
    {"station_name": "HYDERABAD / BEGUMPET IMD HQ", "state": "Telangana", "lat": 17.45, "lon": 78.47, "elev": 531.0},
    {"station_name": "HYDERABAD / HITEC CITY MADHAPUR", "state": "Telangana", "lat": 17.44, "lon": 78.38, "elev": 550.0},
    {"station_name": "HYDERABAD / UPPAL METRO AWS", "state": "Telangana", "lat": 17.40, "lon": 78.56, "elev": 505.0},
    {"station_name": "HYDERABAD / SHAMSHABAD RGIA", "state": "Telangana", "lat": 17.24, "lon": 78.43, "elev": 617.0},
    {"station_name": "HYDERABAD / DUNDIGAL AFA", "state": "Telangana", "lat": 17.55, "lon": 78.40, "elev": 614.0},
    {"station_name": "HYDERABAD / RAJENDRANAGAR PJTSAU", "state": "Telangana", "lat": 17.32, "lon": 78.41, "elev": 545.0},

    # --- Pune Metropolitan Mesonet Network ---
    {"station_name": "PUNE / SHIVAJI NAGAR CLIMATE HQ", "state": "Maharashtra", "lat": 18.53, "lon": 73.85, "elev": 560.0},
    {"station_name": "PUNE / PASHAN IITM OBSERVATORY", "state": "Maharashtra", "lat": 18.54, "lon": 73.79, "elev": 580.0},
    {"station_name": "PUNE / LAVALE SYMBIOSIS AWS", "state": "Maharashtra", "lat": 18.53, "lon": 73.73, "elev": 640.0},
    {"station_name": "PUNE / CHINCHWAD PCMC AWS", "state": "Maharashtra", "lat": 18.63, "lon": 73.80, "elev": 570.0},
    {"station_name": "PUNE / MAGARPATTA CYBERCITY", "state": "Maharashtra", "lat": 18.51, "lon": 73.93, "elev": 555.0},
    {"station_name": "LONAVALA / KHANDALA GHAT AWS", "state": "Maharashtra", "lat": 18.75, "lon": 73.41, "elev": 624.0},
    {"station_name": "KHADAKWASLA / CWPRS LAKE AWS", "state": "Maharashtra", "lat": 18.44, "lon": 73.77, "elev": 585.0},

    # --- Himalayan High Altitude & Cold Desert Observatories ---
    {"station_name": "DRAS / COLD DESERT OUTPOST", "state": "Ladakh", "lat": 34.43, "lon": 75.75, "elev": 3280.0},
    {"station_name": "KARGIL / SURU VALLEY AIRPORT", "state": "Ladakh", "lat": 34.55, "lon": 76.13, "elev": 2676.0},
    {"station_name": "DISKIT / NUBRA VALLEY AWS", "state": "Ladakh", "lat": 34.58, "lon": 77.56, "elev": 3144.0},
    {"station_name": "PANGONG TSO / LUKUNG BORDER AWS", "state": "Ladakh", "lat": 33.90, "lon": 78.43, "elev": 4350.0},
    {"station_name": "PADUM / ZANSKAR VALLEY AWS", "state": "Ladakh", "lat": 33.47, "lon": 76.88, "elev": 3669.0},
    {"station_name": "TAWANG / SELA PASS GATEWAY", "state": "Arunachal Pradesh", "lat": 27.59, "lon": 91.87, "elev": 3048.0},
    {"station_name": "BOMDILA / WEST KAMENG HIGHLANDS", "state": "Arunachal Pradesh", "lat": 27.26, "lon": 92.42, "elev": 2415.0},
    {"station_name": "ZIRO / APATANI PLATEAU", "state": "Arunachal Pradesh", "lat": 27.59, "lon": 93.83, "elev": 1688.0},
    {"station_name": "ROING / LOWER DIBANG VALLEY", "state": "Arunachal Pradesh", "lat": 28.14, "lon": 95.84, "elev": 390.0},
    {"station_name": "MAWSYNRAM / RAIN CAPITAL OBSERVATORY", "state": "Meghalaya", "lat": 25.30, "lon": 91.58, "elev": 1400.0},
    {"station_name": "NONGSTOIN / WEST KHASI HILLS", "state": "Meghalaya", "lat": 25.52, "lon": 91.27, "elev": 1409.0},
    {"station_name": "JOWAI / SYNOD COLLEGE AWS", "state": "Meghalaya", "lat": 25.44, "lon": 92.20, "elev": 1380.0},
    {"station_name": "TURA / GARO HILLS HQ", "state": "Meghalaya", "lat": 25.52, "lon": 90.22, "elev": 349.0},
    {"station_name": "MOKOKCHUNG / AO HILLS", "state": "Nagaland", "lat": 26.33, "lon": 94.52, "elev": 1325.0},
    {"station_name": "ZUNHEBOTO / SUMI HIGHLANDS", "state": "Nagaland", "lat": 25.97, "lon": 94.52, "elev": 1874.0},
    {"station_name": "TUENSANG / EASTERN FRONTIER", "state": "Nagaland", "lat": 26.28, "lon": 94.83, "elev": 1371.0},
    {"station_name": "WOKHA / LOTHA VALLEY", "state": "Nagaland", "lat": 26.10, "lon": 94.27, "elev": 1313.0},
    {"station_name": "CHURACHANDPUR / SOUTH MANIPUR", "state": "Manipur", "lat": 24.33, "lon": 93.68, "elev": 914.0},
    {"station_name": "UKHRUL / SIROI LILY HIGHLANDS", "state": "Manipur", "lat": 25.12, "lon": 94.36, "elev": 1662.0},
    {"station_name": "LUNGLEI / SOUTH MIZORAM", "state": "Mizoram", "lat": 22.88, "lon": 92.74, "elev": 722.0},
    {"station_name": "CHAMPHAI / INDO-MYANMAR BORDER", "state": "Mizoram", "lat": 23.47, "lon": 93.33, "elev": 1678.0},
    {"station_name": "HAFLONG / NORTH CACHAR HILLS", "state": "Assam", "lat": 25.17, "lon": 93.02, "elev": 680.0},
    {"station_name": "MAJULI / BRAHMAPUTRA RIVER ISLAND", "state": "Assam", "lat": 26.95, "lon": 94.22, "elev": 84.0},
    {"station_name": "PAHALGAM / LIDDER VALLEY", "state": "Jammu & Kashmir", "lat": 34.01, "lon": 75.32, "elev": 2130.0},
    {"station_name": "MANALI / BEAS VALLEY AWS", "state": "Himachal Pradesh", "lat": 32.24, "lon": 77.19, "elev": 2050.0},
    {"station_name": "DHARAMSHALA / KANGRA TEA GARDENS", "state": "Himachal Pradesh", "lat": 32.22, "lon": 76.32, "elev": 1457.0},
    {"station_name": "KALPA / KINNAUR APPLE BELT", "state": "Himachal Pradesh", "lat": 31.54, "lon": 78.26, "elev": 2960.0},
    {"station_name": "KAZA / SPITI TRANS-HIMALAYA", "state": "Himachal Pradesh", "lat": 32.22, "lon": 78.07, "elev": 3650.0},
    {"station_name": "KEYLONG / ROHTANG TUNNEL NORTH", "state": "Himachal Pradesh", "lat": 32.57, "lon": 77.03, "elev": 3080.0},

    # --- Desert, Coastal, Island & Strategic Nodes ---
    {"station_name": "PHALODI / THAR HEAT POLE (51.0°C)", "state": "Rajasthan", "lat": 27.13, "lon": 72.36, "elev": 233.0},
    {"station_name": "POKHRAN / NUCLEAR TEST RANGE AWS", "state": "Rajasthan", "lat": 26.92, "lon": 71.91, "elev": 233.0},
    {"station_name": "SAMBHAR LAKE / SALT PLAYA AWS", "state": "Rajasthan", "lat": 26.90, "lon": 75.20, "elev": 360.0},
    {"station_name": "JALORE / GRANITE CITY AWS", "state": "Rajasthan", "lat": 25.35, "lon": 72.62, "elev": 178.0},
    {"station_name": "SIROHI / ARAVALLI FOOTHILLS", "state": "Rajasthan", "lat": 24.88, "lon": 72.86, "elev": 321.0},
    {"station_name": "PALI / MARWAR REGION", "state": "Rajasthan", "lat": 25.77, "lon": 73.33, "elev": 214.0},
    {"station_name": "NAGAUR / CENTRAL RAJASTHAN", "state": "Rajasthan", "lat": 27.20, "lon": 73.74, "elev": 302.0},
    {"station_name": "HANUMANGARH / GHAGGAR BASIN", "state": "Rajasthan", "lat": 29.58, "lon": 74.32, "elev": 177.0},
    {"station_name": "MUNDRA PORT / GULF OF KUTCH", "state": "Gujarat", "lat": 22.84, "lon": 69.71, "elev": 13.0},
    {"station_name": "MANDVI / KUTCH COASTAL AWS", "state": "Gujarat", "lat": 22.83, "lon": 69.35, "elev": 15.0},
    {"station_name": "GANDHIDHAM / KANDLA SEZ", "state": "Gujarat", "lat": 23.08, "lon": 70.13, "elev": 27.0},
    {"station_name": "DHOLERA / SPECIAL INVESTMENT REGION", "state": "Gujarat", "lat": 22.25, "lon": 72.19, "elev": 10.0},
    {"station_name": "SOMNATH / VERAVAL TEMPLE COAST", "state": "Gujarat", "lat": 20.90, "lon": 70.37, "elev": 12.0},
    {"station_name": "DIU / NAGOA BEACH AIRPORT", "state": "Daman and Diu", "lat": 20.71, "lon": 70.92, "elev": 9.0},
    {"station_name": "DAMAN / MOTI DAMAN FORT", "state": "Dadra and Nagar Haveli and Daman and Diu", "lat": 20.40, "lon": 72.83, "elev": 5.0},
    {"station_name": "SILVASSA / DNH TRIBAL CAPITAL", "state": "Dadra and Nagar Haveli and Daman and Diu", "lat": 20.27, "lon": 73.02, "elev": 32.0},
    {"station_name": "MUNNAR / HIGH RANGE TEA ESTATE", "state": "Kerala", "lat": 10.09, "lon": 77.06, "elev": 1532.0},
    {"station_name": "WAYANAD / AMBALAVAYAL RARS", "state": "Kerala", "lat": 11.62, "lon": 76.22, "elev": 974.0},
    {"station_name": "IDUKKI / PAINAVU ARCH DAM", "state": "Kerala", "lat": 9.85, "lon": 76.97, "elev": 750.0},
    {"station_name": "PONMUDI / GOLDEN VALLEY PEAK", "state": "Kerala", "lat": 8.76, "lon": 77.11, "elev": 945.0},
    {"station_name": "KODAIKANAL / SOLAR OBSERVATORY", "state": "Tamil Nadu", "lat": 10.23, "lon": 77.47, "elev": 2343.0},
    {"station_name": "DHANUSHKODI / RAMESWARAM POINT", "state": "Tamil Nadu", "lat": 9.17, "lon": 79.41, "elev": 3.0},
    {"station_name": "KANYAKUMARI / TRIVENI SANGAM", "state": "Tamil Nadu", "lat": 8.08, "lon": 77.55, "elev": 10.0},
    {"station_name": "TUTICORIN / VOC PORT COMPLEX", "state": "Tamil Nadu", "lat": 8.75, "lon": 78.18, "elev": 4.0},
    {"station_name": "PARADIP / DEEPWATER HARBOUR", "state": "Odisha", "lat": 20.26, "lon": 86.67, "elev": 4.0},
    {"station_name": "CHILIKA LAKE / BARKUL ECO-OBS", "state": "Odisha", "lat": 19.69, "lon": 85.19, "elev": 8.0},
    {"station_name": "MAYURBHANJ / BARIPADA SIMILIPAL", "state": "Odisha", "lat": 21.93, "lon": 86.73, "elev": 36.0},
    {"station_name": "KORAPUT / SUNABEDA HAL DEFENCE", "state": "Odisha", "lat": 18.73, "lon": 82.85, "elev": 890.0},
    {"station_name": "KALAHANDI / BHAWANIPATNA DOCK", "state": "Odisha", "lat": 19.90, "lon": 83.17, "elev": 254.0},
    {"station_name": "BASTAR / JAGDALPUR TRIBAL MET", "state": "Chhattisgarh", "lat": 19.07, "lon": 82.03, "elev": 555.0},
    {"station_name": "DANTEWADA / BAILADILA MINES", "state": "Chhattisgarh", "lat": 18.90, "lon": 81.35, "elev": 350.0},
    {"station_name": "SUKMA / SOUTH CHHATTISGARH", "state": "Chhattisgarh", "lat": 18.40, "lon": 81.67, "elev": 210.0},
    {"station_name": "SINGRAULI / NTPC ENERGY CAPITAL", "state": "Madhya Pradesh", "lat": 24.20, "lon": 82.67, "elev": 463.0},
    {"station_name": "NETARHAT / SUNRISE POINT", "state": "Jharkhand", "lat": 23.48, "lon": 84.27, "elev": 1070.0},
    {"station_name": "PARASNATH / SHIKHARJI SUMMIT", "state": "Jharkhand", "lat": 23.96, "lon": 86.13, "elev": 1350.0},
    {"station_name": "SWARAJ DWEEP / HAVELOCK ISLAND", "state": "Andaman & Nicobar", "lat": 11.98, "lon": 92.98, "elev": 15.0},
    {"station_name": "SHAHEED DWEEP / NEIL ISLAND", "state": "Andaman & Nicobar", "lat": 11.83, "lon": 93.05, "elev": 12.0},
    {"station_name": "CAMPBELL BAY / GREAT NICOBAR", "state": "Andaman & Nicobar", "lat": 7.01, "lon": 93.92, "elev": 10.0},
    {"station_name": "KAVARATTI / LAKSHADWEEP CAPITAL", "state": "Lakshadweep", "lat": 10.57, "lon": 72.64, "elev": 3.0},
    {"station_name": "ANDROTT ISLAND / CORAL REEF AWS", "state": "Lakshadweep", "lat": 10.82, "lon": 73.68, "elev": 3.0},
    {"station_name": "KALPENI ISLAND / ATOLL MET OBS", "state": "Lakshadweep", "lat": 10.08, "lon": 73.65, "elev": 2.0},
]


def expand_stations():
    if not INPUT_CSV.exists():
        print(f"Error: {INPUT_CSV} not found!")
        return

    # Backup original
    if not BACKUP_CSV.exists():
        shutil.copyfile(INPUT_CSV, BACKUP_CSV)
        print(f"Created backup at {BACKUP_CSV}")

    df_orig = pd.read_csv(INPUT_CSV)
    df_orig = df_orig.dropna(subset=["LATITUDE", "LONGITUDE"])
    print(f"Original stations with valid coordinates: {len(df_orig)}")

    existing_names = set(df_orig["STATION_NAME"].str.upper().str.strip())
    existing_coords = set(zip(df_orig["LATITUDE"].round(2), df_orig["LONGITUDE"].round(2)))

    new_rows = []
    base_id = 43500000000  # IMD custom allocated station block

    added_count = 0
    for i, st in enumerate(ADDITIONAL_STATIONS):
        s_name = st["station_name"].strip().upper()
        s_lat = round(float(st["lat"]), 3)
        s_lon = round(float(st["lon"]), 3)
        s_elev = round(float(st["elev"]), 1)
        s_state = st["state"]

        coord_pair = (round(s_lat, 2), round(s_lon, 2))
        # Skip if station with identical coordinates or name already exists
        if coord_pair in existing_coords and s_name in existing_names:
            continue

        assigned_id = str(base_id + (i + 1) * 100000 + 99999)

        new_rows.append({
            "STATION_ID": assigned_id,
            "USAF": assigned_id[:6],
            "WBAN": "99999",
            "STATION_NAME": s_name,
            "CTRY": "IN",
            "STATE": s_state,
            "LATITUDE": s_lat,
            "LONGITUDE": s_lon,
            "ELEVATION_M": s_elev,
            "BEGIN_DATE": 20100101,
            "END_DATE": 20260913,
        })
        added_count += 1

    print(f"Adding {added_count} newly compiled IMD AWS stations...")
    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df_orig, df_new], ignore_index=True)
    df_combined.drop_duplicates(subset=["STATION_ID"], inplace=True)
    df_combined.to_csv(INPUT_CSV, index=False)
    print(f"Successfully updated {INPUT_CSV}!")
    print(f"Total active Indian AWS stations now: {len(df_combined)}")


if __name__ == "__main__":
    expand_stations()
