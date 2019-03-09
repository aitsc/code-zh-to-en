# -*- coding: utf-8 -*-
import re
import os
import shutil
import sys
import time
import datetime
from googletrans import Translator
from pygments.lexers import *
from pygments.lexers import LEXERS
from pygments.token import Token

__author__  = "Shicheng Tan <xxj.tan@gmail.com>"
__version__ = "1.0"
__date__    = "2018-10-22"

class 代码类:
    def __init__(self,地址或文本,解释器):
        if os.path.exists(地址或文本):
            with open(地址或文本,'r',encoding='utf-8') as r: self._代码文本=r.read()
        else:
            self._代码文本 = 地址或文本
        self._词法分析=lambda x: [(j,i) for i,j in 解释器().get_tokens(x)]
        self._词法分析结果l=self._词法分析(self._代码文本)
        self._代码名词_类型s=self._提取代码名词(self._词法分析结果l)

    def _提取代码名词(self,词法分析结果):
        代码名词s=set()
        for 词,类型 in 词法分析结果:
            if 代码类.判断是否为可替换类型(类型):
                代码名词s.add((词,类型))
        return 代码名词s

    def _词法分析结果复原(self,词法分析结果l):
        文本l=[i[0] for i in 词法分析结果l]
        return ''.join(文本l)

    def 名词替换(self,原词_替换词,替换词为关键字时的处理=lambda x:x+'_'):
        总替换次数=0
        原词_替换词_修改的={}
        for (原词,类型),替换词 in 原词_替换词.items():
            if not 代码类.判断是否为可替换类型(self._词法分析(替换词)[0][1]):
                替换词=替换词为关键字时的处理(替换词)
                原词_替换词_修改的[(原词,类型)]=替换词
            for i,(原词_,类型_) in enumerate(self._词法分析结果l):
                if (原词_,类型_)==(原词,类型):
                    self._词法分析结果l[i]=(替换词,类型)
                    总替换次数+=1
        return 总替换次数,原词_替换词_修改的

    def 代码写入文件(self,文件地址):
        if 文件地址==None or len(文件地址)==0:
            return 0
        目录=os.path.split(文件地址)[0]
        if not os.path.exists(目录) and 目录:
            os.makedirs(目录)
        with open(文件地址,'w',encoding='utf-8') as w:
            w.write(self.text)

    @staticmethod
    def 判断是否为可替换类型(类型):
        if 类型 in Token.Name.Class:
            return True
        if 类型 in Token.Name.Constant:
            return True
        if 类型 in Token.Name.Function:
            return True
        if 类型 in Token.Name.Other:
            return True
        if 类型 in Token.Name.Variable:
            return True
        if 类型 == Token.Name:
            return True
        return False

    @property
    def text(self):
        return self._词法分析结果复原(self._词法分析结果l).strip('\r\n')

    def get代码名词(self):
        return self._代码名词_类型s

