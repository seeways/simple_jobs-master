#!/usr/bin/env python
# encoding=utf-8
# python3.5
__author__ = 'Tim Liu'
__date__ = '2017/5/5 17:52'

import codecs
import configparser
import logging.config
import os
import re
import sqlite3
import time
import urllib
from datetime import datetime, timezone, timedelta
# import  urllib.request
from urllib.error import URLError, HTTPError, ContentTooShortError
from urllib.request import Request, urlopen

import bs4
from bs4 import BeautifulSoup


def get_east8_date_str(format_long=True):
    """
    获取东八区的当前时间：上海时间
    :param format_long: 是否是长格式：默认是长格式 2017-05-08 03:32:49  ，短格式：2017-05-08
    :return: 字符串格式的日期时间
    """
    dt = datetime.utcnow()
    dt = dt.replace(tzinfo=timezone.utc)
    if format_long:
        return dt.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    else:
        return dt.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")


# 获取51job.com 的html页面
def get_51job_html(jobearea, keyword):
    url_temp = "http://search.51job.com/jobsearch/search_result.php?fromJs=1&jobarea={jobarea}&keyword={keyword}&keywordtype=2&lang=c&stype=2&postchannel=0000&fromType=1&confirmdate=9"
    url = url_temp.format(jobarea=jobearea, keyword=urllib.request.quote(keyword))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36'}

    time.sleep(2)

    req = urllib.request.Request(url, None, headers)
    urlopen_content = urlopen(req)
    # urlopen_content = urllib.request.urlopen(url)  # 打开网址
    html = urlopen_content.read()  # 读取源代码并转为gbk
    urlopen_content.close()
    if html:
        return html.decode('gbk')
    else:
        return ""


# 解析51job.com 页面的
def parse_51job_html_job_nums(html):
    if not html:
        return 0
    soup = BeautifulSoup(html, "html.parser")
    # <div class="dw_table" id="resultList">
    # //*[@id="resultList"]/div[1]/div[3]
    # div1 = soup.find_all(id='resultList')

    # class 是python的关键字，记得加下划线,
    # 第3个div： <div class="rt">共3818条职位</div>
    div_childrens = soup.find_all("div", class_="dw_tlc")[0].children

    # div_childrens 是list_iterator 迭代器 类型
    job_nums = 0
    # 取出：<div class="rt">共7618条职位</div> 里面的数字：7618
    for child in div_childrens:
        # child有两种类型：<class 'bs4.element.Tag'> 与 <class 'bs4.element.NavigableString'>
        if isinstance(child, bs4.element.Tag):
            # 还有：['rt', 'order_time'] 、 ['rt', 'order_auto', 'dw_c_orange']、['chall']
            if child['class'] == ['rt']:
                # ['rt']有2个有，一个child.string等于“共7618条职位”，一个child.string为None
                if child.string:
                    # 用正则先去掉空格这些字符
                    compile_re = re.compile('\s*')
                    str = compile_re.sub('', child.string)
                    # logger.info("======b===", str)
                    # 用正则取出数字
                    match_re = re.match(r".*?(\d+).*", str)
                    if match_re:
                        job_nums = int(match_re.group(1))
                    break

    # logger.info("51job_nums=", job_nums)
    return job_nums


# 获取 智联招聘：zhaopin.com 的html页面
def get_zhaopin_html(jobarea_name, job_type):
    url_temp = "http://sou.zhaopin.com/jobs/searchresult.ashx?jl={jobarea_name}&kw={job_type}&sm=0&p=1&source=1"
    url = url_temp.format(jobarea_name=urllib.request.quote(jobarea_name), job_type=urllib.request.quote(job_type))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36'}

    logger.warning("-------->15-->02")
    try:
        time.sleep(2)
        req = urllib.request.Request(url, None, headers)
        response = urlopen(req)
        # response = urllib.request.urlopen(url) # 打开网址

    except HTTPError as e1:
        print("The (www.python.org)server couldn't fulfill the request.")
        logger.error('-------->15-->02->HTTPError-> %s' % (e1.msg))
    except URLError as e2:
        print('We failed to reach a server.')
        logger.error('-------->15-->03->URLError->%s' % (e2.msg))
    except ContentTooShortError as e3:
        print('Reason: ', e3.reason)
        logger.error('-------->15-->04->ContentTooShortError-> %s' % (e3.msg))
    else:
        html = ""
        logger.warning("-------->15-->05")
        try:
            if response:
                logger.warning("-------->15-->05-->01a")
                html = response.read()  # 读取源代码并转为unicode
                logger.warning("-------->15-->05-->01b")
            else:
                logger.warning("-------->15-->05-->02")
        except Exception as e4:
            logger.error('-------->15-->06->URLError->%s' % (str(e4)))
        finally:
            logger.warning("-------->15-->07-->finally")
            response.close()

        logger.warning("-------->15-->08")

        if html:
            return html.decode('UTF-8')
        else:
            logger.error("-------->15-->09-> html is None")

    return ""


# 解析 智联招聘：zhaopin.com 页面的, css选择器
def parse_zhaopin_html_job_nums(html):
    if not html:
        return 0
    soup = BeautifulSoup(html, "html.parser")
    # <span class="search_yx_tj">共<em>5631</em>个职位满足条件</span>
    # 使用css解析器
    em = soup.select("span.search_yx_tj > em")
    # logger.info(u"zhipin_job_nums=", em[0].string)
    return int(em[0].string)


