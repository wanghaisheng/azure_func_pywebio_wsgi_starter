#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @Author: https://github.com/Evil0ctal/
# @Time: 2021/11/06
# @Update: 2022/02/20
# @Function:
# 基于 PyWebIO、Requests、Flask，可实现在线批量解析抖音的无水印视频/图集。
# 可用于下载作者禁止下载的视频，同时可搭配iOS的快捷指令APP配合本项目API实现应用内下载。
# API请求参考
# 抖音/TikTok解析请求参数
# http://localhost(服务器IP):80/api?url="复制的(抖音/TikTok)的(分享文本/链接)" - 返回JSON数据
# 抖音/TikTok视频下载请求参数
# http://localhost(服务器IP):80/video?url="复制的抖音/TikTok链接" - 返回mp4文件下载请求
# 抖音视频/图集音频下载请求参数
# http://localhost(服务器IP):80/bgm?url="复制的抖音/TikTok链接" - 返回mp3文件下载请求

from pywebio import config, session
from pywebio.input import *
from pywebio.output import *
from pywebio.session import local
from pywebio.platform.flask import webio_view
from retrying import retry
from werkzeug.urls import url_quote
from flask import Flask, request, jsonify, make_response
import re
import json
import pyscreenshot

import time
import pandas as pd
import urllib
import os
import time
import requests
import unicodedata
import sys
from pywebio.session import defer_call, info as session_info, run_async,eval_js
from pywebio import start_server, output, config
from functools import partial
import pickle

import pandas as pd
app = Flask(__name__)
title = "TikToka™ tiktok/douyin videos Batch Download tookit"
description = "TikToka tiktok videos batch download for one user,for specific hashtags,challenges or keywords,no wartermark videos"
headers = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.66'
}
# driver =getwebdriver_ff(False)
def find_url(string):
    # Parse the link in the Douyin share password and return to the list
    url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)
    return url

def valid_check(kou_ling):
    # 校验输入的内容
    print('validate input start')
    # url_list = find_url(kou_ling)
    userinput_url_list = re.findall(
        'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', kou_ling)
    print('found url in user input',userinput_url_list)
    # 对每一个链接进行校验
    if userinput_url_list:
        for i in userinput_url_list:
            if 'douyin.com' in i[:31]:
                if i == userinput_url_list[-1]:
                    return None
                print('this is a douyin video task')
            elif 'tiktok.com' in i[:31]:
                if i == userinput_url_list[-1]:
                    return None
            else:

                return '请确保输入链接均为有效的抖音/TikTok链接!'
    elif 'user:' in kou_ling or 'user：' in kou_ling:
        print('this is a user task')
        return None
    else:
        return '抖音分享口令有误!'


def clean_filename(string, author_name):
    # 替换不能用于文件名的字符
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", string)  # 替换为下划线
    filename = 'douyin.wtf_' + new_title + '_' + author_name
    return filename


def error_do(e, func_name, input_value=''):
    # 输出一个毫无用处的信息
    put_html("<hr>")
    put_error("出现了意料之的错误，请检查输入值是否有效！")
    put_html('<h3>⚠详情</h3>')
    put_table([
        ['函数名', '原因'],
        [func_name, str(e)]])
    put_html("<hr>")
    put_markdown(
        '大量解析TikTok可能导致其防火墙限流!\n请稍等1-2分钟后再次尝试!\n如果多次尝试后仍失败,请点击[反馈](https://github.com/Evil0ctal/TikTokDownloader_PyWebIO/issues).\n你可以在右上角的关于菜单中查看本站错误日志:)')
    put_link('返回主页', '/')
    # 将错误记录在logs.txt中
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open('logs.txt', 'a') as f:
        f.write(date + ":\n" + func_name + ': ' + str(e) +
                '\n' + "Input value: " + input_value + '\n')


def loading():
    # 写一个进度条装装样子吧 :)
    set_scope('bar', position=3)
    with use_scope('bar'):
        put_processbar('bar')
        for i in range(1, 4):
            set_processbar('bar', i / 3)
            time.sleep(0.1)


