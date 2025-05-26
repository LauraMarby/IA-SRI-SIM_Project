import re
import requests
from urllib.parse import urljoin

def parse_robots_txt(robots_content):
    """
    Parsea el contenido de robots.txt y extrae las directivas relevantes.
    
    Args:
        robots_content (str): Contenido del archivo robots.txt
        
    Returns:
        dict: Diccionario con las directivas encontradas
    """
    user_agents = {}
    current_ua = None
    sitemaps = []
    
    # Expresiones regulares para las directivas
    ua_pattern = re.compile(r'^User-agent:\s*(.*)$', re.IGNORECASE)
    disallow_pattern = re.compile(r'^Disallow:\s*(.*)$', re.IGNORECASE)
    allow_pattern = re.compile(r'^Allow:\s*(.*)$', re.IGNORECASE)
    crawl_delay_pattern = re.compile(r'^Crawl-delay:\s*(.*)$', re.IGNORECASE)
    request_rate_pattern = re.compile(r'^Request-rate:\s*(.*)$', re.IGNORECASE)
    sitemap_pattern = re.compile(r'^Sitemap:\s*(.*)$', re.IGNORECASE)
    
    for line in robots_content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Buscar Sitemap
        sitemap_match = sitemap_pattern.match(line)
        if sitemap_match:
            sitemap_url = sitemap_match.group(1).strip()
            if sitemap_url:
                sitemaps.append(sitemap_url)
            continue
        
        # Buscar User-agent
        ua_match = ua_pattern.match(line)
        if ua_match:
            current_ua = ua_match.group(1).strip()
            if current_ua not in user_agents:
                user_agents[current_ua] = {
                    'allowed': [],
                    'disallowed': [],
                    'crawl_delay': None,
                    'request_rate': None
                }
            continue
            
        # Solo procesar otras directivas si tenemos un User-agent definido
        if current_ua is None:
            continue
            
        # Buscar Disallow
        disallow_match = disallow_pattern.match(line)
        if disallow_match:
            path = disallow_match.group(1).strip()
            if path:  # Ignorar líneas Disallow vacías (que permiten todo)
                user_agents[current_ua]['disallowed'].append(path)
            continue
            
        # Buscar Allow
        allow_match = allow_pattern.match(line)
        if allow_match:
            path = allow_match.group(1).strip()
            if path:
                user_agents[current_ua]['allowed'].append(path)
            continue
            
        # Buscar Crawl-delay
        crawl_delay_match = crawl_delay_pattern.match(line)
        if crawl_delay_match:
            delay = crawl_delay_match.group(1).strip()
            try:
                user_agents[current_ua]['crawl_delay'] = float(delay)
            except ValueError:
                pass
            continue
            
        # Buscar Request-rate
        request_rate_match = request_rate_pattern.match(line)
        if request_rate_match:
            rate = request_rate_match.group(1).strip()
            user_agents[current_ua]['request_rate'] = rate
            continue
    
    return user_agents['*'], sitemaps

def analyze_robots(url):
    """
    Analiza el robots.txt de un sitio web y devuelve las directivas importantes.
    
    Args:
        url (str): URL del sitio web a analizar
        
    Returns:
        dict: Diccionario con las directivas encontradas
    """

    robots_url = urljoin(url, '/robots.txt')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(robots_url, headers=headers, timeout=10)
        response.raise_for_status()
        return parse_robots_txt(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener robots.txt: {e}")
        return None
    