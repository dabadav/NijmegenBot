from telegram import Bot
import asyncio
import requests
from bs4 import BeautifulSoup
from geopy.distance import geodesic

TOKEN="6331637997:AAFWO69jwduyTtox-7htClZP0PFKy1wIK4o"
CHAT_ID="510793962"
GEO_API='pk.71b6f8217a35c11611c8f45d07f69399'

reference_address = "Huygensgebouw, Heyendaalseweg, Nijmegen"

def get_location(address, api_key):
    # Encode the address for URL
    params = {
        'key': api_key,
        'q': address,
        'format': 'json'
    }

    # Send request to LocationIQ
    response = requests.get("https://us1.locationiq.com/v1/search.php", params=params)

    # Check if the response is successful
    if response.status_code == 200:
        data = response.json()[0]  # Take the first result
        return (float(data['lat']), float(data['lon']))
    else:
        return None

reference_location = get_location(reference_address, GEO_API)  # Replace with your reference address

def get_distance(location1, location2):
    # Calculate the distance
    if location1 and location2:
        distance = geodesic(location1, location2).kilometers

        # Average speeds (km/h)
        walking_speed = 4  # Average walking speed
        biking_speed = 12  # Average biking speed

        # Time estimation (hours)
        walking_time = (distance / walking_speed) * 60
        biking_time = (distance / biking_speed) * 60

        # Print results
        # print(f"{distance:.2f}km {walking_time:.0f}min {biking_time:.0f}min")
        return [distance, walking_time, biking_time]
    else:
        return 0

def get_property_details_nederwoon():
    url = 'https://nederwoon.nl/search?search_type=&type=&rooms=&completion=&sort=2&city=Nijmegen'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.select('div.location')
    properties = []
    
    for item in items:
        details = {}
        # Extracting address
        address = item.select_one('p.color-medium.fixed-lh').text.strip()
        details['address'] = address
        # Extracting link
        link_tag = item.select_one('a.see-page-button[href]')
        if link_tag:
            details['link'] = 'https://nederwoon.nl' + link_tag['href']
        # Extracting price
        price = item.select_one('p.heading-md.text-regular.color-primary').text.strip()
        details['price'] = price
        # Extracting other details like rooms, size, etc.
        details_list = item.select('ul > li')
        for detail in details_list:
            if 'Woonoppervlakte' in detail.text:
                details['surface'] = detail.text.replace('Woonoppervlakte', '').strip()
            elif 'kamer' in detail.text:
                details['rooms'] = detail.text.strip()
            # Add more details as required
        properties.append(details)

    return properties

def get_property_details_dolfijn():
    url = 'https://dolfijnwonen.nl/woningaanbod/huur?availability=1&moveunavailablelistingstothebottom=true&orderby=10&orderdescending=true'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.select('article.objectcontainer')
    properties = []
    
    for item in items:
        details = {}
        # Extracting address
        address = item.select_one('span.street').text.strip() + ', ' + item.select_one('span.location').text.strip()
        details['address'] = address
        # Extracting link
        link_tag = item.select_one('a.img-container[href]')
        if link_tag:
            details['link'] = 'https://dolfijnwonen.nl' + link_tag['href']  # Adjust base URL if needed
        # Extracting price
        price = item.select_one('span.obj_price').text.strip()
        price = price.replace('/mnd', '').strip()
        if 'incl.' in price:
        # Split the price string on 'incl.', strip spaces, and then join them back
            parts = price.split('incl.')
            price = ' incl.'.join(part.strip() for part in parts)
        details['price'] = price
        # Extracting other details like rooms, bedrooms, etc.
        details['rooms'] = item.select_one('span.object_rooms .number').text.strip()
        details['bedrooms'] = item.select_one('span.object_bed_rooms .number').text.strip()
        # details['bathrooms'] = item.select_one('span.object_bath_rooms .number').text.strip()
        details['surface'] = item.select_one('span.object_sqfeet .number').text.strip()

        property_location = get_location(details['address'], GEO_API)
        distances = get_distance(property_location, reference_location)
        
        if distances != 0:
            details['distance'] = distances
        
        properties.append(details)
    # Sorting properties by price in decreasing order
    properties = sorted(properties, key=lambda x: x['price'], reverse=False)

    return properties

def get_property_details_pararius():
    url = 'https://www.pararius.com/apartments/nijmegen'
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Selecting the listings
    listings = soup.select('section.listing-search-item--list.listing-search-item--for-rent')

    properties = []

    for listing in listings:
        details = {}

        # Extracting title as address
        title_element = listing.select_one('h2.listing-search-item__title a')
        if title_element:
            details['address'] = title_element.text.strip()
            # Extracting link directly from the title
            details['link'] = requests.compat.urljoin(url, title_element['href'])

        # Extracting price
        price_element = listing.select_one('div.listing-search-item__price')
        if price_element:
            details['price'] = price_element.text.strip()

        # Extracting surface
        surface_element = listing.select_one('li.illustrated-features__item--surface-area')
        if surface_element:
            details['surface'] = surface_element.text.strip()

        properties.append(details)

    # Assuming prices are of the form '€XXX per month' and we want to sort based on the numerical value
    properties = sorted(properties, key=lambda x: float(x['price'].replace('€', '').replace(' per month', '').replace(',', '').strip()) if 'price' in x else 0)

    return properties

def format_for_telegram(properties):
    messages = []

    for prop in properties:
        msg = []

        if 'link' in prop:
            msg.append(f"[{prop['address']}]({prop['link']})")

        if 'price' in prop:
            msg.append(f"Price: {prop['price']}")

        if 'surface' in prop:
            msg.append(f"Surface: {prop['surface']}")

        if 'bedrooms' in prop:
            msg.append(f"Bedrooms: {prop['bedrooms']}")

        if 'distance' in prop:
            msg.append(f"Distance: {prop['distance'][0]:.2f}km ({prop['distance'][1]:.0f}min, {prop['distance'][2]:.0f}min)")

        messages.append('\n'.join(msg))

    return '\n\n'.join(messages)

def send_telegram_message(message: str, chat_id: str, token: str):
    bot = Bot(token)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown'))

def main():
    details_dolfijn = format_for_telegram(get_property_details_dolfijn())
    details_pararius = format_for_telegram(get_property_details_pararius())
    details_nederwoon = format_for_telegram(get_property_details_nederwoon())
    send_telegram_message(details_dolfijn, CHAT_ID, TOKEN)
    send_telegram_message(details_pararius, CHAT_ID, TOKEN)
    send_telegram_message(details_nederwoon, CHAT_ID, TOKEN)

if __name__ == '__main__':
    main()