def get_tiktok_url(tiktok_link):
    # 校验TikTok链接
    if tiktok_link[:12] == "https://www.":
        return tiktok_link
    else:
        try:
            # 从请求头中获取原始链接
            response = requests.get(
                url=tiktok_link, headers=headers, allow_redirects=False)
            true_link = response.headers['Location'].split("?")[0]
            # TikTok请求头返回的第二种链接类型
            if '.html' in true_link:
                response = requests.get(
                    url=true_link, headers=headers, allow_redirects=False)
                true_link = response.headers['Location'].split("?")[0]
            return true_link
        except Exception as e:
            error_do(e, get_tiktok_url, tiktok_link)


@retry(stop_max_attempt_number=3)
def get_video_info(original_url):
    # 利用官方接口解析链接信息
    try:
        # 原视频链接
        r = requests.get(url=original_url, allow_redirects=False)
        try:
            # 2021/12/11 发现抖音做了限制，会自动重定向网址，不能用以前的方法获取视频ID了，但是还是可以从请求头中获取。
            long_url = r.headers['Location']
        except:
            # 报错后判断为长链接，直接截取视频id
            long_url = original_url
        key = re.findall('video/(\d+)?', long_url)[0]
        api_url = f'https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={key}'
        print("Sending request to: " + '\n' + api_url)
        js = json.loads(requests.get(url=api_url, headers=headers).text)
        # 判断是否为图集
        if js['item_list'][0]['images'] is not None:
            print("Type = images")
            image_data = js['item_list'][0]['images']
            # 图集背景音频
            image_music = str(js['item_list'][0]['music']
                              ['play_url']['url_list'][0])
            # 图集标题
            image_title = str(js['item_list'][0]['desc'])
            # 图集作者昵称
            image_author = str(js['item_list'][0]['author']['nickname'])
            # 图集作者抖音号
            image_author_id = str(js['item_list'][0]['author']['unique_id'])
            if image_author_id == "":
                # 如果作者未修改过抖音号，应使用此值以避免无法获取其抖音ID
                image_author_id = str(js['item_list'][0]['author']['short_id'])
            # 去水印图集链接
            images_url = []
            for data in image_data:
                images_url.append(data['url_list'][0])
            image_info = [images_url, image_music, image_title,
                          image_author, image_author_id, original_url]
            return image_info, 'image', api_url
        else:
            print("Type = video")
            # 去水印后视频链接(2022年1月1日抖音APi获取到的URL会进行跳转，需要在Location中获取直链)
            video_url = str(js['item_list'][0]['video']['play_addr']
                            ['url_list'][0]).replace('playwm', 'play')
            r = requests.get(url=video_url, headers=headers,
                             allow_redirects=False)
            video_url = r.headers['Location']
            print(video_url)
            # 视频背景音频
            if js['item_list'][0]['music']['play_url']['url_list']:
                print("Getting music from playlist")
                video_music = str(js['item_list'][0]['music']
                                  ['play_url']['url_list'][0])
                print(video_music)
            else:
                video_music = "None"
            print(video_music)
            # 视频标题
            video_title = str(js['item_list'][0]['desc'])
            print(video_title)
            # 视频作者昵称
            video_author = str(js['item_list'][0]['author']['nickname'])
            print(video_author)
            # 视频作者抖音号
            video_author_id = str(js['item_list'][0]['author']['unique_id'])
            print(video_author_id)
            if video_author_id == "":
                # 如果作者未修改过抖音号，应使用此值以避免无法获取其抖音ID
                video_author_id = str(js['item_list'][0]['author']['short_id'])
            # 返回包含数据的列表
            video_info = [video_url, video_music, video_title,
                          video_author, video_author_id, original_url]
            return video_info, 'video', api_url
    except Exception as e:
        # 异常捕获
        error_do(e, 'get_video_info', original_url)


