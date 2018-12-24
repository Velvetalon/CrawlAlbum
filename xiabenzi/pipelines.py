# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
import re,os
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
import logging
import time

class XiabenziPipeline(ImagesPipeline):
    #路径模板
    path_template = "{0}/{1}/{2}"

    def get_media_requests(self, item, info=None) :
        # with open("WFDAWFAWFA.txt","a+") as fp :
        #     fp.write(item['image_url']+"\n")
        for url in item["image_urls"] :
            yield scrapy.Request(url,meta={"item":item})

    def item_completed(self, results, item, info):
        if not results[0][0]:
            raise DropItem('下载失败')
        return item


    def file_path(self, request, response=None, info=None):
        item = request.meta["item"]
        album_name = item["album_name"]
        #清洗文件名。
        album_name = re.sub('[\\/:*?"<>|]'," ",album_name)
        album_keyword = item["key_word"].replace("%20"," ")

        index = os.path.split(request.url)[-1]
        return self.path_template.format(album_keyword,album_name,index)

class log_pipeline(object) :
    def __init__(self):
        #初始化日志模块。
        logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                            filename='./download_log_{0}.log'.format(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))),
                            filemode='w',
                            format=
                            '%(asctime)s : %(message)s')
    def process_item(self,item,spider):
        log_template = "画集名称：{0} - 已下载{1}页 - 来自关键字：<{2}>"
        logging.info(msg=log_template.format(item["album_name"],
                                         item["index"]-1,
                                         item["key_word"].replace("%20"," ")))
        return item