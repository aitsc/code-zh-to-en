Chinese and English code translation: Lexical Analysis + Google Translate + Hump Naming

# Features
1. Support clipboard text direct conversion
2. Support single file conversion
3. support full folder batch conversion
4. Support hundreds of programming languages

# Tips
1. 中文包名有可能会翻译成英文包名
2. google翻译拒绝翻译问题(换ip)
3. 变量翻译成关键字会在后面加_
4. 输入的地址分隔符要与平台对应
5. c(++)不要 #define 中文
6. eval,exec,__all__等内部中文变量不能修改
7. 如果翻译后词是已有词, 那么在后面补_
8. 如果调用中文包, 会把中文变量翻译成英文
9. 如果翻译词重合, 则在后面加补_
10. 类名词和类名相同的变量标识符使用大驼峰

# Requirements
1. pip install googletrans==4.0.0-rc1
2. pip install Pygments