@retry(stop_max_attempt_number=3)
def get_video_info_tiktok(tiktok_url):
    # 对TikTok视频进行解析
    tiktok_url = get_tiktok_url(tiktok_url)
    print(tiktok_url)
    try:
        tiktok_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "authority": "www.tiktok.com",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Host": "www.tiktok.com",
            "User-Agent": "Mozilla/5.0  (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) coc_coc_browser/86.0.170 Chrome/80.0.3987.170 Safari/537.36",
        }
        html = requests.get(url=tiktok_url, headers=tiktok_headers)
        res = re.search(
            '<script id="sigi-persisted-data">(.*)</script><script', html.text).group(1)
        resp = re.findall(r'^window\[\'SIGI_STATE\']=(.*)?;window', res)[0]
        result = json.loads(resp)
        author_id = result["ItemList"]["video"]["list"][0]
        video_info = result["ItemModule"][author_id]
        # print("The author_id is: ", author_id)
        # print(video_info)
        # 从网页中获得的视频JSON 格式很乱 要忍一下
        return video_info
    except Exception as e:
        # 异常捕获
        error_do(e, 'get_video_info_tiktok', tiktok_url)


@retry(stop_max_attempt_number=3)
def tiktok_nwm(tiktok_url):
    # 使用第三方API获取无水印视频链接（不保证稳定）
    try:
        tiktok_url = get_tiktok_url(tiktok_url)
        s = requests.Session()
        api_url = "https://ttdownloader.com/req/"
        source = s.get("https://ttdownloader.com/")
        token = re.findall(r'value=\"([0-9a-z]+)\"', source.text)
        result = s.post(
            api_url,
            data={'url': tiktok_url, 'format': '', 'token': token[0]}
        )
        nwm, wm, audio = re.findall(
            r'(https?://.*?.php\?v\=.*?)\"', result.text
        )
        r = requests.get(nwm, allow_redirects=False)
        true_link = r.headers['Location']
        return true_link
    except Exception as e:
        error_do(e, "tiktok_nwm", tiktok_url)


@app.route("/api")
def webapi():
    # 创建一个Flask应用获取POST参数并返回结果
    try:
        content = request.args.get("url")
        if content:
            post_content = find_url(content)[0]
            # 将API记录在API_logs.txt中
            date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            with open('API_logs.txt', 'a') as f:
                f.write(date + " : " + post_content + '\n')
            # 校验是否为TikTok链接
            if 'tiktok.com' in post_content:
                try:
                    video_info = get_video_info_tiktok(post_content)
                    nwm_link = tiktok_nwm(post_content)
                    # 返回TikTok信息json
                    return jsonify(Status='Success', Type='Video', video_url=nwm_link,
                                   video_music=video_info['music']['playUrl'],
                                   video_title=video_info['desc'], video_author=video_info['author'],
                                   video_author_id=video_info['authorId'], original_url=post_content,
                                   music_title=video_info['music']['title'], music_author=video_info['music']['authorName'],
                                   followerCount=video_info['authorStats']['followingCount'],
                                   followingCount=video_info['authorStats']['followingCount'],
                                   likes_recived=video_info['authorStats']['heart'],
                                   video_count=video_info['authorStats']['videoCount'],
                                   water_mark_url=video_info['video']['playAddr'])
                except Exception:
                    return jsonify(Status='Failed!', Reason='Check the link!')
            # 如果关键字不存在则判断为抖音链接
            elif 'douyin.com' in post_content:
                try:
                    response_data, result_type, api_url = get_video_info(
                        post_content)
                    if result_type == 'image':
                        # 返回图集信息json
                        return jsonify(Status='Success', Type='Image', image_url=response_data[0],
                                       image_music=response_data[1],
                                       image_title=response_data[2], image_author=response_data[3],
                                       image_author_id=response_data[4], original_url=response_data[5])
                    else:
                        # 返回视频信息json
                        return jsonify(Status='Success', Type='Video', video_url=response_data[0],
                                       video_music=response_data[1],
                                       video_title=response_data[2], video_author=response_data[3],
                                       video_author_id=response_data[4], original_url=response_data[5])
                except:
                    return jsonify(Status='Failed!', Reason='Check the link!')
            else:
                return jsonify(Status='Failed!', Reason='Check the link!')

    except Exception as e:
        # 异常捕获
        error_do(e, 'webapi')
        return jsonify(Message="解析失败", Reason=str(e), Result=False)


