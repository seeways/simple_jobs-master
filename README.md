# python_spider_jobs
基于python3

技术栈：urllib+BeautifulSoup4+SQLite，用到的py库：beautifulsoup4、configparser，以后增加图表显示的功能   

python写的爬虫，爬取51job、智联招聘的分城市的各种编程语言职位的总条数。    

爬取后分别保存到sqlite数据库与txt文本文件中。sqlite数据库一天只保存一次。

但jobs.txt一天可以写入多次爬取的记录，自动追加，需要新的，可以删掉再爬。

areaCode.md 是实测可用的城市编码信息    

