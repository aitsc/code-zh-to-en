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

__author__  = "Shicheng Tan"
__version__ = "1.1"
__date__    = "2022-03-31"

class CodeClass:
    def __init__(self,addressOrText,interpreter):
        if os.path.exists(addressOrText):
            with open(addressOrText,'r',encoding='utf-8') as r: self._codeText=r.read()
        else:
            self._codeText = addressOrText
        self._lexicalAnalysis=lambda x: [(j,i) for i,j in interpreter().get_tokens(x)]
        self._lordAnalysisResults=self._lexicalAnalysis(self._codeText)
        self._codeNoun_TypeS=self._extractCodeNoun(self._lordAnalysisResults)

    def _extractCodeNoun(self,lateAnalysisResults):
        codeNounS=set()
        for word,typesOf in lateAnalysisResults:
            if CodeClass.determineIfItIsAnAlternativeType(typesOf):
                codeNounS.add((word,typesOf))
        return codeNounS

    def _lessMethodAnalysisResults(self,lordAnalysisResults):
        textL=[i[0] for i in lordAnalysisResults]
        return ''.join(textL)

    def nounReplacement(self,originalWords_ReplacementWords,processingForReplacingTheWordIsKeyword=lambda x:x+'_'):
        totalReplacement=0
        originalWords_ReplacementWords_Modified={}
        for (primitiveWord,typesOf),replacementWord in originalWords_ReplacementWords.items():
            if not CodeClass.determineIfItIsAnAlternativeType(self._lexicalAnalysis(replacementWord)[0][1]):
                replacementWord=processingForReplacingTheWordIsKeyword(replacementWord)
                originalWords_ReplacementWords_Modified[(primitiveWord,typesOf)]=replacementWord
            for i,(theOriginalWords_,typesOf_) in enumerate(self._lordAnalysisResults):
                if (theOriginalWords_,typesOf_)==(primitiveWord,typesOf):
                    self._lordAnalysisResults[i]=(replacementWord,typesOf)
                    totalReplacement+=1
        return totalReplacement,originalWords_ReplacementWords_Modified

    def codeWriteFile(self,fileAddress):
        if fileAddress==None or len(fileAddress)==0:
            return 0
        content=os.path.split(fileAddress)[0]
        if not os.path.exists(content) and content:
            os.makedirs(content)
        with open(fileAddress,'w',encoding='utf-8') as w:
            w.write(self.text)

    @staticmethod
    def determineIfItIsAnAlternativeType(typesOf):
        if typesOf in Token.Name.Class:
            return True
        if typesOf in Token.Name.Constant:
            return True
        if typesOf in Token.Name.Function:
            return True
        if typesOf in Token.Name.Other:
            return True
        if typesOf in Token.Name.Variable:
            return True
        if typesOf == Token.Name:
            return True
        return False

    @property
    def text(self):
        return self._lessMethodAnalysisResults(self._lordAnalysisResults).strip('\r\n')

    def getCodeNoun(self):
        return self._codeNoun_TypeS