@app.route("/video", methods=["POST", "GET"])
def download_video_url():
    # 返回视频下载请求
    content = request.args.get("url")
    input_url = find_url(content)[0]
    try:
        if 'douyin.com' in input_url:
            video_info, result_type, api_url = get_video_info(input_url)
            video_url = video_info[0]
            # 视频标题
            video_title = video_info[2]
            # 作者昵称
            author_name = video_info[3]
            # 清理文件名
            file_name = clean_filename(video_title, author_name)
        elif 'tiktok.com' in input_url:
            video_info = get_video_info_tiktok(input_url)
            nwm = tiktok_nwm(input_url)
            # 无水印地址
            video_url = nwm
            # 视频标题
            video_title = video_info['desc']
            # 作者昵称
            author_name = video_info['author']
            # 清理文件名
            file_name = clean_filename(video_title, author_name)
        else:
            return jsonify(Status='Failed!', Reason='Check the link!')
        # video_title = 'video_title'
        video_mp4 = requests.get(video_url, headers).content
        # 将video字节流封装成response对象
        response = make_response(video_mp4)
        # 添加响应头部信息
        response.headers['Content-Type'] = "video/mp4"
        # 他妈的,费了我老大劲才解决文件中文名的问题
        try:
            filename = file_name.encode('latin-1')
        except UnicodeEncodeError:
            filenames = {
                'filename': unicodedata.normalize('NFKD', file_name).encode('latin-1', 'ignore'),
                'filename*': "UTF-8''{}".format(url_quote(file_name) + '.mp4'),
            }
        else:
            filenames = {'filename': file_name + '.mp4'}
        # attachment表示以附件形式下载
        response.headers.set('Content-Disposition', 'attachment', **filenames)
        return response
    except Exception as e:
        error_do(e, 'download_video_url')
        return jsonify(Status='Failed!', Reason='Check the link!')


@app.route("/bgm", methods=["POST", "GET"])
def download_bgm_url():
    # 返回视频下载请求
    content = request.args.get("url")
    input_url = find_url(content)[0]
    try:
        if 'douyin.com' in input_url:
            video_info, result_type, api_url = get_video_info(input_url)
            if video_info[1] == "None":
                return jsonify(Status='Failed', Reason='This link has no music to get!')
            else:
                # 音频链接
                bgm_url = video_info[1]
                # 视频标题
                bgm_title = video_info[2]
                # 作者昵称
                author_name = video_info[3]
                # 清理文件名
                file_name = clean_filename(bgm_title, author_name)
        elif 'tiktok.com' in input_url:
            video_info = get_video_info_tiktok(input_url)
            bgm_url = video_info['music']['playUrl']
            # 视频标题
            bgm_title = video_info['music']['title']
            print('title: ', bgm_title)
            # 作者昵称
            author_name = video_info['music']['authorName']
            print('authorName: ', author_name)
            # 清理文件名
            file_name = clean_filename(bgm_title, author_name)
            print(file_name)
        else:
            return jsonify(Status='Failed', Reason='This link has no music to get!')
        video_bgm = requests.get(bgm_url, headers).content
        # 将bgm字节流封装成response对象
        response = make_response(video_bgm)
        # 添加响应头部信息
        response.headers['Content-Type'] = "video/mp3"
        # 他妈的,费了我老大劲才解决文件中文名的问题
        try:
            filename = file_name.encode('latin-1')
        except UnicodeEncodeError:
            filenames = {
                'filename': unicodedata.normalize('NFKD', file_name).encode('latin-1', 'ignore'),
                'filename*': "UTF-8''{}".format(url_quote(file_name) + '.mp3'),
            }
        else:
            filenames = {'filename': file_name + '.mp3'}
        # attachment表示以附件形式下载
        response.headers.set('Content-Disposition', 'attachment', **filenames)
        return response
    except Exception as e:
        error_do(e, 'download_bgm_url')
        return jsonify(Status='Failed!', Reason='Check the link!')


