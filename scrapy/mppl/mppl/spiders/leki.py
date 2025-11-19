import scrapy
from urllib.parse import urljoin


class LekiSpider(scrapy.Spider):
    name = "leki"
    allowed_domains = ["mp.pl"]
    start_urls = ["https://www.mp.pl/pacjent/leki/"]

    custom_settings = {
        "DOWNLOAD_DELAY": 0.7,
        "FEEDS": {
            "leki.json": {"format": "json", "encoding": "utf8"},
        }
    }

    def parse(self, response):
        # linki do liter/cyfr
        for href in response.css(".alphabet-list a::attr(href)").getall():
            yield scrapy.Request(urljoin(response.url, href), callback=self.parse_letter)

    def parse_letter(self, response):
        # linki do leków w <ul class="drug-list">
        for href in response.css("ul.drug-list li a::attr(href)").getall():
            yield scrapy.Request(urljoin(response.url, href), callback=self.parse_lek)

        # paginacja
        next_page = response.css("ul.pagination li.next a::attr(href)").get()
        if next_page:
            yield scrapy.Request(urljoin(response.url, next_page), callback=self.parse_letter)

    def parse_lek(self, response):
        nazwa = response.css("h1::text").get(default="").strip()

        # sekcja "Co zawiera i jak działa"
        # 1. znajdź nagłówek poprzedzony kotwicą <a name="effect">
        h2 = response.xpath("//a[@name='effect']/following::h2[1]")

        # 2. pobierz cały tekst z <div class="item-content"> występującego po h2
        if h2:
            content_div = h2.xpath("following::div[contains(@class,'item-content')][1]")
            opis = " ".join(content_div.css("::text").getall()).strip()
        else:
            opis = ""

        yield {
            "nazwa": nazwa,
            "co_zawiera_i_jak_dziala": opis,
            "url": response.url
        }
