from agents.base_agent import BaseAgent
from googlesearch import search
from utils.save_visited_urls import is_url_visited, save_url_visited_urls
from utils.write_to_json import write_to_json
from utils.initial_crawling_scrapping import fetch_url, find_alcohol_content, find_garnish, find_glass, find_history, find_ingredients, find_instructions, find_name, find_nutrition, find_review
from trafilatura import extract
from bs4 import BeautifulSoup
from embedding.embedder import embed_new_document
from pathlib import Path

class Crawler_Agent(BaseAgent):
    def __init__(self, name, system):
        super().__init__(name, system)
        
        self.DATA_DIR = "src/data/"

    def crawl_srap(self, message: str) -> str:
        """Realiza una búsqueda en google teniendo en cuenta la query del usuario y toma el contenido de la primera página que encuentra."""
        
        try:
            search_results = search(f"{message}, site:https://www.diffordsguide.com/cocktails/recipe/ OR site:https://www.liquor.com/recipes/ OR site:https://punchdrink.com/recipes/", advanced=True, unique=True, lang="en")
            if not search_results:
                return f"Error en la búsqueda. No se encontró resultados para: {message}."
            
            for search_result in search_results:
                if search_result.url != "" and not is_url_visited(search_result.url):
                    try:
                        response = fetch_url(search_result.url)
                    
                        soup = BeautifulSoup(response.content, "html.parser")

                        if 'diffordsguide.com' in search_result.url:
                            print("diffords")
                            content = {}
                            content['Url'] = search_result.url
                            content['Name'] = find_name(soup)
                            content['Glass'] = find_glass(soup)
                            content['Ingredients'] = find_ingredients(soup)
                            content['Instructions'] = find_instructions(soup)
                            content['Review'] = find_review(soup)
                            content['History'] = find_history(soup)
                            content['Nutrition'] = find_nutrition(soup)
                            content['Alcohol_Content'] = find_alcohol_content(soup)
                            content['Garnish'] = find_garnish(soup)
                        
                        else:
                            if 'liquor.com' in search_result.url:
                                name = soup.find('h1', class_='heading__title').text.strip()

                                data = extract(filecontent=str(soup))
                                if data is None:
                                    continue

                                content = {}
                                content["Url"] = search_result.url
                                content["Name"] = name
                                content["Recipe"] = data

                            elif 'punchdrink.com' in search_result.url:
                                name = soup.find('h1', class_='entry-title text-center').text.strip() 
                                recipe = soup.find('div', class_='save-recipe').text.strip()
                                intro = soup.find('div', class_='entry-content').text.strip()

                                content = {}
                                content["Url"] = search_result.url
                                content["Name"] = name
                                content["Intro"] = intro
                                content["Recipe"] = recipe

                        p = write_to_json(content)
                        save_url_visited_urls(search_result.url)
                        return p

                    except Exception as e:
                        print(f"Error al procesar {search_result.url}: {str(e)}")
                        continue

        except Exception as e:
            return f"Error en la búsqueda: {str(e)}"

    async def handle(self, message):
        result = self.crawl_srap(message["content"])

        if not result.startswith('Error en la búsqueda'):
            embed_new_document(Path(result))

        #mandar mensaje a alguien? devolver algo?
