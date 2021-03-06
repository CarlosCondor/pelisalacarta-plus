# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Conector para uploaded.to
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os

from core import scrapertools
from core import logger
from core import config

def test_video_exists( page_url ):
    logger.info("[uploadedto.py] test_video_exists(page_url='%s')" % page_url)
    
    real_url = page_url.replace("uploaded.to","uploaded.net")
    # Vídeo borrado: uploaded.to/file/q4rkg1rw -> Redirige a otra página uploaded.to/410/q4rkg1rw
    # Video erróneo: uploaded.to/file/q4rkg1rx -> Redirige a otra página uploaded.to/404
    location = scrapertools.get_header_from_response( url = real_url , header_to_get = "location")
    logger.info("location="+location)
    if location=="":
        return True,""
    elif "uploaded.net/410" in location:
        return False,"El archivo ya no está disponible<br/>en uploaded.to (ha sido borrado)"
    elif "uploaded.net/404" in location:
        return False,"El archivo no existe<br/>en uploaded.to (enlace no válido)"
    else:
        return True,""

def get_video_url( page_url , premium = False , user="" , password="", video_password="" ):
    logger.info("[uploadedto.py] get_video_url(page_url='%s')" % page_url)
    video_urls = []
    
    if premium:
        # Login para conseguir la cookie
        logger.info("[uploadedto.py] -------------------------------------------")
        logger.info("[uploadedto.py] login")
        logger.info("[uploadedto.py] -------------------------------------------")
        login_url = "http://uploaded.net/io/login"
        post = "id="+user+"&pw="+password
        headers = []
        headers.append( ["User-Agent","Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:10.0.1) Gecko/20100101 Firefox/10.0.1"] )
        headers.append( ["X-Requested-With","XMLHttpRequest"] )
        headers.append( ["X-Prototype-Version","1.6.1"] )
        headers.append( ["Referer","http://uploaded.to/"] )
        
        setcookie = scrapertools.get_header_from_response( login_url, post=post, headers=headers, header_to_get="set-cookie")
        logger.info("Cabecera set-cookie="+setcookie)

        logger.info("[uploadedto.py] -------------------------------------------")
        logger.info("[uploadedto.py] obtiene la url")
        logger.info("[uploadedto.py] -------------------------------------------")

        location = scrapertools.get_header_from_response( page_url , header_to_get = "location")
        logger.info("location="+location)
        #Set-Cookie3: auth=3315964ab4fac585fdd9d4228dc70264a1756ba; path="/"; domain=".uploaded.to"; path_spec; domain_dot; expires="2015-02-25 18:35:37Z"; version=0
        #Set-Cookie3: login="%26id%3D3315964%26pw%3Dde135af0befa087e897ee6bfa78f2511a1ed093f%26cks%3D854cca559368"; path="/"; domain=".uploaded.to"; path_spec; domain_dot; expires="2013-02-25 18:35:37Z"; version=0
        
        '''
        #cookie_data=config.get_cookie_data()
        #logger.info("cookie_data="+cookie_data)
        cookie_data = setcookie
        auth = scrapertools.get_match( cookie_data , 'auth=([a-z0-9]+)' )
        logger.info("auth="+auth)
        #%26id%3D7308170%26pw%3Df14c8daa489647d758a88474f509cd4277980f6b%26cks%3D204cffc6c96f
        login = scrapertools.get_match( cookie_data , 'login=([a-zA-Z0-9\%]+)' )
        logger.info("login="+login)
        
        headers.append([ "Cookie", 'login='+login+'; auth='+auth])
        temp_location = scrapertools.get_header_from_response( location , header_to_get = "location" , headers=headers)
        logger.info("temp_location="+temp_location)

        #location = location + "|Cookie="+urllib.quote('login='+login+'; auth='+auth)
        location = temp_location
        '''

        logger.info("[uploadedto.py] -------------------------------------------")
        logger.info("[uploadedto.py] obtiene el nombre del fichero")
        logger.info("[uploadedto.py] -------------------------------------------")
        try:
            #content-disposition=attachment; filename="El Hobbit CAM LATINO Barbie.avi"
            content_disposition = scrapertools.get_header_from_response( location , header_to_get = "content-disposition" , headers=headers)
            if content_disposition!="":
                filename = scrapertools.get_match(content_disposition,'filename="([^"]+)"')
                extension = filename[-4:]
        except:
            extension = ""
        
        '''
        temp_location = scrapertools.get_header_from_response( location , header_to_get = "location" , headers=headers)
        logger.info("temp_location="+temp_location)
        if temp_location!="":
            location = temp_location
        '''
        
        video_urls.append( [extension+" (Premium) [uploaded.to]" , location] )

    for video_url in video_urls:
        logger.info("[uploadedto.py] %s - %s" % (video_url[0],video_url[1]))

    return video_urls

# Encuentra vídeos del servidor en el texto pasado
def find_videos(data):
    encontrados = set()
    devuelve = []
    
    # http://uploaded.net/file/1haty8nt
    patronvideos  = '(uploaded.net/file/[a-zA-Z0-9]+)'
    logger.info("[uploadedto.py] find_videos #"+patronvideos+"#")
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[uploaded.to]"
        url = "http://"+match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'uploadedto' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)
            
    # http://uploaded.to/file/1haty8nt
    patronvideos  = 'uploaded.to(/file/[a-zA-Z0-9]+)'
    logger.info("[uploadedto.py] find_videos #"+patronvideos+"#")
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[uploaded.to]"
        url = "http://uploaded.net"+match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'uploadedto' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    # http://ul.to/file/y2y6nzep
    patronvideos  = 'ul.to(/file/[a-zA-Z0-9]+)'
    logger.info("[uploadedto.py] find_videos #"+patronvideos+"#")
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[uploaded.to]"
        url = "http://uploaded.net"+match
        if url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'uploadedto' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    #http://ul.to/mjphp9hl
    patronvideos  = '(ul.to/[a-zA-Z0-9]+)'
    logger.info("[uploadedto.py] find_videos #"+patronvideos+"#")
    matches = re.compile(patronvideos,re.DOTALL).findall(data)

    for match in matches:
        titulo = "[uploaded.to]"
        url = match.replace("ul.to/","http://uploaded.net/file/")
        if url!="http://uploaded.net/file/file" and url not in encontrados:
            logger.info("  url="+url)
            devuelve.append( [ titulo , url , 'uploadedto' ] )
            encontrados.add(url)
        else:
            logger.info("  url duplicada="+url)

    return devuelve

