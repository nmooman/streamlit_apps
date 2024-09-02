import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import tldextract
import whois
import time
import re
import io

def search_company(company_name):
    search_engines = [
        f"https://duckduckgo.com/html/?q={company_name}",
        f"https://www.bing.com/search?q={company_name}"
    ]
    
    for search_url in search_engines:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if "duckduckgo.com" in search_url:
            result = soup.find('a', class_='result__url')
        else:  # Bing
            result = soup.find('cite')
        
        if result:
            return result.text if "bing.com" in search_url else result['href']
    
    return None

def get_company_info(company_name):
    url = search_company(company_name)
    
    if not url:
        return None, None, None, None, None

    # Extract domain name
    extracted = tldextract.extract(url)
    domain = f"{extracted.domain}.{extracted.suffix}"

    # Perform WHOIS lookup
    try:
        domain_info = whois.whois(domain)
        address = domain_info.address
        country = domain_info.country
    except:
        address = "Address not found"
        country = "Country not found"

    # Fetch webpage content
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        page_response = requests.get(url, headers=headers, timeout=5)
        page_content = page_response.text
        
        # Try to extract address and country from webpage if not found in WHOIS
        if address == "Address not found" or country == "Country not found":
            page_soup = BeautifulSoup(page_content, 'html.parser')
            
            # Look for address in common patterns
            address_pattern = re.compile(r'\d{1,5}\s\w.*?\d{5}')
            address_match = address_pattern.search(page_content)
            if address_match:
                address = address_match.group()
            
            # Look for country
            country_pattern = re.compile(r'\b(?:United States|Canada|United Kingdom|Australia|Germany|France|Japan|China)\b')
            country_match = country_pattern.search(page_content)
            if country_match:
                country = country_match.group()
        
    except:
        page_content = "Unable to fetch webpage content"

    return url, domain, page_content[:500], address, country  # Limiting page content to first 500 characters

def process_companies(df):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for index, row in df.iterrows():
        company_name = row['Company Name']
        status_text.text(f"Processing: {company_name}")
        
        url, domain, webpage, address, country = get_company_info(company_name)
        
        results.append({
            "Company Name": company_name,
            "URL": url,
            "Domain Name": domain,
            "Webpage Preview": webpage,
            "Address": address,
            "Country": country
        })
        
        progress_bar.progress((index + 1) / len(df))
        time.sleep(1)  # To avoid overwhelming the services

    status_text.text("Processing complete!")
    return pd.DataFrame(results)

def main():
    st.title("Company Information Extractor")

    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        if 'Company Name' not in df.columns:
            st.error("The Excel file must have a 'Company Name' column.")
        else:
            if st.button("Process Companies"):
                results_df = process_companies(df)
                st.dataframe(results_df)
                
                # Provide a download button for the results
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    results_df.to_excel(writer, index=False)
                output.seek(0)
                st.download_button(
                    label="Download Results",
                    data=output,
                    file_name="company_info_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()