def put_result(item,label):
    # 根据解析格式向前端输出表格
    video_info, result_type, api_url = get_video_info(item)
    short_api_url = '/api?url=' + item
    if result_type == 'video':
        download_video = '/video?url=' + video_info[5]
        download_bgm = '/bgm?url=' + video_info[5]
        put_table([
            [label['douyin_type'], label['douyin_content']],
            [label['douyin_Format'], result_type],
            [label['douyin_Video_raw_link'], put_link(label['douyin_Video_raw_link_hint'], video_info[0], new_window=True)],
            [label['douyin_Video_download'], put_link(label['douyin_Video_download_hint'], download_video, new_window=True)],
            [label['douyin_Background_music_raw_link'], put_link(label['douyin_Background_music_raw_link_hint'], video_info[1], new_window=True)],
            [label['douyin_Background_music_download'], put_link(label['douyin_Background_music_download_hint'], download_bgm, new_window=True)],
            [label['douyin_Video_title'], video_info[2]],
            [label['douyin_Author_nickname'], video_info[3]],
            [label['douyin_Author_Douyin_ID'], video_info[4]],
            [label['douyin_Original_video_link'], put_link(label['douyin_Original_video_link_hint'], video_info[5], new_window=True)],
            [label['douyin_Current_video_API_link'], put_link(label['douyin_Current_video_API_link_hint'], api_url, new_window=True)],
            [label['douyin_Current_video_streamline_API_link'], put_link(label['douyin_Current_video_streamline_API_link_hint'], short_api_url, new_window=True)]
        ])
    else:
        download_bgm = '/bgm?url=' + video_info[5]
        put_table([
            [label['douyin_type'], label['douyin_content']],
            [label['douyin_Format'], result_type],
            [label['douyin_Background_music_raw_link'], put_link(label['douyin_Background_music_raw_link_hint'], video_info[1], new_window=True)],
            [label['douyin_Background_music_download'], put_link(label['douyin_Background_music_download_hint'], download_bgm, new_window=True)],
            [label['douyin_Video_title'], video_info[2]],
            [label['douyin_Author_nickname'], video_info[3]],
            [label['douyin_Author_Douyin_ID'], video_info[4]],
            [label['douyin_Original_video_link'], put_link(label['douyin_Original_video_link_hint'], video_info[5], new_window=True)],
            [label['douyin_Current_video_API_link'], put_link(label['douyin_Current_video_API_link_hint'], api_url, new_window=True)],
            [label['douyin_Current_video_streamline_API_link'], put_link(label['douyin_Current_video_streamline_API_link_hint'], short_api_url, new_window=True)]
        ])
        for i in video_info[0]:
            put_table([
            [label['douyin_Picture_straight_link'], put_link(
                label['douyin_Picture_straight_link_hint'], i, new_window=True), put_image(i)]
            ])


def put_tiktok_result(item,label):
    # 将TikTok结果显示在前端
    video_info = get_video_info_tiktok(item)
    nwm = tiktok_nwm(item)
    download_url = '/video?url=' + item
    api_url = '/api?url=' + item
    put_table([
        [label['tiktok_type'], label['tiktok_content']],
        [label['tiktok_Video_title'], video_info['desc']],
        [label['tiktok_Video_direct_link_with_watermark'], put_link(label['tiktok_Video_direct_link_with_watermark_hint'], video_info['video']
                                 ['playAddr'], new_window=True)],
        [label['tiktok_Video_direct_link_without_watermark'], put_link(label['tiktok_Video_direct_link_without_watermark_hint'], nwm, new_window=True)],
        [label['tiktok_Video_direct_link_without_watermark'], put_link(label['tiktok_Video_direct_link_without_watermark_hint'], download_url, new_window=True)],
        [label['tiktok_Background_music_raw_link'], video_info['music']['title'] +
         " - " + video_info['music']['authorName']],
        [label['tiktok_Background_music_raw_link'], put_link(label['tiktok_Background_music_raw_link_hint'], video_info['music']
                           ['playUrl'], new_window=True)],
        [label['tiktok_Author_nickname'], video_info['author']],
        [label['tiktok_Author_user_ID'], video_info['authorId']],
        [label['titkok_Follower_count'], video_info['authorStats']['followerCount']],
        [label['tiktok_Following_count'], video_info['authorStats']['followingCount']],
        [label['tiktok_Total_likes_get'], video_info['authorStats']['heart']],
        [label['tiktok_videos_count'], video_info['authorStats']['videoCount']],
        [label['tiktok_Original_video_link'], put_link(label['tiktok_Original_video_link_hint'], item, new_window=True)],
        [label['tiktok_Current_video_API_link'], put_link(label['tiktok_Current_video_API_link_hint'], api_url, new_window=True)]
    ])


