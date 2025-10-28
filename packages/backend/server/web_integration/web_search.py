import requests
import json
import os
import time
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
from newspaper import Article
from datetime import datetime
import hashlib

class WebSearchEngine:
    """Class for web search and content extraction"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("SERPAPI_KEY")
        self.search_history = []
        self.cached_results = {}
        self.cache_duration = 3600  # Cache results for 1 hour
    
    def search(self, query, num_results=5, search_type="web"):
        """
        Search the web for a query
        
        Args:
            query (str): Search query
            num_results (int): Number of results to return
            search_type (str): Type of search (web, news, images)
            
        Returns:
            dict: Search results
        """
        # Check cache first
        cache_key = f"{query}_{num_results}_{search_type}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        if cache_hash in self.cached_results:
            cached_item = self.cached_results[cache_hash]
            # Check if cache is still valid
            if time.time() - cached_item["timestamp"] < self.cache_duration:
                return cached_item["results"]
        
        # If SerpAPI key is available, use it
        if self.api_key:
            results = self._search_serpapi(query, num_results, search_type)
        else:
            # Fallback to direct requests
            results = self._search_direct(query, num_results, search_type)
        
        # Add to search history
        self.search_history.append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "num_results": len(results.get("results", [])),
            "search_type": search_type
        })
        
        # Cache results
        self.cached_results[cache_hash] = {
            "results": results,
            "timestamp": time.time()
        }
        
        return results
    
    def _search_serpapi(self, query, num_results=5, search_type="web"):
        """Search using SerpAPI"""
        try:
            # Set up the API endpoint and parameters
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results
            }
            
            # Add parameters based on search type
            if search_type == "news":
                params["tbm"] = "nws"
            elif search_type == "images":
                params["tbm"] = "isch"
            
            # Make the request
            response = requests.get(url, params=params)
            data = response.json()
            
            # Format results
            results = {"query": query, "results": []}
            
            if search_type == "web" or search_type == "news":
                # Extract organic results
                organic_results = data.get("organic_results", [])
                
                for result in organic_results[:num_results]:
                    results["results"].append({
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "source": result.get("source", ""),
                        "position": result.get("position", 0)
                    })
            elif search_type == "images":
                # Extract image results
                image_results = data.get("images_results", [])
                
                for result in image_results[:num_results]:
                    results["results"].append({
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "thumbnail": result.get("thumbnail", ""),
                        "source": result.get("source", ""),
                        "original": result.get("original", "")
                    })
            
            return results
        except Exception as e:
            print(f"Error in SerpAPI search: {str(e)}")
            # Fallback to direct search
            return self._search_direct(query, num_results, search_type)
    
    def _search_direct(self, query, num_results=5, search_type="web"):
        """
        Search using direct requests (fallback method)
        Note: This is a simple implementation and may not work reliably
        """
        try:
            # Format query for URL
            query_formatted = query.replace(" ", "+")
            
            # Set up the URL based on search type
            if search_type == "news":
                url = f"https://www.google.com/search?q={query_formatted}&tbm=nws"
            elif search_type == "images":
                url = f"https://www.google.com/search?q={query_formatted}&tbm=isch"
            else:
                url = f"https://www.google.com/search?q={query_formatted}"
            
            # Set headers to mimic a browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # Make the request
            response = requests.get(url, headers=headers)
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Format results
            results = {"query": query, "results": []}
            
            if search_type == "web" or search_type == "news":
                # Extract search results
                search_results = soup.select("div.g")
                
                for i, result in enumerate(search_results[:num_results]):
                    # Extract title
                    title_element = result.select_one("h3")
                    title = title_element.get_text() if title_element else ""
                    
                    # Extract link
                    link_element = result.select_one("a")
                    link = link_element.get("href") if link_element else ""
                    if link.startswith("/url?q="):
                        link = link.split("/url?q=")[1].split("&")[0]
                    
                    # Extract snippet
                    snippet_element = result.select_one("div.VwiC3b")
                    snippet = snippet_element.get_text() if snippet_element else ""
                    
                    # Extract source
                    source_element = result.select_one("div.UPmit")
                    source = source_element.get_text() if source_element else ""
                    
                    results["results"].append({
                        "title": title,
                        "link": link,
                        "snippet": snippet,
                        "source": source,
                        "position": i + 1
                    })
            elif search_type == "images":
                # Extract image results
                image_results = soup.select("div.isv-r")
                
                for i, result in enumerate(image_results[:num_results]):
                    # Extract image data
                    img_element = result.select_one("img.rg_i")
                    if img_element:
                        title = img_element.get("alt", "")
                        thumbnail = img_element.get("src", "")
                        
                        # Extract link
                        link_element = result.select_one("a")
                        link = link_element.get("href") if link_element else ""
                        if link.startswith("/url?q="):
                            link = link.split("/url?q=")[1].split("&")[0]
                        
                        results["results"].append({
                            "title": title,
                            "link": link,
                            "thumbnail": thumbnail,
                            "source": "",
                            "position": i + 1
                        })
            
            return results
        except Exception as e:
            print(f"Error in direct search: {str(e)}")
            return {"query": query, "results": [], "error": str(e)}
    
    def extract_article(self, url):
        """
        Extract article content from a URL
        
        Args:
            url (str): URL to extract content from
            
        Returns:
            dict: Article information
        """
        try:
            # Create an Article object
            article = Article(url)
            
            # Download and parse the article
            article.download()
            article.parse()
            
            # Extract the article's text
            article.nlp()
            
            # Format the result
            result = {
                "url": url,
                "title": article.title,
                "text": article.text,
                "summary": article.summary,
                "keywords": article.keywords,
                "authors": article.authors,
                "publish_date": article.publish_date.isoformat() if article.publish_date else None,
                "top_image": article.top_image,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        except Exception as e:
            print(f"Error extracting article: {str(e)}")
            
            # Fallback to simpler extraction
            try:
                # Make the request
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(url, headers=headers)
                
                # Parse the HTML
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract the title
                title = soup.title.string if soup.title else ""
                
                # Extract the main content
                # This is a simple approach and may not work for all websites
                content = ""
                
                # Try to find the main content
                main_elements = soup.select("article, main, #content, .content, .article, .post")
                
                if main_elements:
                    # Use the first main element
                    main_element = main_elements[0]
                    
                    # Extract paragraphs
                    paragraphs = main_element.select("p")
                    content = "\n".join([p.get_text() for p in paragraphs])
                else:
                    # Fallback to all paragraphs
                    paragraphs = soup.select("p")
                    content = "\n".join([p.get_text() for p in paragraphs])
                
                # Format the result
                result = {
                    "url": url,
                    "title": title,
                    "text": content,
                    "summary": "",
                    "keywords": [],
                    "authors": [],
                    "publish_date": None,
                    "top_image": "",
                    "timestamp": datetime.now().isoformat(),
                    "extraction_method": "fallback"
                }
                
                return result
            except Exception as e2:
                print(f"Error in fallback extraction: {str(e2)}")
                return {"url": url, "error": str(e), "timestamp": datetime.now().isoformat()}
    
    def summarize_search_results(self, query, num_results=3, extract_content=True):
        """
        Search and summarize results for a query
        
        Args:
            query (str): Search query
            num_results (int): Number of results to summarize
            extract_content (bool): Whether to extract full content from URLs
            
        Returns:
            dict: Summarized search results
        """
        # Search for the query
        search_results = self.search(query, num_results)
        
        if not search_results or not search_results.get("results"):
            return {"query": query, "summary": "No results found", "timestamp": datetime.now().isoformat()}
        
        # Extract content if requested
        if extract_content:
            for result in search_results["results"]:
                if "link" in result:
                    try:
                        article = self.extract_article(result["link"])
                        result["content"] = article
                    except Exception as e:
                        print(f"Error extracting content: {str(e)}")
                        result["content"] = {"error": str(e)}
        
        # Create a summary
        summary = f"Search results for '{query}':\n\n"
        
        for i, result in enumerate(search_results["results"]):
            summary += f"{i+1}. {result.get('title', 'No title')}\n"
            summary += f"   Source: {result.get('source', 'Unknown')}\n"
            summary += f"   Link: {result.get('link', 'No link')}\n"
            
            if "content" in result and "summary" in result["content"] and result["content"]["summary"]:
                summary += f"   Summary: {result['content']['summary']}\n"
            elif "snippet" in result:
                summary += f"   Snippet: {result.get('snippet', 'No snippet')}\n"
            
            summary += "\n"
        
        return {
            "query": query,
            "summary": summary,
            "results": search_results["results"],
            "timestamp": datetime.now().isoformat()
        }
    
    def fact_check(self, statement):
        """
        Perform a simple fact check on a statement
        
        Args:
            statement (str): Statement to fact check
            
        Returns:
            dict: Fact check results
        """
        # Search for the statement with fact check terms
        query = f"{statement} fact check"
        search_results = self.search(query, num_results=5)
        
        if not search_results or not search_results.get("results"):
            return {"statement": statement, "result": "No fact check information found", "confidence": 0}
        
        # Look for fact checking websites in the results
        fact_check_domains = [
            "factcheck.org", "politifact.com", "snopes.com", "fullfact.org", 
            "factchecker", "truthometer", "fact-check", "fact check"
        ]
        
        fact_check_results = []
        
        for result in search_results["results"]:
            # Check if the result is from a fact checking website
            is_fact_check = False
            
            if "link" in result:
                domain = urlparse(result["link"]).netloc
                is_fact_check = any(fc in domain.lower() for fc in fact_check_domains)
            
            if not is_fact_check and "title" in result:
                is_fact_check = any(fc in result["title"].lower() for fc in fact_check_domains)
            
            if not is_fact_check and "snippet" in result:
                is_fact_check = any(fc in result["snippet"].lower() for fc in fact_check_domains)
            
            if is_fact_check:
                fact_check_results.append(result)
        
        if not fact_check_results:
            return {"statement": statement, "result": "No specific fact check found", "confidence": 0.2}
        
        # Extract the fact check result
        # This is a simple approach and may not be accurate
        fact_check_result = fact_check_results[0]
        
        # Look for fact check ratings in the snippet
        rating_terms = {
            "true": ["true", "correct", "accurate", "confirmed"],
            "mostly_true": ["mostly true", "largely accurate", "generally correct"],
            "mixed": ["mixed", "partly true", "half true", "partially correct"],
            "mostly_false": ["mostly false", "largely inaccurate", "generally incorrect"],
            "false": ["false", "incorrect", "inaccurate", "untrue", "pants on fire"]
        }
        
        snippet = fact_check_result.get("snippet", "").lower()
        title = fact_check_result.get("title", "").lower()
        
        # Check for rating terms in the snippet and title
        found_ratings = []
        
        for rating, terms in rating_terms.items():
            for term in terms:
                if term in snippet or term in title:
                    found_ratings.append(rating)
        
        # Determine the overall rating
        if found_ratings:
            # Use the most common rating
            from collections import Counter
            rating_counter = Counter(found_ratings)
            overall_rating = rating_counter.most_common(1)[0][0]
            
            # Map to confidence score
            confidence_map = {
                "true": 0.9,
                "mostly_true": 0.7,
                "mixed": 0.5,
                "mostly_false": 0.3,
                "false": 0.1
            }
            
            confidence = confidence_map.get(overall_rating, 0.5)
        else:
            # If no specific rating is found, default to mixed
            overall_rating = "unknown"
            confidence = 0.5
        
        return {
            "statement": statement,
            "result": overall_rating,
            "confidence": confidence,
            "source": fact_check_result.get("link", ""),
            "source_name": fact_check_result.get("source", ""),
            "snippet": fact_check_result.get("snippet", "")
        }
    
    def get_search_history(self):
        """Get search history"""
        return self.search_history
    
    def clear_cache(self):
        """Clear the search cache"""
        self.cached_results = {}
        return True
