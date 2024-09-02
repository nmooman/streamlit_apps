#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import tldextract

def get_company_info(company_name):
    # Search for the company using a search engine (in this case, using DuckDuckGo)
    search_url = f"https://duckduckgo.com/html/?q={company_name}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract the first search result URL
    result = soup.find('a', class_='result__url')
    if result:
        url = result['href']
    else:
        return None, None, None, None, None

    # Extract domain name
    domain = tldextract.extract(url).registered_domain

    # Fetch webpage content
    try:
        page_response = requests.get(url, headers=headers, timeout=5)
        page_content = page_response.text
    except:
        page_content = "Unable to fetch webpage content"

    # Extract address and country (this is a simplified approach and may not work for all websites)
    address = "Address not found"
    country = "Country not found"
    page_soup = BeautifulSoup(page_content, 'html.parser')
    address_candidates = page_soup.find_all(['p', 'div'], string=lambda text: 'address' in text.lower() if text else False)
    for candidate in address_candidates:
        address = candidate.text.strip()
        break

    country_candidates = page_soup.find_all(['p', 'div'], string=lambda text: 'country' in text.lower() if text else False)
    for candidate in country_candidates:
        country = candidate.text.strip()
        break

    return url, domain, page_content[:500], address, country  # Limiting page content to first 500 characters

def main():
    st.title("Company Information Extractor")

    company_name = st.text_input("Enter company name:")
    if st.button("Extract Information"):
        if company_name:
            with st.spinner("Extracting information..."):
                url, domain, webpage, address, country = get_company_info(company_name)
                
                if url:
                    data = {
                        "Company Name": [company_name],
                        "URL": [url],
                        "Domain Name": [domain],
                        "Webpage Preview": [webpage],
                        "Address": [address],
                        "Country": [country]
                    }
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                else:
                    st.error("Unable to find information for the given company name.")
        else:
            st.warning("Please enter a company name.")

if __name__ == "__main__":
    main()
