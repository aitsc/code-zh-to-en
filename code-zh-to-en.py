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

class CodeClass:
    def __init__(self,addressOrText,interpreter):
        if os.path.exists(addressOrText):
            with open(addressOrText,'r',encoding='utf-8') as r: self._codeText=r.read()
        else:
            self._codeText = addressOrText
        self._lexicalAnalysis=lambda x: [(j,i) for i,j in interpreter().get_tokens(x)]
        self._lexicalAnalysisResult=self._lexicalAnalysis(self._codeText)
        self._codeNoun_TypeS=self._extractCodeNoun(self._lexicalAnalysisResult)

    def _extractCodeNoun(self,lexicalAnalysisResult_):
        codeNounS=set()
        for word,typesOf in lexicalAnalysisResult_:
            if CodeClass.determineIfItIsAReplaceableType(typesOf):
                codeNounS.add((word,typesOf))
        return codeNounS

    def _lexicalAnalysisResultsRecovery(self,lexicalAnalysisResult):
        textL=[i[0] for i in lexicalAnalysisResult]
        return ''.join(textL)

    def nounReplacement(self,originalWord_ReplacementWord,processingWhenTheReplacementWordIsAKeyword=lambda x:x+'_'):
        totalNumberOfReplacements=0
        originalWord_ReplacementWord_Modified={}
        for (originalWord,typesOf),replacementWord in originalWord_ReplacementWord.items():
            if not CodeClass.determineIfItIsAReplaceableType(self._lexicalAnalysis(replacementWord)[0][1]):
                replacementWord=processingWhenTheReplacementWordIsAKeyword(replacementWord)
                originalWord_ReplacementWord_Modified[(originalWord,typesOf)]=replacementWord
            for i,(originalWord_,typesOf_) in enumerate(self._lexicalAnalysisResult):
                if (originalWord_,typesOf_)==(originalWord,typesOf):
                    self._lexicalAnalysisResult[i]=(replacementWord,typesOf)
                    totalNumberOfReplacements+=1
        return totalNumberOfReplacements,originalWord_ReplacementWord_Modified

    def codeWriteToFile(self,fileAddress):
        if fileAddress==None or len(fileAddress)==0:
            return 0
        tableOfContents=os.path.split(fileAddress)[0]
        if not os.path.exists(tableOfContents) and tableOfContents:
            os.makedirs(tableOfContents)
        with open(fileAddress,'w',encoding='utf-8') as w:
            w.write(self.text)

    @staticmethod
    def determineIfItIsAReplaceableType(typesOf):
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
        return self._lexicalAnalysisResultsRecovery(self._lexicalAnalysisResult).strip('\r\n')

    def getCodeNoun(self):
        return self._codeNoun_TypeS