def ios_pop_window():
    with popup("iOS快捷指令"):
        put_text('快捷指令需要在抖音或TikTok的APP内，浏览你想要无水印保存的视频或图集。')
        put_text('点击分享按钮，然后下拉找到 "抖音TikTok无水印下载" 这个选项。')
        put_text('如遇到通知询问是否允许快捷指令访问xxxx (域名或服务器)，需要点击允许才可以正常使用。')
        put_text('该快捷指令会在你相册创建一个新的相薄方便你浏览保存到内容。')
        put_html('<br>')
        put_link('[点击获取快捷指令]', 'https://www.icloud.com/shortcuts/e8243369340548efa0d4c1888dd3c170',
                 new_window=True)


def api_document_pop_window():
    with popup("API documentation"):
        put_markdown("💽API documentation")
        put_markdown("The API can convert the request parameters into the non-watermarked video/picture direct link that needs to be extracted, and it can be downloaded in-app with the IOS shortcut.")
        put_link('[Chinese document]', 'https://github.com/Evil0ctal/TikTokDownloader_PyWebIO#%EF%B8%8Fapi%E4%BD%BF%E7%94%A8',
                 new_window=True)
        put_html('<br>')
        put_link('[English document]',
                 'https://github.com/Evil0ctal/TikTokDownloader_PyWebIO/blob/main/README.en.md#%EF%B8%8Fapi-usage',
                 new_window=True)
        put_html('<hr>')
        put_markdown("🛰️API reference")
        put_markdown('Douyin/TikTok parsing request parameters')
        put_code('http://localhost(Server IP):80/api?url="Copied (TikTok/TikTok) (Share text/link)"\n#Return JSON')
        put_markdown('Douyin/TikTok video download request parameters')
        put_code('http://localhost(Server IP):80/download_video?url="Duplicated Douyin/TikTok link"\n#Return to mp4 file download request')
        put_markdown('TikTok video/atlas audio download request parameters')
        put_code('http://localhost(Server IP):80/download_bgm?url="Duplicated Douyin/TikTok link"\n#Return to mp3 file download request')


def error_log_popup_window():
    with popup('Error log'):
        content = open(r'./logs.txt', 'rb').read()
        put_file('logs.txt', content=content)
        with open('./logs.txt', 'r') as f:
            content = f.read()
            put_text(str(content))


def log_popup_window():
    with popup('错误日志'):
        put_html('<h3>⚠️关于解析失败</h3>')
        put_text('目前已知短时间大量访问抖音或Tiktok可能触发其验证码。')
        put_text('若多次解析失败后，请等待一段时间再尝试。')
        put_html('<hr>')
        put_text('请检查以下错误日志:')
        content = open(r'./logs.txt', 'rb').read()
        put_file('logs.txt', content=content)
        with open('./logs.txt', 'r') as f:
            content = f.read()
            put_text(str(content))

def doc_popup_window(display_label):
    with popup('%s'%display_label['doc']):
        put_html('<h3>%s</h3>'%display_label['uservideo'])
        put_image('https://views.whatilearened.today/views/github/evil0ctal/TikTokDownload_PyWebIO.svg',
                  title='访问记录')
        put_html('<hr>')
        put_html('<h3>⭐Github</h3>')
        put_markdown(
            '[TikTokDownloader_PyWebIO](https://github.com/Evil0ctal/TikTokDownloader_PyWebIO)')
        put_html('<hr>')
        put_html('<h3>🎯反馈</h3>')
        put_markdown(
            '提交：[issues](https://github.com/Evil0ctal/TikTokDownloader_PyWebIO/issues)')
        put_html('<hr>')
        put_html('<h3>🌐视频/图集批量下载</h3>')
        put_markdown(
            '可以使用[IDM](https://www.zhihu.com/topic/19746283/hot)之类的工具对结果页面的链接进行嗅探。')
        put_html('<hr>')
        put_html('<h3>💖WeChat</h3>')
        put_markdown('微信：[Evil0ctal](https://mycyberpunk.com/)')
        put_html('<hr>')        # "uid":"79298110705","short_id":"148174106","nickname":"苹果 姐姐"
        # sec_uid MS4wLjABAAAAnLgnj-bl5HuQ5l79HK5P9qyT0-SSdP112ZHy09OQS0s

