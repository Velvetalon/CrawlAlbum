import scrapy
import xiabenzi.items
import bs4
import urllib.parse
import os
import yaml

class getImage(scrapy.Spider):
    #用于区别Spider
    name = "getImage"
    #图片链接模板
    img_url_template = "https://comic.voicehentai.com/uploads/others/{0}/{1}/{2}.jpg"
    #关键字文件路径
    key_word_path = "KeyWord.txt"
    #搜索引擎模板
    search_engine_template = "https://www.voicehentai.com/search.php?{0}={1}"
    #网站本站。用于拼接相对路径。
    website_url = "https://www.voicehentai.com/"
    #搜索关键字。用于拼接搜索链接。
    search = "search.php"
    #默认关键字。
    default_key_word = {
        # 作品名称
        "parodies":
            ["Azur Lane", "Girls Frontline", "granblue fantasy", ],
        # 人物名称
        "characters":
            ["illustrious", "belfast", "prinz eugen", ],
        # 任意关键字
        "keyword":
            ["bondage", ],
    }

    #读取关键字配置。
    def read_keyword(self):
        self.urls = []

        #如果文件不存在或文件为空，则写入默认配置。
        if not os.path.exists(self.key_word_path) or not os.path.getsize(self.key_word_path):
            with open(self.key_word_path, "w+") as fp:
                yaml.dump(self.default_key_word,fp)

        with open(self.key_word_path, "r") as fp:
            conf = yaml.load(fp.read())
        #生成搜索链接。
        for key in conf.keys() :
            for keyword in conf[key] :
                self.urls.append(self.search_engine_template.format(key,keyword))

    #爬取方法
    def start_requests(self):  # 由此方法通过下面链接爬取页面
        self.read_keyword()
        #self.urls = ["https://www.voicehentai.com/page.php?id=4bf283e2-2d29-11e8-a98a-52540037eb09&part=6"]
        for url in self.urls:
            #初始化item
            item = getInitItem()
            yield scrapy.Request(url=url, callback=self.parse,meta={"item":item})  #提交给parse方法处理

    def parse(self, response):
        #如果爬取了所有图片，则结束爬取。
        if response.status == 404 :
            if response.url.find(".png") != -1 :
                yield response.meta["item"]
                return
            else :
                yield scrapy.Request(url=response.url.replace(".jpg", ".png"),
                                     callback=self.parse,
                                     meta={"item": response.meta["item"]})
                return
        #如果是一个搜索结果页，则解析其中的链接，并请求下一页。
        if response.url.find("search.php") != -1 :
            #提取其中所有画集主页链接，依次访问。
            soup = bs4.BeautifulSoup(response.body.decode("utf8"), "lxml")
            tag_list = soup.findAll(class_ = "col-sm-3 col-md-3 col-xs-6 product product_wd")
            #对于每一个画集都应该使用一个新的item。
            for tag in tag_list :
                new_item = getInitItem()
                # 保存关键字。
                new_item["key_word"] = response.url.split("=")[-1]
                yield scrapy.Request(url=self.website_url+tag.a.attrs["href"],
                               callback=self.parse, meta={"item":new_item})


            #判断是否是当前关键字的最后一页，如果不是最后一页则递归爬取下一页。
            div_tag = soup.find("div", attrs={"id": "page"})
            #如果未找到该div，表示只有一页。
            if not div_tag:
                return
            #如果没有下一页，则结束爬虫。
            next = div_tag.find("a", text=" > ")
            if not next:
                return
            else:
                next_item = getInitItem()
                next_url = self.website_url + self.search + next["href"]
                yield scrapy.Request(url=next_url,callback=self.parse,meta={"item":next_item})

        #如果是一个画集主页链接，则解析该链接并保存参数信息，然后开始重复获取图片链接。
        elif response.url.find("page.php") != -1 :
            url_args = urllib.parse.parse_qs(urllib.parse.urlparse(response.url).query)
            soup = bs4.BeautifulSoup(response.body.decode("utf8"), "lxml")
            title = soup.findAll("h1")[1].text
            item = response.meta["item"]
            item["album_name"] = title
            item["id"] = url_args["id"][0]
            item["part"] = url_args["part"][0]

            yield scrapy.Request(url=self.img_url_template.format(item["part"],item["id"],item["index"]),
                                    callback=self.parse,
                                    meta={"item":item})
        else :
            item = response.meta["item"]
            item["image_urls"].append(response.url)
            item["index"]+=1
            next = self.img_url_template.format(item["part"], item["id"], item["index"])
            yield scrapy.Request(url=next.replace(".png",".jpg"),
                                    callback=self.parse,
                                    meta={"item": item})

def getInitItem() :
    item = xiabenzi.items.FileDownload()
    item["image_urls"] = []
    item["index"] = 1
    item["key_word"] = "Single"
    return item





















