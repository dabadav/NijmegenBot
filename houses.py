from telegram import Bot
import asyncio
import requests
from bs4 import BeautifulSoup

TOKEN="6331637997:AAFWO69jwduyTtox-7htClZP0PFKy1wIK4o"
CHAT_ID="510793962"

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

        messages.append('\n'.join(msg))

    return '\n\n'.join(messages)

def send_telegram_message(message: str, chat_id: str, token: str):
    bot = Bot(token)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown'))

def main():
    details_dolfijn = format_for_telegram(get_property_details_dolfijn())
    details_pararius = format_for_telegram(get_property_details_pararius())
    send_telegram_message(details_dolfijn, CHAT_ID, TOKEN)
    send_telegram_message(details_pararius, CHAT_ID, TOKEN)

if __name__ == '__main__':
    main()