def save_sqlite(published_time, jobarea_name, job_nums, job_type, job_site):
    """
        把爬取的数据写入sqlite数据库
    :param published_time: 职位爬取的时间
    :param jobarea_name:  职位的城市名称
    :param job_nums:      职位的个数
    :param job_type:     职位的类型：大数据 、 java、php、python、 android、iOS
    :param job_site:      搜索到的网站：前程无忧： 51job.com  ， 智联招聘：zhaopin.com
    :return:
    """
    dbPath = '%s/jobs_analysis.db' % os.getcwd()
    # logger.info(dbPath)
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    # 如果表不存在就新建表
    cur.execute(
        'CREATE TABLE  IF NOT EXISTS  jobs_tb (id INTEGER  NOT NULL  PRIMARY KEY AUTOINCREMENT DEFAULT 0,published_time VARCHAR(20) DEFAULT "",jobarea_name VARCHAR(20) DEFAULT "",job_nums INT DEFAULT 0, job_type VARCHAR(20) DEFAULT "", job_site VARCHAR(50) DEFAULT "", job_mark VARCHAR(255) DEFAULT "" )')
    con.commit()

    # r 表示不转义，保留原始字符
    sqlStr = r'INSERT INTO jobs_tb (id,published_time, jobarea_name, job_nums, job_type, job_site) VALUES(NULL, "%s",  "%s", "%d", "%s", "%s")' % (
        published_time, jobarea_name, job_nums, job_type, job_site)
    # logger.info(sqlStr)
    cur.execute(sqlStr)
    con.commit()

    # 关闭数据库
    con.close()


def is_need_save_db(current_date, job_site):
    """
    是否需要保存到数据库，保证数据一天最多只保存一次
    :param current_date: 当前日期："2017-05-06"
    :param job_site: 那个站点：前程无忧： 51job.com  ， 智联招聘：zhaopin.com
    :return: 是否已经保存过
    """
    cp = configparser.ConfigParser()
    appconf_path = '%s/conf/app.conf' % os.getcwd()
    with codecs.open(appconf_path, 'rb', encoding='utf-8') as f:
        cp.read_file(f)
    saved_date = cp.get('ini', 'save_date_' + job_site)
    if current_date > saved_date:
        cp.set('ini', 'save_date_' + job_site, current_date)
        with codecs.open(appconf_path, 'w', encoding='utf-8') as f:
            cp.write(f)
        return True
    else:
        return False


def spider_jobs(is_need_save=False, job_site="51job.com", job_type='python', jobarea_names=[], jobarea_codes=[]):
    jobs_txt_path = '%s/jobs.txt' % os.getcwd()
    file = codecs.open(jobs_txt_path, "a", "utf-8")
    file.write(u"----------------- " + job_type + " -----------------\n")

    for j in range(len(jobarea_names)):
        # 日期时间
        time_str = get_east8_date_str(True)
        # time_str = time.strftime('%Y-%m-%d  %H:%M:%S', time.localtime(time.time()))
        # 工作地名
        jobarea_name = jobarea_names[j]

        if job_site == "51job.com":
            html = get_51job_html(jobarea_codes[j], job_type)
            # 工作的职位数
            job_nums = parse_51job_html_job_nums(html)
            job_nums_str = u"共" + str(job_nums) + u"条职位"
        elif job_site == "zhaopin.com":
            logger.debug("-------->15")
            html = get_zhaopin_html(jobarea_name, job_type)
            logger.debug("-------->16")
            # 工作的职位数
            job_nums = parse_zhaopin_html_job_nums(html)
            # 说明报异常了，不用保存及显示
            if job_nums == 0:
                continue
            logger.debug("-------->17")
            job_nums_str = u"共" + str(job_nums) + u"条职位"

        if is_need_save:
            logger.info(u"--->Now is saving! job_nums=%d" % job_nums)
            # 数据保存到sqlite数据库
            save_sqlite(time_str, jobarea_name, job_nums, job_type, job_site)
        else:
            # 已经保存过sqlite数据库了，就不保存了
            logger.info(u"--->Today was saved! job_nums=%d" % job_nums)

        # 数据保存到txt文本文件中
        file.write(u"{0}\t{1}\t{2} \n".format(time_str, jobarea_name, job_nums_str))

    file.close()


def search_jobs(job_sites, keywords, jobarea_names, jobarea_codes):
    for job_site in job_sites:
        jobs_txt_path = '%s/jobs.txt' % os.getcwd()
        file = codecs.open(jobs_txt_path, "a", "utf-8")
        file.write(u"================= " + job_site + " =================\n")
        file.close()

        # 判断sqlite数据库是否要保存今天的记录
        current_date = get_east8_date_str(False)
        # current_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))

        is_need_save = is_need_save_db(current_date, job_site)

        for i in range(len(keywords)):
            spider_jobs(is_need_save, job_site, keywords[i], jobarea_names, jobarea_codes)


if __name__ == '__main__':
    # 日志文件：myapp.log,并且在屏幕上输出info级别的log
    logging.config.fileConfig("conf/logger.conf")
    logger = logging.getLogger("INFO")
    # 前程无忧： 51job.com
    job_sites = ["51job.com"]
    # job_sites = ["51job.com"]

    # 机器学习、数据挖掘 、深度学习、架构师
    keywords = ["java", "Android", "UI", u"ui设计师"]
    # 51job用：北京 ： jobarea=010000，
    # jobarea_names = [u"北京", u"上海", u"深圳", u"广州", u"西安", ]
    # jobarea_codes = ["010000", "020000", "040000", "030200", "200200"]

    jobarea_names = [u"深圳", u"西安", ]
    jobarea_codes = ["040000", "200200"]

    logger.info(u"============>bengin...")
    search_jobs(job_sites, keywords, jobarea_names, jobarea_codes)
    logger.info(u"============>end!")