class MultiFileCode:
    def __init__(self,codeSource:str,classNameTranslationMethod,variableTranslationMethod,fileType_InterpreterD,defaultInterpreter=eval('Python3Lexer')):
        self._primaryAddress,self._secondaryAddress_CodeClassD,self._otherFileSecondaryAddressS=self._readCode(codeSource,fileType_InterpreterD,defaultInterpreter)
        self._chineseCodeNounS=self._obtainChineseNoun_Type([i for i in self._secondaryAddress_CodeClassD.values()])
        self._allCodeNounsS=self._getAllNouns_Type([i for i in self._secondaryAddress_CodeClassD.values()])
        self._originalWord_ReplacementWordD=self._translationCodeNoun(self._chineseCodeNounS,classNameTranslationMethod,variableTranslationMethod,self._allCodeNounsS) # {(词,类型):翻译词,..}
        self._replace([i for i in self._secondaryAddress_CodeClassD.values()],self._originalWord_ReplacementWordD)

    def _replace(self,codeClassL,originalWord_ReplacementWordD):
        print('进行替换...')
        totalNumberOfReplacements=0
        editTranslationKeywords=0
        for i in codeClassL:
            numberOfReplacements,originalWord_ReplacementWord_Modified=i.nounReplacement(originalWord_ReplacementWordD)
            totalNumberOfReplacements+=numberOfReplacements
            originalWord_ReplacementWordD.update(originalWord_ReplacementWord_Modified)
            editTranslationKeywords+=len(originalWord_ReplacementWord_Modified)
        print('\t总替换次数: %d, 修正翻译词错成关键字: %d'%(totalNumberOfReplacements,editTranslationKeywords))

    def _obtainChineseNoun_Type(self,codeClassL):
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

    def _translationCodeNoun(self,codeNoun:set,classNameTranslationMethod,variableTranslationMethod,allCodeNounsS)->dict:
        print('翻译代码名词...')
        originalWord_ReplacementWord={}
        translatedWord_OriginalWordD={}
        correctTranslationIntoTheSameWord=0
        nounS=set(word for word,typesOf in codeNoun if typesOf in Token.Name.Class)
        for word,typesOf in codeNoun:
            if len(originalWord_ReplacementWord)%5==0:
                sys.stdout.write('\r')
                print('\t%d/%d'%(len(originalWord_ReplacementWord),len(codeNoun)),end='')
                sys.stdout.flush()
            if word in nounS:
                translationWord = classNameTranslationMethod(word)
            else:
                translationWord = variableTranslationMethod(word)
            # 如果翻译词重合, 则在后面加入_
            wrong=False
            while translationWord in translatedWord_OriginalWordD and translatedWord_OriginalWordD[translationWord]!=word:
                translationWord+='_'
                wrong=True
            if wrong:
                correctTranslationIntoTheSameWord+=1
            originalWord_ReplacementWord[(word, typesOf)] = translationWord
            translatedWord_OriginalWordD[translationWord]=word
        # 如果翻译后词是已有词, 那么在后面加入_
        correctTranslationWordsIntoExistingWords=0
        allCodeNounsS=set(word for word,typesOf in allCodeNounsS)
        for k in originalWord_ReplacementWord.keys():
            error=False
            while originalWord_ReplacementWord[k] in allCodeNounsS:
                originalWord_ReplacementWord[k]+='_'
                error=True
            if error:
                correctTranslationWordsIntoExistingWords+=1
        print('\r\t共翻译%d个词, 其中类词%d个, 修正翻译词错成已有词: %d, 修正翻译错成相同词: %d'%
              (len(originalWord_ReplacementWord),len(nounS),correctTranslationWordsIntoExistingWords,correctTranslationIntoTheSameWord))
        return originalWord_ReplacementWord

    def _readCode(self,codeSource:str,fileType_InterpreterD,defaultInterpreter):
        print('读取代码...')
        secondaryAddress_CodeClassD={}
        otherFileSecondaryAddressS=set()
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
                        secondaryAddress_CodeClassD[secondaryAddress] = CodeClass(filePath,fileType_InterpreterD[suffix])
                    else:
                        otherFileSecondaryAddressS.add(secondaryAddress)
        # 如果是一个文件
        elif os.path.isfile(codeSource):
            primaryAddress,fileName=os.path.split(codeSource)
            suffix=os.path.splitext(codeSource)[1][1:].lower()
            if suffix in fileType_InterpreterD:
                secondaryAddress_CodeClassD[fileName] = CodeClass(codeSource,fileType_InterpreterD[suffix])
            else:
                secondaryAddress_CodeClassD[fileName] = CodeClass(codeSource, defaultInterpreter)
        # 如果是文本
        else:
            secondaryAddress_CodeClassD[''] = CodeClass(codeSource, defaultInterpreter)
        print('\t主地址: %s, 代码文件数: %d, 其他文件数: %d'%(primaryAddress,len(secondaryAddress_CodeClassD),len(otherFileSecondaryAddressS)))
        return primaryAddress,secondaryAddress_CodeClassD,otherFileSecondaryAddressS

    def outputAllCode(self,outputPosition:str,outputOtherFiles=False,otherFileSuffixWhitelist=None,otherFileSuffixBlacklist=None,nounTranslationComparisonTableOutputFileName=''):
        if outputPosition==None:
            return 0
        # 如果是文件夹
        if len(outputPosition)>0 and len(os.path.splitext(outputPosition)[1])==0:
            for secondaryDirectory,code_Obj in self._secondaryAddress_CodeClassD.items():
                address=outputPosition+'/'+secondaryDirectory
                code_Obj.codeWriteToFile(address)
            self.outputNounTranslationComparisonTable(outputPosition+'/'+nounTranslationComparisonTableOutputFileName)
            if not outputOtherFiles:
                return len(self._secondaryAddress_CodeClassD)
            else:
                outputQuantity=len(self._secondaryAddress_CodeClassD)
                for otherFileSubdirectories in self._otherFileSecondaryAddressS:
                    suffix=os.path.splitext(otherFileSubdirectories)[1]
                    if otherFileSuffixWhitelist!=None and len(otherFileSuffixWhitelist)>0 and suffix not in otherFileSuffixWhitelist:
                        continue
                    if otherFileSuffixBlacklist!=None and suffix in otherFileSuffixBlacklist:
                        continue
                    originalDirectory=self._primaryAddress+'/'+otherFileSubdirectories
                    outputDirectory=outputPosition+'/'+otherFileSubdirectories
                    tableOfContents=os.path.split(outputDirectory)[0]
                    if not os.path.exists(tableOfContents):
                        os.makedirs(tableOfContents)
                    shutil.copyfile(originalDirectory, outputDirectory)
                    outputQuantity+=1
                return outputQuantity
        # 如果是一个文件
        else:
            if not len(self._secondaryAddress_CodeClassD)==1:
                print('输出位置错误 - 不是一个代码文件!')
                return 0
            for code_Obj in self._secondaryAddress_CodeClassD.values():
                code_Obj.codeWriteToFile(outputPosition)
            if len(outputPosition)>0:
                self.outputNounTranslationComparisonTable(os.path.split(outputPosition)[0] + '/' + nounTranslationComparisonTableOutputFileName)
            else:
                self.outputNounTranslationComparisonTable(nounTranslationComparisonTableOutputFileName)
            return 1

    def viewTheFirstCode(self,output=True):
        if len(self._secondaryAddress_CodeClassD) > 0:
            for code_Obj in self._secondaryAddress_CodeClassD.values():
                print()
                if output:
                    print(code_Obj.text)
                return code_Obj.text

    def outputNounTranslationComparisonTable(self,outputAddress):
        if outputAddress==None or len(outputAddress)==0:
            return 0
        with open(outputAddress,'w',encoding='utf-8') as w:
            w.write('词\t类型\t翻译词\n')
            for (word,typesOf),replacementWord in self._originalWord_ReplacementWordD.items():
                w.write('%s\t%s\t%s\n'%(word,str(typesOf).replace('Token.',''),replacementWord))

