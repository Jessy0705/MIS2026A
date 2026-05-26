from google import genai

client = genai.Client(api_key='AIzaSyCxHmUCRxsIo_BumOf4-k6ZNExNeVZE7uM')

Question = input("請問你要問AI甚麼問題?")

# 直接體驗最新一代的 3.5 Flash 
response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents = Question,
)

print(response.text)