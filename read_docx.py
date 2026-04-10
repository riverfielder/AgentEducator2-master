import sys, docx
path = r'C:\Users\ASUS\Downloads\“系统设计与实现类”毕业论文写作指南0128.docx'
doc = docx.Document(path)
for para in doc.paragraphs:
    print(para.text)