class ChineseEnglishTranslationNomenclature:
    @staticmethod
    def hump(text_,translator_,smallHump=True):
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
        if smallHump:
            for i,character in enumerate(text_):
                if character.isalpha():
                    text_=text_[:i]+character.lower()+text_[i+1:]
                    break
        return headReservedSymbol+text_

def demo(codeSource,outputPosition='',defaultInterpreter=eval('Python3Lexer'),outputTranslationTable='',copyOtherFilesAtTheSameTime=False):
    startingTime = time.time();print(datetime.datetime.now())
    translator = Translator(service_urls=['translate.google.cn'])
    translator_=lambda x: translator.translate(x,dest='en').text
    multiFileCodeChineseEnglishTranslation_Obj=MultiFileCode(
        codeSource=codeSource,
        classNameTranslationMethod=lambda x:ChineseEnglishTranslationNomenclature.hump(x,translator_,smallHump=False),
        variableTranslationMethod=lambda x:ChineseEnglishTranslationNomenclature.hump(x,translator_,smallHump=True),
        fileType_InterpreterD=default_FileType_InterpreterD,
        defaultInterpreter=defaultInterpreter,
    )
    multiFileCodeChineseEnglishTranslation_Obj.outputAllCode(
        outputPosition=outputPosition,
        outputOtherFiles=copyOtherFilesAtTheSameTime,
        otherFileSuffixWhitelist={},
        otherFileSuffixBlacklist={},
        nounTranslationComparisonTableOutputFileName=outputTranslationTable,
    )
    print('共耗时:%.4f分钟' % ((time.time() - startingTime) / 60))
    return multiFileCodeChineseEnglishTranslation_Obj


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
    import pyperclip
    codeSource = pyperclip.paste();outputPosition=''
    codeSource = '中英代码转化.py'
    outputPosition = 'code-zh-to-en.py'
    defaultInterpreter = default_FileType_InterpreterD['py']
    outputTranslationTable = '-名词翻译对照表.txt'
    copyOtherFilesAtTheSameTime = False # 代码源为文件夹时可用

    obj=demo(codeSource, outputPosition, defaultInterpreter, outputTranslationTable, copyOtherFilesAtTheSameTime)
    pyperclip.copy(obj.viewTheFirstCode(False))