class MultiFileCodeInEnglishTranslation:
    def __init__(self,codeSource:str,classNameTranslationMethod,variableTranslationMethod,fileType_InterpreterD,defaultInterpreter=eval('Python3Lexer')):
        self._primaryAddress,self._secondAddress_CodeClassD,self._otherFilesSAddressS=self._readCode(codeSource,fileType_InterpreterD,defaultInterpreter)
        self._chineseCodeNoun=self._getChineseNouns_Type([i for i in self._secondAddress_CodeClassD.values()])
        self._allCodeNounS=self._getAllNouns_Type([i for i in self._secondAddress_CodeClassD.values()])
        self._originalWords_ReplacementWordD=self._translationCodeNoun(self._chineseCodeNoun,classNameTranslationMethod,variableTranslationMethod,self._allCodeNounS) # {(词,类型):翻译词,..}
        self._replace([i for i in self._secondAddress_CodeClassD.values()],self._originalWords_ReplacementWordD)

    def _replace(self,codeClassL,originalWords_ReplacementWordD):
        print('进行替换...')
        totalReplacement=0
        modifyTranslationKeyword=0
        for i in codeClassL:
            replacement,originalWords_ReplacementWords_Modified=i.nounReplacement(originalWords_ReplacementWordD)
            totalReplacement+=replacement
            originalWords_ReplacementWordD.update(originalWords_ReplacementWords_Modified)
            modifyTranslationKeyword+=len(originalWords_ReplacementWords_Modified)
        print('\t总替换次数: %d, 修正翻译词错成关键字: %d'%(totalReplacement,modifyTranslationKeyword))

    def _getChineseNouns_Type(self,codeClassL):
        codeNounS = set()
        for i in codeClassL:
            for word, typesOf in i.getCodeNoun():
                if re.search('[一-龥]',word):
                    codeNounS.add((word, typesOf))
        return codeNounS

    def _getAllNouns_Type(self,codeClassL):
        codeNounS = set()
        for i in codeClassL:
            for word, typesOf in i.getCodeNoun():
                codeNounS.add((word, typesOf))
        return codeNounS

    def _translationCodeNoun(self,codeNoun:set,classNameTranslationMethod,variableTranslationMethod,allCodeNounS)->dict:
        print('翻译代码名词...')
        originalWords_ReplacementWords={}
        translatedWords_PrimaryWordD={}
        correctTranslationError=0
        classified=set(word for word,typesOf in codeNoun if typesOf in Token.Name.Class)
        for word,typesOf in codeNoun:
            if len(originalWords_ReplacementWords)%1==0:
                sys.stdout.write('\r')
                print('\t%d/%d'%(len(originalWords_ReplacementWords),len(codeNoun)),end='')
                sys.stdout.flush()
            if word in classified:
                translationWord = classNameTranslationMethod(word)
            else:
                translationWord = variableTranslationMethod(word)
            # 如果翻译词重合, 则在后面加入_
            wrong=False
            while translationWord in translatedWords_PrimaryWordD and translatedWords_PrimaryWordD[translationWord]!=word:
                translationWord+='_'
                wrong=True
            if wrong:
                correctTranslationError+=1
            originalWords_ReplacementWords[(word, typesOf)] = translationWord
            translatedWords_PrimaryWordD[translationWord]=word
        # 如果翻译后词是已有词, 那么在后面加入_
        correctTranslationWordMiscondu=0
        allCodeNounS=set(word for word,typesOf in allCodeNounS)
        for k in originalWords_ReplacementWords.keys():
            mistake=False
            while originalWords_ReplacementWords[k] in allCodeNounS:
                originalWords_ReplacementWords[k]+='_'
                mistake=True
            if mistake:
                correctTranslationWordMiscondu+=1
        print('\r\t共翻译%d个词, 其中类词%d个, 修正翻译词错成已有词: %d, 修正翻译错成相同词: %d'%
              (len(originalWords_ReplacementWords),len(classified),correctTranslationWordMiscondu,correctTranslationError))
        return originalWords_ReplacementWords

    def _readCode(self,codeSource:str,fileType_InterpreterD,defaultInterpreter):
        print('读取代码...')
        secondAddress_CodeClassD={}
        otherFilesSAddressS=set()
        primaryAddress=''
        # 如果是文件夹
        if os.path.isdir(codeSource):
            primaryAddress=codeSource
            for fileAndFolderAddress in os.walk(primaryAddress):
                parentFolder=fileAndFolderAddress[0]
                for fileName in fileAndFolderAddress[2]:
                    filePath=os.path.join(parentFolder, fileName)
                    secondaryAddress=('::'+filePath).replace('::'+primaryAddress,'')
                    suffix=os.path.splitext(filePath)[1][1:].lower()
                    if suffix in fileType_InterpreterD:
                        secondAddress_CodeClassD[secondaryAddress] = CodeClass(filePath,fileType_InterpreterD[suffix])
                    else:
                        otherFilesSAddressS.add(secondaryAddress)
        # 如果是一个文件
        elif os.path.isfile(codeSource):
            primaryAddress,fileName=os.path.split(codeSource)
            suffix=os.path.splitext(codeSource)[1][1:].lower()
            if suffix in fileType_InterpreterD:
                secondAddress_CodeClassD[fileName] = CodeClass(codeSource,fileType_InterpreterD[suffix])
            else:
                secondAddress_CodeClassD[fileName] = CodeClass(codeSource, defaultInterpreter)
        # 如果是文本
        else:
            secondAddress_CodeClassD[''] = CodeClass(codeSource, defaultInterpreter)
        print('\t主地址: %s, 代码文件数: %d, 其他文件数: %d'%(primaryAddress,len(secondAddress_CodeClassD),len(otherFilesSAddressS)))
        return primaryAddress,secondAddress_CodeClassD,otherFilesSAddressS

    def outputAllCode(self,outputLocation:str,outputOtherFiles=False,otherFilesAreEmbeddedInWhiteList=None,otherFileSuffixBlacklists=None,nameTranslationComparisonTableOutputFileName=''):
        if outputLocation==None:
            return 0
        # 如果是文件夹
        if len(outputLocation)>0 and len(os.path.splitext(outputLocation)[1])==0:
            for secondaryDirectory,code_Obj in self._secondAddress_CodeClassD.items():
                address=outputLocation+'/'+secondaryDirectory
                code_Obj.codeWriteFile(address)
            self.outputNounTranslationComparisonTable(outputLocation+'/'+nameTranslationComparisonTableOutputFileName)
            if not outputOtherFiles:
                return len(self._secondAddress_CodeClassD)
            else:
                outputQuantity=len(self._secondAddress_CodeClassD)
                for otherFiles in self._otherFilesSAddressS:
                    suffix=os.path.splitext(otherFiles)[1]
                    if otherFilesAreEmbeddedInWhiteList!=None and len(otherFilesAreEmbeddedInWhiteList)>0 and suffix not in otherFilesAreEmbeddedInWhiteList:
                        continue
                    if otherFileSuffixBlacklists!=None and suffix in otherFileSuffixBlacklists:
                        continue
                    origin=self._primaryAddress+'/'+otherFiles
                    outputCatalog=outputLocation+'/'+otherFiles
                    content=os.path.split(outputCatalog)[0]
                    if not os.path.exists(content):
                        os.makedirs(content)
                    shutil.copyfile(origin, outputCatalog)
                    outputQuantity+=1
                return outputQuantity
        # 如果是一个文件
        else:
            if not len(self._secondAddress_CodeClassD)==1:
                print('输出位置错误 - 不是一个代码文件!')
                return 0
            for code_Obj in self._secondAddress_CodeClassD.values():
                code_Obj.codeWriteFile(outputLocation)
            if len(outputLocation)>0:
                self.outputNounTranslationComparisonTable(os.path.split(outputLocation)[0] + '/' + nameTranslationComparisonTableOutputFileName)
            else:
                self.outputNounTranslationComparisonTable(nameTranslationComparisonTableOutputFileName)
            return 1

    def viewTheFirstCode(self,output=True):
        if len(self._secondAddress_CodeClassD) > 0:
            for code_Obj in self._secondAddress_CodeClassD.values():
                print()
                if output:
                    print(code_Obj.text)
                return code_Obj.text

    def outputNounTranslationComparisonTable(self,outputAddress):
        if outputAddress==None or len(outputAddress)==0:
            return 0
        with open(outputAddress,'w',encoding='utf-8') as w:
            w.write('词\t类型\t翻译词\n')
            for (word,typesOf),replacementWord in self._originalWords_ReplacementWordD.items():
                w.write('%s\t%s\t%s\n'%(word,str(typesOf).replace('Token.',''),replacementWord))