def about_popup_window():
    with popup('更多信息'):
        put_html('<h3>👀访问记录</h3>')
        put_image('https://views.whatilearened.today/views/github/evil0ctal/TikTokDownload_PyWebIO.svg',
                  title='访问记录')
        put_html('<hr>')
        put_html('<h3>⭐Github</h3>')
        put_markdown(
            '[TikTokDownloader_PyWebIO](https://github.com/Evil0ctal/TikTokDownloader_PyWebIO)')
        put_html('<hr>')
        put_html('<h3>🎯反馈</h3>')
        put_markdown(
            '提交：[issues](https://github.com/Evil0ctal/TikTokDownloader_PyWebIO/issues)')
        put_html('<hr>')
        put_html('<h3>🌐视频/图集批量下载</h3>')
        put_markdown(
            '可以使用[IDM](https://www.zhihu.com/topic/19746283/hot)之类的工具对结果页面的链接进行嗅探。')
        put_html('<hr>')
        put_html('<h3>💖WeChat</h3>')
        put_markdown('微信：[Evil0ctal](https://mycyberpunk.com/)')
        put_html('<hr>')


def sponsor_popup_window():
    with popup('赏份盒饭'):
        put_html('<h3>👀微信</h3>')
        put_image('https://views.whatilearened.today/views/github/evil0ctal/TikTokDownload_PyWebIO.svg',
                  title='访问记录')
        put_html('<hr>')
        put_html('<h3>⭐支付宝</h3>')
        put_markdown(
            '[TikTokDownloader_PyWebIO](https://github.com/Evil0ctal/TikTokDownloader_PyWebIO)')
        put_html('<hr>')
        put_html('<h3>🎯反馈</h3>')
        put_markdown(
            '提交：[issues](https://github.com/Evil0ctal/TikTokDownloader_PyWebIO/issues)')
        put_html('<hr>')
        put_html('<h3>🌐buymeacoffee</h3>')
        put_markdown(
            'find me here[buymeacoffee](https://www.buymeacoffee.com/madegamedev)。')
        put_html('<hr>')
        put_html('<h3>Patreon</h3>')
        put_markdown('Patreon ：[Evil0ctal](https://mycyberpunk.com/)')
        put_html('<hr>')

def translations(lang):
    if os.path.exists('i18n/languages/'+lang+'.json'):
        path ='i18n/languages/'+lang+'.json'
    else:
        path ='i18n/languages/en.json'

    with open(path,encoding='utf-8') as fd:
        return json.load(fd)
en_labels=translations('en')
zh_labels=translations('zh')
es_labels=translations('es')
fr_labels=translations('fr')
ru_labels=translations('ru')


def language_pop_window():
    with popup('Select Site Language'):
        put_link('[Chinese Language]', 'https://douyin.wtf')
        put_html('<br>')
        put_link('[English Language]', 'https://en.douyin.wtf')



def locale(lang):
    # put_text("You click %s button" % lang_val)
    return translations(lang)
    # put_text("You title %s is" % local.title_label, type(local.title_label))






js_file = "https://www.googletagmanager.com/gtag/js?id=G-484Z1BXPFZ"
js_code = """
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());

gtag('config', 'G-484Z1BXPFZ');
"""

