# -*- coding: gbk -*-
import pymysql
from openai import OpenAI

# DeepSeek API Key
api_key = 'sk-cbaf83ca18874515961249c3cb6c4ef8'  # ���滻Ϊ���DeepSeek API��Կ
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# MySQL���ݿ���������
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'a257814256',  # ���滻Ϊ���MySQL����
    'database': 'web_scraping',
    'charset': 'utf8mb4'
}

# ���ӵ�MySQL���ݿⲢ��ȡ�ܽ�����
connection = pymysql.connect(**db_config)
summaries = []

try:
    with connection.cursor() as cursor:
        # ѡ�������ܽ�����
        cursor.execute("SELECT summary FROM articles WHERE summary IS NOT NULL")
        summaries = [summary[0] for summary in cursor.fetchall()]
finally:
    connection.close()

# �������ܽ����ݺϲ�Ϊһ���ַ���
all_summaries = "\n".join(summaries)

# ʹ��DeepSeek API����ͳ�Ʒ������ɱ���
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "����һ��ͳ�Ʒ������ɱ���ʦ�����������ʱ����ѭ���¹������ݸ��� - �������ݼ��Ļ�����Ϣ������������Դ��ʱ�䷶Χ��������ά�ȡ������������ - �������ݵ������ԡ�׼ȷ�Ժ�һ���Եļ������Ԥ������ - ��ϸ˵��������ϴ��ȱʧֵ�����쳣ֵ����Ȳ��衣������ͳ�� - �ṩ���ݵĻ���ͳ�����������ֵ����λ������׼���λ���ȡ����ݿ��ӻ� - ����ʹ�õ�ͼ�����ͣ�������ͼ������ͼ������ͼ�ȣ����Լ���Щͼ���ʾ�Ĺؼ����֡�������� - �г����е�ͳ�Ƽ�����飬�����������͡�ʹ�õ�������ˮƽ�ͽ��������Է��� - ��������֮�������ԣ�����ʹ�õ����ϵ������Ƥ��ѷ��˹Ƥ����������Ҫ���֡��ع���� - ��������˻ع����������ģ�͵����͡��ؼ�������ģ����϶Ⱥͽ��͡����ɷַ���/���ӷ��� - ���Ӧ���˽�ά������˵��ѡ��ķ���������ͽ��͡�������� - ����ʹ�õľ����㷨��ȷ���Ĵ������ص������ͷ������������ѧϰģ�� - ����漰����ѧϰ������ģ�����͡�ѵ�����̡�����ָ���ģ�ͱ��֡�������� - �ṩ�Է����������ϸ���ͣ��������ݷ�����ҵ����о�����ľ��庬�塣���ۺͽ��� - ���ڷ��������������ۺͿ��ܵ�ҵ����о����顣�������� - �������ݻ򷽷��ľ����ԣ��Լ���Щ���ƿ��ܶԷ������������Ӱ�졣δ���������� - ����δ������̽�������ݷ�������򷽷��Ľ���"},
        {"role": "user", "content": f"����������ݽ���ͳ�Ʒ��������ɱ��棺\n\n{all_summaries}\n"},
    ],
    stream=False
)
report = response.choices[0].message.content.strip()

# ������洢Ϊ�ı��ļ�
with open('�ۺϱ���.txt', 'w', encoding='utf-8') as file:
    file.write(report)

print("�ۺϱ����ѳɹ����ɲ��洢Ϊ�ı��ļ���")