class ChineseAndEnglishTranslationNomenclature:
    @staticmethod
    def hump(text_,translator_,hump_=True):
        # 头部保留符号
        headReservedSymbol=re.search('^[$@_]*',text_).group()
        text_ = re.sub('^[$@_]+', '', text_)
        # 去除影响翻译的字符
        text_ = re.sub('[$@_]+', ':', text_)
        # 翻译处理
        text_=translator_(text_).lower()
        # 替换其他非法符号
        text_=text_.replace('-',' ')
        text_=re.sub('[^0-9a-zA-Z$@_\s]+','_',text_)
        # 分割
        text_ = re.findall('[a-zA-Z]+|[^\sa-zA-Z]+', text_)
        # 合并
        text_=''.join([i.capitalize() for i in text_])
        if hump_:
            for i,character in enumerate(text_):
                if character.isalpha():
                    text_=text_[:i]+character.lower()+text_[i+1:]
                    break
        time.sleep(5)
        return headReservedSymbol+text_

def demo(codeSource,outputLocation='',defaultInterpreter=eval('Python3Lexer'),outputTranslationTable='',copyOtherFilesAtTheSameTime=False):
    startingTime = time.time();print(datetime.datetime.now())
    translator = Translator(service_urls=['translate.google.com'])
    translator_=lambda x: translator.translate(x,dest='en').text
    multiFileCodeInEnglishTranslation_Obj=MultiFileCodeInEnglishTranslation(
        codeSource=codeSource,
        classNameTranslationMethod=lambda x:ChineseAndEnglishTranslationNomenclature.hump(x,translator_,hump_=False),
        variableTranslationMethod=lambda x:ChineseAndEnglishTranslationNomenclature.hump(x,translator_,hump_=True),
        fileType_InterpreterD=default_FileType_InterpreterD,
        defaultInterpreter=defaultInterpreter,
    )
    multiFileCodeInEnglishTranslation_Obj.outputAllCode(
        outputLocation=outputLocation,
        outputOtherFiles=copyOtherFilesAtTheSameTime,
        otherFilesAreEmbeddedInWhiteList={},
        otherFileSuffixBlacklists={},
        nameTranslationComparisonTableOutputFileName=outputTranslationTable,
    )
    print('共耗时:%.4f分钟' % ((time.time() - startingTime) / 60))
    return multiFileCodeInEnglishTranslation_Obj


default_FileType_InterpreterD={
    ':解释器名称来源(点击进入查看)':LEXERS,
    'py':eval('Python3Lexer'),
    'java':eval('JavaLexer'),
    'c':eval('CLexer'),
    'cpp':eval('CppLexer'),
    'js':eval('JavascriptLexer'),
    'swift':eval('SwiftLexer'),
}

if __name__=='__main__':
    codeSource = '中英代码转化.py'
    outputLocation = 'code-zh-to-en.py'
    defaultInterpreter = default_FileType_InterpreterD['py']
    outputTranslationTable = '-名词翻译对照表.txt'
    copyOtherFilesAtTheSameTime = False # 代码源为文件夹时可用
    obj=demo(codeSource, outputLocation, defaultInterpreter, outputTranslationTable, copyOtherFilesAtTheSameTime)