@config(title=title, description=description,js_file=js_file, js_code=js_code)
def tiktoka(lang='en'):
    # lang = eval_js("new URLSearchParams(window.location.search).get('lang')")   or 'en'
    # lang =put_buttons(['en', 'zh', 'fr', 'es', 'ru'], onclick=locale)    
    display_label=locale(lang)    
    session.set_env(title=display_label['head_title'])

    # session.set_env(description=display_label['head_description'])    
    # 设置favicon
    favicon_url = "https://raw.githubusercontent.com/Evil0ctal/TikTokDownloader_PyWebIO/main/favicon/android-chrome-512x512.png"
    session.run_js("""
    $('#favicon32,#favicon16').remove(); 
    $('head').append('<meta charset="utf-8">')
    $('head').append('<meta name="description" content=%s</>')
    $('head').append('<link rel="icon" type="image/png" href="%s">')
    $('head').append('<link rel="alternate" hreflang="en-gb" href="https://api.tiktokvideos.download/en" />')
    $('head').append('<link rel="alternate" hreflang="en-us" href="https://api.tiktokvideos.download/en" />')
    $('head').append('<link rel="alternate" hreflang="en" href="https://api.tiktokvideos.download" />')
    $('head').append('<link rel="alternate" hreflang="ru"  href="https://api.tiktokvideos.download/ru" />')
    $('head').append('<link rel="alternate" hreflang="fr" href="https://api.tiktokvideos.download/fr" />')
    $('head').append('<link rel="alternate" hreflang="vi" href="https://api.tiktokvideos.download/vi" />')
    $('head').append('<link rel="alternate" hreflang="fil" href="https://api.tiktokvideos.download/fil" />')
    $('head').append('<link rel="alternate" hreflang="x-default"  href="https://api.tiktokvideos.download" />')
    $('head').append('<meta name="viewport" content="width=device-width, initial-scale=1">
    $('head').append(' <script type="application/ld+json"/>')
    $('head').append('{')
    $('head').append('"@context": "http://schema.org",')
    $('head').append('"@type": "WebSite",')
    $('head').append('"name":%s,')
    $('head').append('"alternateName": %s,')
    $('head').append('"url": %s')
    $('head').append(' }')
    $('head').append('</script/>')
    """ %(display_label['head_description'],favicon_url,display_label['title'],display_label['head_description'],"https://api.tiktokvideos.download/"))
    # 修改footer
    # session.run_js("""$('footer').remove()""")

    session.run_js(
"""
$('footer').append('<a href="https://tiktokvideos.download/" }">  Tiktoka Mirror  </a>')
$('footer').append('<a href="https://trend.tiktokvideos.download/" }">  Tiktoka Trends  </a>')
$('footer').append('<a href="https://ninja.tiktokvideos.download/" }">  Tiktoka Ninja  </a>')

"""

    )
    # 访问记录
    view_amount = requests.get(
        "https://views.whatilearened.today/views/github/evil0ctal/TikTokDownload_PyWebIO.svg")

    put_markdown(
        """<div align='center' ><font size='14'>%s</font></div>""" % display_label['title'])
    put_markdown(
        """<div align='center' ><font size='14'>%s</font></div>"""%display_label['sub_title'])
    put_markdown(
        """<div align='center' ><font size='12'>%s</font></div>"""%display_label["third_title"])
    put_html('<hr>')
    put_row([
            # put_button("%s"%display_label['mobilepop'], onclick=lambda: ios_pop_window(), link_style=True, small=True),
            #  put_button("API", onclick=lambda: api_document_pop_window(),
            #             link_style=True, small=True),
            #  put_button("%s"%display_label['log'], onclick=lambda: log_popup_window(),
            #             link_style=True, small=True),
            # #  put_button("%s"%display_label['about'], onclick=lambda: about_popup_window(),
            # #             link_style=True, small=True),
            #  put_button("%s"%display_label['doc'], onclick=lambda: doc_popup_window(display_label),
            # #             link_style=True, small=True),                        
            #  put_button("%s"%display_label['support'], onclick=lambda: sponsor_popup_window(),
            #             link_style=True, small=True)
             ])
    kou_ling = textarea("%s"%display_label['kouling'], type=TEXT, validate=valid_check, required=True,
                        placeholder=display_label['placeholder'],
                        position=0)
    if kou_ling:
        print('kouling is not none',kou_ling)
        url_lists = find_url(kou_ling)
        print('parsing video url results',url_lists)
        # 解析开始时间
        start = time.time()
        try:
            loading()
            for url in url_lists:
                if 'douyin.com' in url:
                    put_result(url,display_label)
                else:
                    put_tiktok_result(url,display_label)
            clear('bar')
            # 解析结束时间
            end = time.time()
            put_html("<br><hr>")
            put_link('%s'%display_label['returnhome'], '/')
            put_text('%s'%display_label['timecost']+'%.4f秒' % (end - start))
        except Exception as e:
            # 异常捕获
            clear('bar')
            error_do(e, 'main')
            end = time.time()
            put_text('%s'%display_label['timecost']+'%.4f秒' % (end - start))