class 多文件代码中英翻译:
    def __init__(self,代码源:str,类名翻译方法,变量翻译方法,文件类型_解释器d,默认解释器=eval('Python3Lexer')):
        self._主地址,self._次地址_代码类d,self._其他文件次地址s=self._读取代码(代码源,文件类型_解释器d,默认解释器)
        self._中文代码名词s=self._获得中文名词_类型([i for i in self._次地址_代码类d.values()])
        self._所有代码名词s=self._获得所有名词_类型([i for i in self._次地址_代码类d.values()])
        self._原词_替换词d=self._翻译代码名词(self._中文代码名词s,类名翻译方法,变量翻译方法,self._所有代码名词s) # {(词,类型):翻译词,..}
        self._进行替换([i for i in self._次地址_代码类d.values()],self._原词_替换词d)

    def _进行替换(self,代码类l,原词_替换词d):
        print('进行替换...')
        总替换次数=0
        修改翻译关键字数=0
        for i in 代码类l:
            替换次数,原词_替换词_修改的=i.名词替换(原词_替换词d)
            总替换次数+=替换次数
            原词_替换词d.update(原词_替换词_修改的)
            修改翻译关键字数+=len(原词_替换词_修改的)
        print('\t总替换次数: %d, 修正翻译词错成关键字: %d'%(总替换次数,修改翻译关键字数))

    def _获得中文名词_类型(self,代码类l):
        代码名词s = set()
        for i in 代码类l:
            for 词, 类型 in i.get代码名词():
                if re.search('[一-龥]',词):
                    代码名词s.add((词, 类型))
        return 代码名词s

    def _获得所有名词_类型(self,代码类l):
        代码名词s = set()
        for i in 代码类l:
            for 词, 类型 in i.get代码名词():
                代码名词s.add((词, 类型))
        return 代码名词s

    def _翻译代码名词(self,代码名词:set,类名翻译方法,变量翻译方法,所有代码名词s)->dict:
        print('翻译代码名词...')
        原词_替换词={}
        已翻译词_原词d={}
        修正翻译错成相同词=0
        类名词s=set(词 for 词,类型 in 代码名词 if 类型 in Token.Name.Class)
        for 词,类型 in 代码名词:
            if len(原词_替换词)%5==0:
                sys.stdout.write('\r')
                print('\t%d/%d'%(len(原词_替换词),len(代码名词)),end='')
                sys.stdout.flush()
            if 词 in 类名词s:
                翻译词 = 类名翻译方法(词)
            else:
                翻译词 = 变量翻译方法(词)
            # 如果翻译词重合, 则在后面加入_
            错=False
            while 翻译词 in 已翻译词_原词d and 已翻译词_原词d[翻译词]!=词:
                翻译词+='_'
                错=True
            if 错:
                修正翻译错成相同词+=1
            原词_替换词[(词, 类型)] = 翻译词
            已翻译词_原词d[翻译词]=词
        # 如果翻译后词是已有词, 那么在后面加入_
        修正翻译词错成已有词=0
        所有代码名词s=set(词 for 词,类型 in 所有代码名词s)
        for k in 原词_替换词.keys():
            错误=False
            while 原词_替换词[k] in 所有代码名词s:
                原词_替换词[k]+='_'
                错误=True
            if 错误:
                修正翻译词错成已有词+=1
        print('\r\t共翻译%d个词, 其中类词%d个, 修正翻译词错成已有词: %d, 修正翻译错成相同词: %d'%
              (len(原词_替换词),len(类名词s),修正翻译词错成已有词,修正翻译错成相同词))
        return 原词_替换词

    def _读取代码(self,代码源:str,文件类型_解释器d,默认解释器):
        print('读取代码...')
        次地址_代码类d={}
        其他文件次地址s=set()
        主地址=''
        # 如果是文件夹
        if os.path.isdir(代码源):
            主地址=代码源
            for 文件和文件夹地址 in os.walk(主地址):
                父文件夹=文件和文件夹地址[0]
                for 文件名 in 文件和文件夹地址[2]:
                    文件路径=os.path.join(父文件夹, 文件名)
                    次地址=('::'+文件路径).replace('::'+主地址,'')
                    后缀=os.path.splitext(文件路径)[1][1:].lower()
                    if 后缀 in 文件类型_解释器d:
                        次地址_代码类d[次地址] = 代码类(文件路径,文件类型_解释器d[后缀])
                    else:
                        其他文件次地址s.add(次地址)
        # 如果是一个文件
        elif os.path.isfile(代码源):
            主地址,文件名=os.path.split(代码源)
            后缀=os.path.splitext(代码源)[1][1:].lower()
            if 后缀 in 文件类型_解释器d:
                次地址_代码类d[文件名] = 代码类(代码源,文件类型_解释器d[后缀])
            else:
                次地址_代码类d[文件名] = 代码类(代码源, 默认解释器)
        # 如果是文本
        else:
            次地址_代码类d[''] = 代码类(代码源, 默认解释器)
        print('\t主地址: %s, 代码文件数: %d, 其他文件数: %d'%(主地址,len(次地址_代码类d),len(其他文件次地址s)))
        return 主地址,次地址_代码类d,其他文件次地址s

    def 输出所有代码(self,输出位置:str,输出其他文件=False,其他文件后缀白名单=None,其他文件后缀黑名单=None,名词翻译对照表输出文件名=''):
        if 输出位置==None:
            return 0
        # 如果是文件夹
        if len(输出位置)>0 and len(os.path.splitext(输出位置)[1])==0:
            for 次目录,代码_obj in self._次地址_代码类d.items():
                地址=输出位置+'/'+次目录
                代码_obj.代码写入文件(地址)
            self.输出名词翻译对照表(输出位置+'/'+名词翻译对照表输出文件名)
            if not 输出其他文件:
                return len(self._次地址_代码类d)
            else:
                输出数量=len(self._次地址_代码类d)
                for 其他文件次目录 in self._其他文件次地址s:
                    后缀=os.path.splitext(其他文件次目录)[1]
                    if 其他文件后缀白名单!=None and len(其他文件后缀白名单)>0 and 后缀 not in 其他文件后缀白名单:
                        continue
                    if 其他文件后缀黑名单!=None and 后缀 in 其他文件后缀黑名单:
                        continue
                    原目录=self._主地址+'/'+其他文件次目录
                    输出目录=输出位置+'/'+其他文件次目录
                    目录=os.path.split(输出目录)[0]
                    if not os.path.exists(目录):
                        os.makedirs(目录)
                    shutil.copyfile(原目录, 输出目录)
                    输出数量+=1
                return 输出数量
        # 如果是一个文件
        else:
            if not len(self._次地址_代码类d)==1:
                print('输出位置错误 - 不是一个代码文件!')
                return 0
            for 代码_obj in self._次地址_代码类d.values():
                代码_obj.代码写入文件(输出位置)
            if len(输出位置)>0:
                self.输出名词翻译对照表(os.path.split(输出位置)[0] + '/' + 名词翻译对照表输出文件名)
            else:
                self.输出名词翻译对照表(名词翻译对照表输出文件名)
            return 1

    def 查看第一个代码(self,输出=True):
        if len(self._次地址_代码类d) > 0:
            for 代码_obj in self._次地址_代码类d.values():
                print()
                if 输出:
                    print(代码_obj.text)
                return 代码_obj.text

    def 输出名词翻译对照表(self,输出地址):
        if 输出地址==None or len(输出地址)==0:
            return 0
        with open(输出地址,'w',encoding='utf-8') as w:
            w.write('词\t类型\t翻译词\n')
            for (词,类型),替换词 in self._原词_替换词d.items():
                w.write('%s\t%s\t%s\n'%(词,str(类型).replace('Token.',''),替换词))

