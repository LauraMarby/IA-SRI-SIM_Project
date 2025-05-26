import requests
from bs4 import BeautifulSoup
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from utils.extract_robots import analyze_robots
from utils.write_to_json import write_to_json

target_url = "https://www.diffordsguide.com/"

robot_data, sitemaps = analyze_robots(target_url) 

visited_urls = set()

max_crawl = 4000

url_pattern = re.compile(r"^https://www\.diffordsguide\.com/cocktails/recipe/\d+/")
sitemap_pattern = re.compile(r"^https://www\.diffordsguide\.com/sitemap/cocktail\.xml")

# drinks_data = []

session = requests.Session()

@retry(
    stop=stop_after_attempt(4),  
    wait=wait_exponential(multiplier=5, min=4, max=5),  
)
def fetch_url(url):
    """
    Obtiene la url y devuelve el Response neecsario para BeautifulSoup 
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    response = session.get(url, headers=headers)
    response.raise_for_status()
    return response

def find_name(soup):
    """
    Encuentra el nombre del coctel en la pagina web
    """
    try:
        container1 = soup.find('div', class_='layout-container__body')
        container2 = container1.find('div', class_='legacy-strip legacy-strip--content legacy-strip--notch legacy-strip--cocktails')
        grid = container2.find('div', class_='grid-container')
        name = grid.find('h1', class_='legacy-strip__heading').text.strip()
        return name
    except Exception as e:
        return f"Ocurrió un error: {e}"

def find_glass(soup):
    """
    Encuentra el recipiente en el que se sirve el coctel en cuestión
    """
    try:
        serve_span = soup.find('span', string=lambda s: s and 'Serve in a' in s)

        if serve_span:
            serve_a = serve_span.find_next_sibling('a')
            glass = serve_a.text.strip() if serve_a else None
            # print(glass)
            return glass
        else:
            # print("No se encontró el recipiente.")
            return ''
    except Exception as e:
        return f"Ocurrió un error: {e}"
    
def find_ingredients(soup):
    """
    Encuentra los ingredientes necesarios para hacer el coctel
    """
    try:
        ingredients = []

        table = soup.find('table', class_='legacy-ingredients-table')
        tbody = table.find('tbody')

        for row in tbody.find_all('tr'):
            tds = row.find_all('td')
            if len(tds) >= 2:
                amount = ''.join(tds[0].stripped_strings)
                ingredient = tds[1].get_text(separator=" ", strip=True)

                ingredients.append(f"{amount} {ingredient}")
                # print(f"{amount} - {ingredient}")
        
        return ingredients
    except Exception as e:
        return f"Ocurrió un error: {e}"

def find_instructions(soup):
    """
    Encuentra las instrucciones para crear el coctel
    """
    try:
        instructions = []

        how_to_make = soup.find('h2', string="How to make:")
        instructions_list = how_to_make.find_next_sibling('ol')

        if instructions_list:
            for li in instructions_list.find_all('li'):
                parts = []
                for element in li.contents:
                    if element.name == 'a':
                        parts.append(element.get_text(separator=" ", strip=True))
                    elif isinstance(element, str):
                        parts.append(element.strip())
                    else:
                        parts.append(element.get_text(separator=" ", strip=True))

                instruction = ' '.join(parts)
                instruction = ' '.join(instruction.split())
                instructions.append(instruction)
        else:
            instructions_list = how_to_make.find_next_sibling('p')
            instructions.append(instructions_list.get_text(separator=" ", strip=True))

        # for i, instr in enumerate(instructions, 1):
        #     print(f"{i}. {instr}")

        return instructions
    except Exception as e:
        return f"Ocurrió un error: {e}"

def find_review(soup):
    """
    Encuentra el criterio que se tiene de este coctel
    """
    try:
        review_content = ''
        review = soup.find('h2', string="Review:")
        if review:
            review_content = review.find_next_sibling('p').get_text(separator=" ", strip=True)
        return review_content
    except Exception as e:
        return f"Ocurrió un error: {e}"

def find_history(soup):
    """
    Encuentra un breve resumen de la historia del coctel
    """
    try:
        history_content = ''
        history = soup.find('h2', string="History:")
        if history:
            history_content = history.find_next_sibling('p').get_text(separator=" ", strip=True)
        return history_content
    except Exception as e:
        return f"Ocurrió un error: {e}"

def find_nutrition(soup):
    """
    Encuentra los datos nutritivos del coctel
    """
    try:
        nutrition_content = ''
        nutrition = soup.find('h2', string="Nutrition:")
        if nutrition:
            nutrition_content = nutrition.find_next_sibling('p').get_text(separator=" ", strip=True)
        return nutrition_content
    except Exception as e:
        return f"Ocurrió un error: {e}"

def find_alcohol_content(soup):
    """
    Encuentra el contenido en alcohol del coctel
    """
    try:
        alcohol_contents=[]
        alcohol_content = soup.find('h2', class_='m-0', string="Alcohol content:")
        if alcohol_content:
            alcohol_content_container = alcohol_content.find_next_sibling('ul')
            for li in alcohol_content_container.find_all('li'):
                    parts = []
                    for element in li.contents:
                        parts.append(element.get_text(separator=" ", strip=True))
                    alcohol_contents.append(parts)

        return alcohol_contents
    except Exception as e:
        return f"Ocurrió un error: {e}"

def find_garnish(soup):
    """
    Encuentra con qué se decora el coctel
    """
    try:
        garnish_content = ''
        garnish = soup.find('span', string="Garnish:")
        if garnish:
            garnish_sibling = garnish.next_sibling
            garnish_content = garnish_sibling.strip() if garnish_sibling else None
        return garnish_content
    except Exception as e:
        return f"Ocurrió un error: {e}"

def crawler():
    """
    Evalúa las urls que nos ofrecen los sitemaps de robots.txt y extrae recetas de 2000 cocteles (sujeto a cambios-crawler inicial)
    """

    crawl_count = 0

    while(crawl_count < max_crawl):

        for sitemap in sitemaps:
            if crawl_count == max_crawl:
                break
            if not sitemap_pattern.search(sitemap):
                continue

            response_sitemap = fetch_url(sitemap)
            soup_sitemap = BeautifulSoup(response_sitemap.content, "xml")

            for url in soup_sitemap.find_all('url'):
                if crawl_count == max_crawl:
                    break

                current_url = url.find('loc').text

                if current_url in visited_urls:
                    continue

                visited_urls.add(current_url)

                print(f'Url: {current_url}')

                response = fetch_url(current_url)

                soup = BeautifulSoup(response.content, "html.parser")

                #scrapper
                if url_pattern.search(current_url):
                    data = {}
                    data['Url'] = current_url

                    data['Name'] = find_name(soup)
                    if isinstance(data['Name'], str) and data['Name'].startswith("Ocurrió un error:"):
                        continue

                    data['Glass'] = find_glass(soup)
                    if isinstance(data['Glass'], str) and data['Glass'].startswith("Ocurrió un error:"):
                        continue

                    data['Ingredients'] = find_ingredients(soup)
                    if isinstance(data['Ingredients'], str) and data['Ingredients'].startswith("Ocurrió un error:"):
                        continue

                    data['Instructions'] = find_instructions(soup)
                    if isinstance(data['Instructions'], str) and data['Instructions'].startswith("Ocurrió un error:"):
                        continue

                    data['Review'] = find_review(soup)
                    if isinstance(data['Review'], str) and data['Review'].startswith("Ocurrió un error:"):
                        continue

                    data['History'] = find_history(soup)
                    if isinstance(data['History'], str) and data['History'].startswith("Ocurrió un error:"):
                        continue

                    data['Nutrition'] = find_nutrition(soup)
                    if isinstance(data['Nutrition'], str) and data['Nutrition'].startswith("Ocurrió un error:"):
                        continue

                    data['Alcohol_Content'] = find_alcohol_content(soup)
                    if isinstance(data['Alcohol_Content'], str) and data['Alcohol_Content'].startswith("Ocurrió un error:"):
                        continue

                    data['Garnish'] = find_garnish(soup)
                    if isinstance(data['Garnish'], str) and data['Garnish'].startswith("Ocurrió un error:"):
                        continue
                    
                    # drinks_data.append(data)
                    write_to_json(data)
                    crawl_count+=1

    # return drinks_data