class 中英翻译命名法:
    @staticmethod
    def 驼峰(文本,翻译器,小驼峰=True):
        # 头部保留符号
        头部保留符号=re.search('^[$@_]*',文本).group()
        文本 = re.sub('^[$@_]+', '', 文本)
        # 去除影响翻译的字符
        文本 = re.sub('[$@_]+', ':', 文本)
        # 翻译处理
        文本=翻译器(文本).lower()
        # 替换其他非法符号
        文本=文本.replace('-',' ')
        文本=re.sub('[^0-9a-zA-Z$@_\s]+','_',文本)
        # 分割
        文本 = re.findall('[a-zA-Z]+|[^\sa-zA-Z]+', 文本)
        # 合并
        文本=''.join([i.capitalize() for i in 文本])
        if 小驼峰:
            for i,字符 in enumerate(文本):
                if 字符.isalpha():
                    文本=文本[:i]+字符.lower()+文本[i+1:]
                    break
        return 头部保留符号+文本

def demo(代码源,输出位置='',默认解释器=eval('Python3Lexer'),输出翻译表='',同时拷贝其他文件=False):
    开始时间 = time.time();print(datetime.datetime.now())
    translator = Translator(service_urls=['translate.google.cn'])
    翻译器=lambda x: translator.translate(x,dest='en').text
    多文件代码中英翻译_obj=多文件代码中英翻译(
        代码源=代码源,
        类名翻译方法=lambda x:中英翻译命名法.驼峰(x,翻译器,小驼峰=False),
        变量翻译方法=lambda x:中英翻译命名法.驼峰(x,翻译器,小驼峰=True),
        文件类型_解释器d=默认_文件类型_解释器d,
        默认解释器=默认解释器,
    )
    多文件代码中英翻译_obj.输出所有代码(
        输出位置=输出位置,
        输出其他文件=同时拷贝其他文件,
        其他文件后缀白名单={},
        其他文件后缀黑名单={},
        名词翻译对照表输出文件名=输出翻译表,
    )
    print('共耗时:%.4f分钟' % ((time.time() - 开始时间) / 60))
    return 多文件代码中英翻译_obj


默认_文件类型_解释器d={
    ':解释器名称来源(点击进入查看)':LEXERS,
    'py':eval('Python3Lexer'),
    'java':eval('JavaLexer'),
    'c':eval('CLexer'),
    'cpp':eval('CppLexer'),
    'js':eval('JavascriptLexer'),
    'swift':eval('SwiftLexer'),
}

if __name__=='__main__':
    import pyperclip
    代码源 = pyperclip.paste();输出位置=''
    代码源 = '中英代码转化.py'
    输出位置 = 'code-zh-to-en.py'
    默认解释器 = 默认_文件类型_解释器d['py']
    输出翻译表 = '-名词翻译对照表.txt'
    同时拷贝其他文件 = False # 代码源为文件夹时可用

    obj=demo(代码源, 输出位置, 默认解释器, 输出翻译表, 同时拷贝其他文件)
    pyperclip.copy(obj.查看第一个代码(False))